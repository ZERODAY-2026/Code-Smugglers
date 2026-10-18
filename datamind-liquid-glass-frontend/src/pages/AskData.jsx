import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, ArrowUp, CheckCircle2, Copy, Database, FileCode2, Info, RefreshCw, Sparkles } from 'lucide-react';
import { LiquidCard, Magnetic } from '../components/liquid.jsx';
import { Head, Page, item } from '../components/PageKit.jsx';
import { useData } from '../context/DataContext.jsx';

function formatValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function ResultDetails({ result }) {
  const [showSql, setShowSql] = useState(false);
  const copy = (value) => navigator.clipboard?.writeText(value);
  const tone = result.status === 'ok' ? 'success' : result.status === 'empty' ? 'empty' : 'notice';
  return <motion.div className="query-result-stack" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
    <div className={`query-status-card ${tone}`}><div className="result-status-icon">{result.status === 'ok' ? <CheckCircle2 size={19} /> : <Info size={19} />}</div><div><b>{result.status === 'ok' ? result.answer : result.status === 'empty' ? 'No matching rows' : result.question}</b><p>{result.explanation}</p></div></div>
    {result.rows?.length > 0 && <LiquidCard className="results-card"><div className="results-header"><div><div className="card-eyebrow">SNOWFLAKE RESULTS</div><h3>{result.rows.length} returned row{result.rows.length === 1 ? '' : 's'}</h3></div><button className="subtle-button" onClick={() => copy(JSON.stringify({ columns: result.columns, rows: result.rows }, null, 2))}><Copy size={14} /> Copy data</button></div><div className="table-scroll dynamic-result-table"><table><thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.map((row, rowIndex) => <tr key={rowIndex}>{result.columns.map((column, columnIndex) => <td key={`${column}-${rowIndex}`}>{formatValue(row[columnIndex])}</td>)}</tr>)}</tbody></table></div></LiquidCard>}
    {result.sql && <LiquidCard className="sql-panel dynamic-sql-panel"><button className="sql-toggle" onClick={() => setShowSql((value) => !value)}><span><FileCode2 size={14} /> Generated SQL</span><span>{showSql ? 'Hide' : 'Show'}</span></button><AnimatePresence>{showSql && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}><pre>{result.sql}</pre><button className="subtle-button" onClick={() => copy(result.sql)}><Copy size={13} /> Copy SQL</button></motion.div>}</AnimatePresence></LiquidCard>}
    {result.assumptions?.length > 0 && <div className="evidence-list"><b>Assumptions</b>{result.assumptions.map((text) => <p key={text}><Info size={13} />{text}</p>)}</div>}
    {result.warnings?.length > 0 && <div className="evidence-list warning-list"><b>Warnings</b>{result.warnings.map((text) => <p key={text}><AlertCircle size={13} />{text}</p>)}</div>}
    {result.query_id && <div className="query-id"><span>Snowflake query ID</span><code>{result.query_id}</code><button className="icon-button" onClick={() => copy(result.query_id)} aria-label="Copy query ID"><Copy size={14} /></button></div>}
  </motion.div>;
}

export default function AskData() {
  const { schema, schemaError, runQuery, refreshConnection } = useData();
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const end = useRef(null);

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, busy]);

  const send = async (value) => {
    const text = value.trim();
    if (!text || busy) return;
    setQuestion(''); setError(''); setBusy(true);
    setMessages((current) => [...current, { role: 'user', text }]);
    try {
      const result = await runQuery(text);
      setMessages((current) => [...current, { role: 'assistant', result }]);
    } catch (requestError) {
      setError(requestError.message);
      setMessages((current) => [...current, { role: 'assistant', result: { status: 'error', explanation: requestError.message, columns: [], rows: [], assumptions: [], warnings: [] } }]);
    } finally { setBusy(false); }
  };

  return <Page>
    <Head eyebrow="ASK DATA" title="Talk to your data" sub={schema ? `${schema.dataset_description} · live Snowflake evidence` : 'Connect to your live data in plain English.'} />
    <motion.div variants={item} className="data-context-strip"><Database size={15} /><span>{schema ? `${schema.database}.${schema.schema}` : 'Dataset unavailable'}</span><span className={`context-state ${schema && !schemaError ? 'online' : 'offline'}`} />{schemaError && <button className="subtle-button" onClick={() => refreshConnection().catch(() => {})}><RefreshCw size={13} /> Retry connection</button>}</motion.div>
    {messages.length === 0 && <motion.div variants={item} className="ask-empty"><Sparkles size={22} /><h3>Ask a question about your dataset</h3><p>Gemma plans the query, Snowflake computes it, and the evidence appears here.</p></motion.div>}
    <motion.div variants={item}><LiquidCard className="chat-card"><div className="chat-scroll"><AnimatePresence initial={false}>{messages.map((message, index) => <motion.div key={`${message.role}-${index}`} layout className={`conversation-message ${message.role}`}>{message.role === 'user' ? <div className="bubble me">{message.text}</div> : <div className="assistant-response"><div className="bubble ai"><Sparkles size={14} />{message.result.status === 'error' ? message.result.explanation : message.result.question || message.result.answer || message.result.explanation}</div>{message.result.status !== 'error' && <ResultDetails result={message.result} />}</div>}</motion.div>)}{busy && <motion.div className="bubble ai"><span className="goo-dots"><i /><i /><i /></span> Querying Gemma and Snowflake…</motion.div>}</AnimatePresence><div ref={end} /></div><form className="chat-input" onSubmit={(event) => { event.preventDefault(); send(question); }}><input value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={2000} placeholder="e.g. How many customers subscribed to a term deposit?" aria-label="Ask a question about your data" /><Magnetic><button className="submit-query" disabled={!question.trim() || busy || !schema} aria-label="Send question"><ArrowUp size={18} /></button></Magnetic></form></LiquidCard></motion.div>
    {error && <div className="inline-error"><AlertCircle size={15} />{error}</div>}
  </Page>;
}
