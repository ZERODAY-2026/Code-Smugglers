import React, { useState } from 'react';
import { AnimatePresence, motion, useAnimation } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { ArrowRight, Check, Eye, EyeOff, LoaderCircle, Lock, Mail, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import ThemeToggle from '../components/ThemeToggle.jsx';
import { LiquidCard, Magnetic } from '../components/liquid.jsx';

const ease = [.2, .7, .2, 1];
const chips = [['Live data', 'Snowflake', '8%', '14%'], ['Planner', 'Gemma', '70%', '8%'], ['Evidence', 'Verified', '62%', '74%']];

export default function Login() {
  const { authenticate, signIn } = useAuth(); const loc = useLocation(); const shake = useAnimation();
  const [email, setEmail] = useState(''), [pw, setPw] = useState(''), [show, setShow] = useState(false);
  const [remember, setRemember] = useState(true), [state, setState] = useState('idle'), [err, setErr] = useState('');
  const fail = (m) => { setErr(m); shake.start({ x: [0, -10, 10, -6, 6, 0], transition: { duration: .4 } }); };
  const submit = async (e, demo) => {
    e?.preventDefault(); if (state !== 'idle') return;
    const em = demo ? 'demo@datamind.app' : email.trim();
    if (!/^\S+@\S+\.\S+$/.test(em)) return fail('Enter a valid email address.');
    if (!demo && pw.length < 6) return fail('Password must be at least 6 characters.');
    setErr(''); setState('loading');
    const u = await authenticate({ email: em }); setState('done');
    setTimeout(() => signIn(u, remember), 700);
  };
  return <div className="login-wrap">
    <div className="login-theme"><ThemeToggle /></div>
    <motion.div className="login-hero" initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .7, ease }}>
      <div className="brand-mark"><span className="brand-symbol"><Sparkles size={18} /></span><span>data<span className="brand-light">mind</span><i>.</i></span></div>
      <h1>Talk to your data<span className="heading-period">.</span></h1><p>Ask better questions. Find clearer answers.</p>
      <div className="chip-field">{chips.map(([a, b, l, t], i) => <motion.div key={a} className="float-chip" style={{ left: l, top: t }} animate={{ y: [0, -12, 0] }} transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut', delay: i * .6 }}><small>{a}</small><b>{b}</b></motion.div>)}<span className="lens" /></div>
    </motion.div>
    <motion.div className="login-panel" animate={shake}>
      <LiquidCard className="login-card">
        <motion.form onSubmit={submit} initial="h" animate="s" variants={{ s: { transition: { staggerChildren: .08, delayChildren: .2 } } }} noValidate>
          {[<div key="t"><div className="eyebrow"><span className="eyebrow-line" /> WELCOME BACK</div><h2>Sign in</h2></div>,
          <label key="e" className="field"><Mail size={16} /><input type="email" autoComplete="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label>,
          <label key="p" className="field"><Lock size={16} /><input type={show ? 'text' : 'password'} autoComplete="current-password" placeholder="Password" value={pw} onChange={(e) => setPw(e.target.value)} /><button type="button" className="eye" onClick={() => setShow(!show)} aria-label="Toggle password">{show ? <EyeOff size={16} /> : <Eye size={16} />}</button></label>,
          <div key="r" className="login-row"><button type="button" className={`liquid-switch ${remember ? 'on' : ''}`} onClick={() => setRemember(!remember)} aria-label="Remember me"><motion.span layout transition={{ type: 'spring', stiffness: 500, damping: 28 }} /></button><span>Keep me signed in</span></div>].map((n, i) => <motion.div key={i} variants={{ h: { opacity: 0, y: 14 }, s: { opacity: 1, y: 0, transition: { duration: .45, ease } } }}>{n}</motion.div>)}
          <AnimatePresence>{err && <motion.p className="form-error" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>{err}</motion.p>}</AnimatePresence>
          <Magnetic><motion.button layout className={`login-btn ${state}`} type="submit" whileTap={{ scale: .96 }}>
            <AnimatePresence mode="wait"><motion.span key={state} className="login-btn-in" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: .2 }}>
              {state === 'idle' && <>Sign in <ArrowRight size={16} /></>}{state === 'loading' && <><LoaderCircle className="spin" size={16} /> Signing in</>}{state === 'done' && <><Check size={16} /> Welcome</>}
            </motion.span></AnimatePresence></motion.button></Magnetic>
          <button type="button" className="demo-btn" onClick={() => submit(null, true)}>Continue with demo account</button>
              <p className="login-note">Local workspace sign-in · connect the backend to query live Snowflake data.</p>
        </motion.form>
      </LiquidCard>
    </motion.div>
  </div>;
}
