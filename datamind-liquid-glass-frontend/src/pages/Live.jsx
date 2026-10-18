import React from 'react';
import { CheckCircle2, Database, RefreshCw, WifiOff } from 'lucide-react';
import { LiquidCard } from '../components/liquid.jsx';
import { Head, Page, item } from '../components/PageKit.jsx';
import { useData } from '../context/DataContext.jsx';

export default function Live() {
  const { health, schema, connected, schemaError, refreshConnection } = useData();
  return <Page animated={false}><Head animated={false} eyebrow="LIVE CONNECTION" title="Everything, connected" sub="Live connection telemetry from the DataMind backend." /><div className="live-grid"><LiquidCard animated={false} className="live-tile"><div className="live-top"><span>Backend status</span>{connected ? <CheckCircle2 className="live-good" size={16} /> : <WifiOff size={16} />}</div><strong>{connected ? 'Online' : 'Offline'}</strong><p>{health?.service || 'DataMind Backend'}</p></LiquidCard><LiquidCard animated={false} className="live-tile"><div className="live-top"><span>Active dataset</span><Database size={16} /></div><strong>{schema?.dataset || '—'}</strong><p>{schema ? `${schema.columns.length} columns discovered` : 'Schema unavailable'}</p></LiquidCard><LiquidCard animated={false} className="live-tile"><div className="live-top"><span>Execution source</span><span className={`pulse-dot ${connected ? '' : 'offline-dot'}`} /></div><strong>Snowflake</strong><p>{schema ? `${schema.database}.${schema.schema}` : 'Not connected'}</p></LiquidCard></div><LiquidCard animated={false} className="live-big connection-detail"><div className="card-eyebrow">CONNECTION DETAILS</div><h3>No simulated metrics</h3><p>DataMind intentionally does not invent streaming values. This panel reflects only the current backend and schema connection.</p><button className="subtle-button" onClick={() => refreshConnection().catch(() => {})}><RefreshCw size={14} /> Refresh connection</button>{schemaError && <div className="inline-error"><WifiOff size={14} />{schemaError}</div>}</LiquidCard></Page>;
}
