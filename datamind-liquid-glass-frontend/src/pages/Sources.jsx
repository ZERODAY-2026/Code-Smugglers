import React from 'react';
import { AlertCircle, CheckCircle2, Database, RefreshCw, Table2 } from 'lucide-react';
import { LiquidCard } from '../components/liquid.jsx';
import { Head, Page } from '../components/PageKit.jsx';
import { useData } from '../context/DataContext.jsx';

export default function Sources() {
  const { schema, schemaError, connected, refreshConnection } = useData();
  const tables = [...new Set(schema?.columns?.map((column) => column.table) || [])];
  return <Page animated={false}><Head animated={false} eyebrow="DATA SOURCES" title="Your connected data" sub="This view is generated from the active backend schema." /><div className="source-live-status"><span className={`status-dot ${connected ? '' : 'offline-dot'}`} /><b>{connected ? 'Connected to Snowflake' : 'Backend unavailable'}</b><span>{schema ? `${schema.database}.${schema.schema}` : schemaError || 'No schema loaded'}</span>{!connected && <button className="subtle-button" onClick={() => refreshConnection().catch(() => {})}><RefreshCw size={13} /> Retry</button>}</div>{schema && <div className="src-grid">{tables.map((table) => <LiquidCard animated={false} className="src-card" key={table}><span className="src-icon on"><Database size={18} /></span><div><b>{table}</b><small>{schema.columns.filter((column) => column.table === table).length} columns · {schema.dataset_description}</small></div><CheckCircle2 className="source-check" size={17} /></LiquidCard>)}</div>}{schema && <LiquidCard animated={false} className="schema-card"><div className="card-eyebrow"><Table2 size={13} /> AVAILABLE COLUMNS</div><div className="schema-chips">{schema.columns.map((column) => <span key={`${column.table}.${column.column}`} title={column.qualified_table}>{column.column}<small>{column.data_type}</small></span>)}</div></LiquidCard>}{schemaError && !schema && <div className="inline-error"><AlertCircle size={15} />{schemaError}</div>}</Page>;
}
