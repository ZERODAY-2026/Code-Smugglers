import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, Database, LoaderCircle, MessageSquareText, RefreshCw, Sparkles, Table2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { LiquidCard } from '../components/liquid.jsx';
import QueryVisualization from '../components/QueryVisualization.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useData } from '../context/DataContext.jsx';

const examples = [
  { icon: Table2, text: 'How many customers subscribed to a term deposit?' },
  { icon: Database, text: 'Show the distribution of customers by job.' },
  { icon: MessageSquareText, text: 'What is the average balance by education?' },
];

function formatValue(value) {
  return value === null || value === undefined ? '—' : String(value);
}

export default function Overview() {
  const { user } = useAuth();
  const { schema, connected, schemaError, runQuery, refreshConnection } = useData();
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { if (!connected) refreshConnection().catch(() => {}); }, [connected, refreshConnection]);
  const submit = async (text) => {
    const value = text.trim();
    if (!value || loading) return;
    setQuestion(''); setLoading(true); setError('');
    try { setResult(await runQuery(value)); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); }
  };

  return <div className="page-content">
    <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> YOUR DATA, IN A NEW LIGHT</div><h1>Welcome back, {user?.name}<span className="heading-period">.</span></h1><p className="heading-subtitle">{schema?.dataset_description || 'Ask better questions. Find clearer answers.'}</p></div></div>
    <section className="query-hero"><div className="hero-orb orb-a" /><div className="hero-orb orb-b" /><div className="query-intro"><div className="ai-spark"><Sparkles size={19} /></div><div><div className="query-kicker">YOUR AI DATA ANALYST <span className={`live-chip ${connected ? '' : 'offline-chip'}`}><i /> {connected ? 'CONNECTED' : 'OFFLINE'}</span></div><h2>What would you like to know?</h2><p>Ask a question about your live {schema?.dataset || 'dataset'}.</p></div></div><form className="query-composer" onSubmit={(event) => { event.preventDefault(); submit(question); }}><input value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={2000} placeholder="e.g. How many customers subscribed to a term deposit?" aria-label="Ask a question about your data" /><button className="submit-query" disabled={!question.trim() || loading || !connected} aria-label="Run query">{loading ? <LoaderCircle className="spin" size={18} /> : <ArrowRight size={18} />}</button></form><div className="suggestion-row"><span className="suggestion-label">TRY ASKING</span>{examples.map(({ icon: Icon, text }) => <button key={text} className="suggestion-chip" onClick={() => submit(text)}><Icon size={14} />{text}</button>)}</div></section>
    {(schemaError || error) && <div className="inline-error"><AlertCircle size={15} />{error || schemaError}<button className="subtle-button" onClick={() => refreshConnection().catch(() => {})}><RefreshCw size={13} /> Retry</button></div>}
    <div className="section-title-row"><div><h3>Live workspace</h3><p>{schema ? `${schema.database}.${schema.schema} · ${schema.columns.length} columns available` : 'Waiting for the backend schema'}</p></div><button className="subtle-button" onClick={() => navigate('/ask')}>Open full analyst <ArrowRight size={14} /></button></div>
    {result && <LiquidCard animated={false} className="results-card overview-result"><div className="results-header"><div><div className="card-eyebrow">LATEST ANALYSIS · {result.status.toUpperCase()}</div><h3>{result.answer || result.question || result.explanation}</h3><p>{result.explanation}</p></div></div>{result.rows?.length ? <div className="table-scroll dynamic-result-table"><table><thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.map((row, rowIndex) => <tr key={rowIndex}>{result.columns.map((column, columnIndex) => <td key={`${column}-${rowIndex}`}>{formatValue(row[columnIndex])}</td>)}</tr>)}</tbody></table></div> : <div className="empty-result">No rows were returned for this question.</div>}<div className="result-meta">{result.query_id ? `Snowflake query ID: ${result.query_id}` : 'No Snowflake query was executed for this response.'}</div></LiquidCard>}
    {result && <QueryVisualization result={result} />}
    {!result && <div className="ask-empty compact"><Sparkles size={22} /><h3>Your live results will appear here</h3><p>Use one of the suggestions or ask your own question. Nothing on this dashboard is fabricated.</p></div>}
  </div>;
}
