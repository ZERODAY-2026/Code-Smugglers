import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Database, RefreshCw, Table2 } from 'lucide-react';
import { LiquidCard } from '../components/liquid.jsx';
import { Head, Page, item } from '../components/PageKit.jsx';
import { useData } from '../context/DataContext.jsx';

export default function Sources() {
  const { schema, schemaError, connected, refreshConnection } = useData();
  const tables = [...new Set(schema?.columns?.map((column) => column.table) || [])];
  return <Page><Head eyebrow="DATA SOURCES" title="Your connected data" sub="This view is generated from the active backend schema." /><div className="source-live-status"><span className={`status-dot ${connected ? '' : 'offline-dot'}`} /><b>{connected ? 'Connected to Snowflake' : 'Backend unavailable'}</b><span>{schema ? `${schema.database}.${schema.schema}` : schemaError || 'No schema loaded'}</span>{!connected && <button className="subtle-button" onClick={() => refreshConnection().catch(() => {})}><RefreshCw size={13} /> Retry</button>}</div>{schema && <motion.div className="src-grid" variants={item}>{tables.map((table) => <LiquidCard className="src-card" key={table}><span className="src-icon on"><Database size={18} /></span><div><b>{table}</b><small>{schema.columns.filter((column) => column.table === table).length} columns · {schema.dataset_description}</small></div><CheckCircle2 className="source-check" size={17} /></LiquidCard>)}</motion.div>}{schema && <LiquidCard className="schema-card"><div className="card-eyebrow"><Table2 size={13} /> AVAILABLE COLUMNS</div><div className="schema-chips">{schema.columns.map((column) => <span key={`${column.table}.${column.column}`} title={column.qualified_table}>{column.column}<small>{column.data_type}</small></span>)}</div></LiquidCard>}{schemaError && !schema && <div className="inline-error"><AlertCircle size={15} />{schemaError}</div>}</Page>;
}
