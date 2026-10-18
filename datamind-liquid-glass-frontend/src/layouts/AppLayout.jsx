import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate, useOutlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useData } from '../context/DataContext.jsx';
import ThemeToggle from '../components/ThemeToggle.jsx';
import { LiquidCard } from '../components/liquid.jsx';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, Bell,
  Check, ChevronDown, CircleHelp, Clock3, Code2, Database, Download,
  Ellipsis, LogOut, FileCode2, Filter, Gauge, History, LayoutDashboard, LoaderCircle,
  Menu, MessageSquareText, Plus, Search, Send, Settings2, ShieldCheck,
  Sparkles, Table2, X, Zap
} from 'lucide-react';

const GlassCard = LiquidCard;

function Logo() {
  return <div className="brand-mark"><span className="brand-symbol"><Sparkles size={18} strokeWidth={1.8} /></span><span>data<span className="brand-light">mind</span><i>.</i></span></div>;
}

export default function AppLayout() {
  const location = useLocation(); const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showHistory, setShowHistory] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [notice, setNotice] = useState('');
  const { schema, connected, history } = useData();
  const outlet = useOutlet({ setNotice, setShowHistory });

  const navItems = [
    { label: 'Overview', icon: LayoutDashboard, path: '/' },
    { label: 'Ask Data', icon: MessageSquareText, path: '/ask' },
    { label: 'Live stream', icon: Activity, path: '/live' },
    { label: 'Query history', icon: History, path: '/history' },
    { label: 'Data sources', icon: Database, path: '/sources' }
  ];
  const activeNav = (navItems.find((n) => n.path === location.pathname) || navItems[0]).label;
  const staticPage = ['/', '/ask', '/live', '/history', '/sources'].includes(location.pathname);

  return (
    <div className={`app-shell ${location.pathname === '/' ? 'overview-static' : ''}`}>
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <motion.aside initial={{ x: -28, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ duration: .65, ease: [.2, .7, .2, 1] }} className={`sidebar ${mobileNav ? 'mobile-open' : ''}`}>
        <div className="sidebar-top"><Logo /><button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><X size={18} /></button></div>
        <button className="workspace-switch"><span className="workspace-avatar">D</span><span className="workspace-copy"><b>DataMind workspace</b><small>Personal workspace</small></span><ChevronDown size={15} /></button>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="side-nav">
          {navItems.map(({ label, icon: Icon, path }) => <button key={label} className={`nav-item ${activeNav === label ? 'active' : ''}`} onClick={() => { navigate(path); setMobileNav(false); }}>{activeNav === label && <motion.span layoutId="navpill" className="nav-pill" transition={{ type: 'spring', stiffness: 380, damping: 30 }} />}<Icon size={17} strokeWidth={1.8} /><span>{label}</span>{label === 'Query history' && <span className="nav-count">4</span>}</button>)}
        </nav>
        <div className="nav-caption source-caption">CONNECTED SOURCE</div>
        <div className="source-item"><span className="snowflake-mark">✳</span><span className="source-copy"><b>Snowflake</b><small>{schema ? `${schema.database}.${schema.schema}` : 'Connecting…'}</small></span><span className={`status-dot ${connected ? '' : 'offline-dot'}`} /></div>
        <div className="sidebar-bottom">
          <div className="usage-card"><div className="usage-heading"><span>Queries this browser</span><span>{history.length}</span></div><div className="usage-track"><span style={{ width: `${Math.min(history.length / 30 * 100, 100)}%` }} /></div><p>{history.length} saved live quer{history.length === 1 ? 'y' : 'ies'}</p></div>
          <button className="nav-item settings-item" onClick={() => setNotice('Settings are available when connected to your DataMind workspace.')}><Settings2 size={17} /><span>Settings</span></button>
          <div className="profile-row"><div className="profile-avatar">{user.name[0]}</div><div className="profile-copy"><b>{user.name}</b><small>{user.email}</small></div><button className="icon-button" onClick={logout} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button></div>
        </div>
      </motion.aside>

      <main className="main-content">
        <motion.header className="topbar" initial={{ y: -15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: .5 }}>
          <button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu size={19} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="crumb-slash">/</span><b>{activeNav}</b></div>
          <div className="topbar-actions"><div className="connection-pill"><span className={`status-dot ${connected ? '' : 'offline-dot'}`} /> {connected ? 'Backend connected' : 'Backend offline'}</div><ThemeToggle /><button className="icon-button notification-button" aria-label="Notifications" onClick={() => setNotice(connected ? 'DataMind is connected to live schema evidence.' : 'Start the backend to connect DataMind.')}><Bell size={17} /><i /></button><button className="help-button" onClick={() => setNotice('Ask DataMind questions in plain English. Every result is computed by Snowflake and shown with evidence.')}><CircleHelp size={16} /><span>Help</span></button></div>
        </motion.header>

        {staticPage ? <div className="route-wrap">{outlet}</div> : <AnimatePresence mode="wait"><motion.div key={location.pathname} className="route-wrap" initial={{ opacity: 0, filter: 'blur(14px)', y: 14 }} animate={{ opacity: 1, filter: 'blur(0px)', y: 0 }} exit={{ opacity: 0, filter: 'blur(14px)', y: -10 }} transition={{ duration: .35 }}>{outlet}</motion.div></AnimatePresence>}
      </main>

      <AnimatePresence>{notice && <motion.div className="toast" initial={{ opacity: 0, y: 15, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10 }}><span className="toast-icon"><Check size={15} /></span><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss"><X size={14} /></button></motion.div>}</AnimatePresence>
      <AnimatePresence>{showHistory && <><motion.div className="modal-scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowHistory(false)} /><motion.div className="history-modal glass-card" initial={{ opacity: 0, y: 18, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 12, scale: .98 }}><div className="modal-head"><div><div className="card-eyebrow">YOUR WORKSPACE</div><h3>Recent activity</h3></div><button className="icon-button" onClick={() => setShowHistory(false)} aria-label="Close activity"><X size={17} /></button></div>{history.slice(0, 5).map((entry) => <button className="history-item" key={entry.id} onClick={() => { navigate('/history'); setShowHistory(false); }}><span className="history-icon"><MessageSquareText size={15} /></span><span><b>{entry.question}</b><small>{new Date(entry.createdAt).toLocaleString()} · {entry.result.status}</small></span><ArrowUpRight size={15} /></button>)}{!history.length && <p className="modal-note">No live queries yet.</p>}</motion.div></>}</AnimatePresence>
    </div>
  );
}
