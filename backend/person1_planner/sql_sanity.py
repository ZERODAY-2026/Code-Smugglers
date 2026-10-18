"""Lightweight, token-based sanity checks for model-written candidate SQL.

This is NOT a SQL parser and NOT an authorization layer. It exists to (a) reject
obviously wrong output early so the planner can ask the model to repair it, and
(b) catch the cheap-to-detect tricks (writes hidden behind WITH, unlisted tables,
stage reads, dynamic identifiers). Person 2's AST gate stays the real authority.

Unlike the earlier substring/regex checks, everything here is computed on a token
stream where string literals, quoted identifiers and comments have already been
separated out, so ``'a;b'`` or ``-- note; ok`` no longer trigger false positives
and keywords hidden inside strings cannot trigger false negatives either.
"""
from __future__ import annotations

from dataclasses import dataclass


class SqlSanityError(ValueError):
    """Candidate SQL failed a sanity check. The message is safe to show/log."""


@dataclass(frozen=True, slots=True)
class Token:
    kind: str  # word | qid | str | num | punct
    text: str
    start: int
    end: int

    @property
    def upper(self) -> str:
        return self.text.upper()


FORBIDDEN_WORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "ALTER", "DROP", "TRUNCATE",
    "CALL", "COPY", "GRANT", "REVOKE", "EXECUTE", "UNDROP", "PUT", "REMOVE",
})
# Table functions that cannot reach data outside the supplied schema.
ALLOWED_TABLE_FUNCTIONS = frozenset({"FLATTEN", "GENERATOR", "VALUES", "SPLIT_TO_TABLE", "TABLE"})
_NOT_AN_ALIAS = frozenset({
    "WHERE", "GROUP", "ORDER", "HAVING", "QUALIFY", "LIMIT", "OFFSET", "FETCH", "UNION",
    "EXCEPT", "INTERSECT", "MINUS", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS",
    "NATURAL", "OUTER", "ON", "USING", "LATERAL", "WINDOW", "SAMPLE", "TABLESAMPLE",
    "PIVOT", "UNPIVOT", "MATCH_RECOGNIZE", "AT", "BEFORE", "CHANGES", "CONNECT", "START",
})
_FROM_CLAUSE_END = frozenset({
    "WHERE", "GROUP", "ORDER", "HAVING", "QUALIFY", "LIMIT", "OFFSET", "FETCH", "UNION",
    "EXCEPT", "INTERSECT", "MINUS", "WINDOW", "SELECT",
})
_FROM_IS_NOT_A_TABLE_IN =frozenset({"EXTRACT", "TRIM", "SUBSTRING", "SUBSTR", "OVERLAY", "POSITION"})
# Words that appear in expressions but are not column references.
_EXPR_WORDS = frozenset({
    "AS", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END", "AND", "OR", "NOT", "NULL",
    "TRUE", "FALSE", "IN", "IS", "LIKE", "ILIKE", "BETWEEN", "INTERVAL", "ALL", "ANY",
    "YEAR", "QUARTER", "MONTH", "WEEK", "DAY", "HOUR", "MINUTE", "SECOND", "DOW", "DOY",
    "EPOCH", "INT", "INTEGER", "BIGINT", "NUMBER", "NUMERIC", "DECIMAL", "FLOAT", "DOUBLE",
    "VARCHAR", "STRING", "TEXT", "CHAR", "BOOLEAN", "DATE", "TIME", "TIMESTAMP", "TIMESTAMP_NTZ",
    "TIMESTAMP_LTZ", "TIMESTAMP_TZ", "FROM", "OVER", "PARTITION", "BY", "ASC", "DESC",
    "CURRENT_DATE", "CURRENT_TIMESTAMP", "ROWS", "RANGE", "UNBOUNDED", "PRECEDING", "FOLLOWING",
    "CURRENT", "ROW",
})


def tokenize(sql: str) -> list[Token]:
    """Split SQL into tokens, dropping whitespace and comments.

    Raises SqlSanityError on unterminated strings/quotes/comments so that a
    truncated model response cannot slip through as "valid".
    """
    tokens: list[Token] = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c.isspace():
            i += 1
        elif c == "-" and sql.startswith("--", i) or c == "/" and sql.startswith("//", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j + 1
        elif c == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            if j < 0:
                raise SqlSanityError("unterminated block comment")
            i = j + 2
        elif c == "'":
            j = i + 1
            while True:
                if j >= n:
                    raise SqlSanityError("unterminated string literal")
                if sql[j] == "\\":  # Snowflake permits backslash escapes in '...'
                    j += 2
                    continue
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            tokens.append(Token("str", sql[i : j + 1], i, j + 1))
            i = j + 1
        elif sql.startswith("$$", i):
            j = sql.find("$$", i + 2)
            if j < 0:
                raise SqlSanityError("unterminated $$ string")
            tokens.append(Token("str", sql[i : j + 2], i, j + 2))
            i = j + 2
        elif c in '"`':
            j = i + 1
            while True:
                if j >= n:
                    raise SqlSanityError("unterminated quoted identifier")
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            tokens.append(Token("qid", sql[i + 1 : j].replace(c + c, c), i, j + 1))
            i = j + 1
        elif c.isalpha() or c == "_":
            j = i + 1
            while j < n and (sql[j].isalnum() or sql[j] in "_$"):
                j += 1
            tokens.append(Token("word", sql[i:j], i, j))
            i = j
        elif c.isdigit():
            j = i + 1
            while j < n and (sql[j].isalnum() or sql[j] in "._"):
                j += 1
            tokens.append(Token("num", sql[i:j], i, j))
            i = j
        else:
            tokens.append(Token("punct", c, i, i + 1))
            i += 1
    return tokens


def identifier_parts(name: str) -> tuple[str, ...]:
    """Return normalized parts without discarding database/schema qualifiers."""
    try:
        parts = tuple(t.text.casefold() for t in tokenize(name) if t.kind in {"word", "qid"})
    except SqlSanityError:
        parts = ()
    if parts:
        return parts
    return tuple(part.strip('"`').casefold() for part in name.strip().split(".") if part.strip())


def canonical(name: str) -> str:
    """Return the last identifier part: ``DB."S".Sales`` -> ``sales``."""
    parts = identifier_parts(name)
    return parts[-1] if parts else ""


def clean_candidate_sql(sql: str) -> str:
    """Return ``sql`` without trailing semicolons if it passes the sanity checks."""
    text = sql.strip()
    try:
        tokens = tokenize(text)
    except SqlSanityError as exc:
        raise SqlSanityError(f"Gemma candidate SQL is malformed ({exc}). No query was executed.") from exc

    # Drop trailing semicolons (a single terminating ';' is normal model output).
    while tokens and tokens[-1].kind == "punct" and tokens[-1].text == ";":
        text = text[: tokens[-1].start].rstrip()
        tokens.pop()

    if not tokens or tokens[0].kind != "word" or tokens[0].upper not in {"SELECT", "WITH"}:
        raise SqlSanityError("Gemma candidate SQL must begin with SELECT or WITH. No query was executed.")
    if any(t.kind == "punct" and t.text == ";" for t in tokens):
        raise SqlSanityError("Gemma candidate SQL appears to contain multiple statements. No query was executed.")

    for idx, tok in enumerate(tokens):
        if tok.kind == "word" and tok.upper in FORBIDDEN_WORDS:
            raise SqlSanityError(
                f"Gemma candidate SQL contains a disallowed keyword ({tok.upper}). No query was executed."
            )
        if tok.kind == "punct" and tok.text == "@":
            raise SqlSanityError("Gemma candidate SQL references a stage (@...). No query was executed.")
        if tok.kind == "word" and tok.upper == "IDENTIFIER" and idx + 1 < len(tokens) and tokens[idx + 1].text == "(":
            raise SqlSanityError("Gemma candidate SQL uses IDENTIFIER(), which bypasses table checks.")
    return text


def _dotted_name(tokens: list[Token], j: int) -> tuple[str, int]:
    """Read ``a.b.c`` starting at ``j``; return (name, index after it)."""
    name = tokens[j].text
    j += 1
    while j + 1 < len(tokens) and tokens[j].text == "." and tokens[j + 1].kind in {"word", "qid"}:
        name += "." + tokens[j + 1].text
        j += 2
    return name, j


def cte_names(tokens: list[Token]) -> set[str]:
    names: set[str] = set()
    for i in range(len(tokens) - 2):
        t = tokens[i]
        if t.kind in {"word", "qid"} and tokens[i + 1].upper == "AS" and tokens[i + 2].text == "(":
            names.add(t.text.casefold())
    return names


def referenced_tables(tokens: list[Token]) -> list[str]:
    """Names appearing in table position after FROM/JOIN (CTEs/subqueries excluded).

    Raises SqlSanityError for table functions outside ALLOWED_TABLE_FUNCTIONS
    (e.g. RESULT_SCAN, QUERY_HISTORY) since those read data outside the schema.
    """
    ctes = cte_names(tokens)
    found: list[str] = []
    paren_owner: list[str] = []
    active_from: set[int] = set()  # paren depths currently inside a FROM ... clause
    prev_word = ""
    for i, tok in enumerate(tokens):
        depth = len(paren_owner)
        if tok.text == "(" and tok.kind == "punct":
            paren_owner.append(prev_word)
        elif tok.text == ")" and tok.kind == "punct":
            active_from.discard(depth)
            if paren_owner:
                paren_owner.pop()
        elif tok.text == "," and tok.kind == "punct":
            # Comma join, even after a JOIN ... ON ... clause: `FROM a JOIN b ON x, c`.
            if depth in active_from:
                _collect_table(tokens, i + 1, ctes, found)
        elif tok.kind == "word" and tok.upper in _FROM_CLAUSE_END:
            active_from.discard(depth)
        elif tok.kind == "word" and tok.upper in {"FROM", "JOIN"}:
            in_fn_from = tok.upper == "FROM" and (
                (paren_owner and paren_owner[-1] in _FROM_IS_NOT_A_TABLE_IN) or prev_word == "DISTINCT"
            )
            if not in_fn_from:
                _collect_table(tokens, i + 1, ctes, found)
                active_from.add(depth)
        if tok.kind == "word":
            prev_word = tok.upper
        elif tok.kind != "punct" or tok.text not in {"(", ")"}:
            prev_word = ""
    return found


def _collect_table(tokens: list[Token], j: int, ctes: set[str], out: list[str]) -> None:
    """Record the table name starting at token ``j`` (if it is a plain table reference)."""
    n = len(tokens)
    if j < n and tokens[j].kind == "word" and tokens[j].upper in {"LATERAL", "ONLY"}:
        j += 1
    if j >= n or tokens[j].kind not in {"word", "qid"}:
        return  # '(' subquery / '@' stage (rejected elsewhere) / end
    name, k = _dotted_name(tokens, j)
    if k < n and tokens[k].text == "(":
        fn = canonical(name).upper()
        if fn not in ALLOWED_TABLE_FUNCTIONS:
            raise SqlSanityError(f"Gemma candidate SQL calls table function {fn}(), which is not permitted.")
        if fn == "TABLE":
            inner = tokens[k + 1] if k + 1 < n else None
            if inner is None or inner.kind != "word" or inner.upper not in ALLOWED_TABLE_FUNCTIONS:
                raise SqlSanityError("Gemma candidate SQL wraps a non-permitted table function in TABLE().")
        return  # inner tokens are scanned by the caller's main loop
    if name.casefold() not in ctes:
        out.append(name)


def output_aliases(tokens: list[Token]) -> set[str]:
    """Aliases defined with ``AS name`` (CAST(x AS type) excluded)."""
    aliases: set[str] = set()
    paren_owner: list[str] = []
    prev_word = ""
    for i, tok in enumerate(tokens):
        if tok.text == "(" and tok.kind == "punct":
            paren_owner.append(prev_word)
        elif tok.text == ")" and tok.kind == "punct":
            if paren_owner:
                paren_owner.pop()
        elif tok.kind == "word" and tok.upper == "AS" and i + 1 < len(tokens):
            nxt = tokens[i + 1]
            in_cast = bool(paren_owner) and paren_owner[-1] in {"CAST", "TRY_CAST"}
            if nxt.kind in {"word", "qid"} and not in_cast:
                aliases.add(nxt.text.casefold())
        if tok.kind == "word":
            prev_word = tok.upper
        elif tok.kind != "punct" or tok.text not in {"(", ")"}:
            prev_word = ""
    return aliases


def has_row_limit(tokens: list[Token]) -> bool:
    return any(t.kind == "word" and t.upper in {"LIMIT", "TOP", "FETCH"} for t in tokens)


def expression_identifiers(expr: str) -> list[str]:
    """Column-like identifiers inside a structured-plan field.

    ``"REVENUE"`` -> [revenue]; ``"SALES.REVENUE"`` -> [revenue];
    ``"*"`` -> []; ``"DATE_TRUNC('month', ORDER_DATE)"`` -> [order_date].
    """
    try:
        tokens = tokenize(expr)
    except SqlSanityError:
        return [canonical(expr)]
    names: list[str] = []
    for i, tok in enumerate(tokens):
        if tok.kind not in {"word", "qid"}:
            continue
        nxt = tokens[i + 1].text if i + 1 < len(tokens) else ""
        if nxt == "(" and tok.kind == "word":
            continue  # function name
        if nxt == "." :
            continue  # qualifier (table / alias), the column is the last segment
        if tok.kind == "word" and tok.upper in _EXPR_WORDS:
            continue
        names.append(tok.text.casefold())
    return names
