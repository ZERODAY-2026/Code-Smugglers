import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUpRight, Clock3, Database, MessageSquareText, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { LiquidCard } from '../components/liquid.jsx';
import { Head, Page, item } from '../components/PageKit.jsx';
import { useData } from '../context/DataContext.jsx';

export default function History() {
  const { history } = useData();
  const navigate = useNavigate();
  const [open, setOpen] = useState(null);
  return <Page><Head eyebrow="QUERY HISTORY" title="Everything you've asked" sub="Saved locally from real DataMind requests on this browser." /><motion.div variants={item}>{history.length ? <LiquidCard className="hist-card">{history.map((entry) => <div className="hist-row" key={entry.id}><button className="hist-btn" onClick={() => setOpen(open === entry.id ? null : entry.id)}><MessageSquareText size={15} /><b>{entry.question}</b><small><Clock3 size={11} /> {new Date(entry.createdAt).toLocaleString()}</small><motion.span animate={{ rotate: open === entry.id ? 45 : 0 }}><Plus size={15} /></motion.span></button><AnimatePresence>{open === entry.id && <motion.div className="history-detail" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}><span className={`history-status ${entry.result.status}`}>{entry.result.status}</span>{entry.result.query_id && <code>{entry.result.query_id}</code>}<button className="subtle-button" onClick={() => navigate('/ask')}><ArrowUpRight size={14} /> Ask another question</button></motion.div>}</AnimatePresence></div>)}</LiquidCard> : <div className="ask-empty"><Database size={22} /><h3>No queries yet</h3><p>Run a live question and it will appear here.</p></div>}</motion.div></Page>;
}
