import React, { useEffect, useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, animate } from 'framer-motion';

export function LiquidDefs() {
  return (<>
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true"><defs>
      <filter id="liquid" x="-20%" y="-20%" width="140%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency=".012 .018" numOctaves="2" seed="3" result="n">
          <animate attributeName="baseFrequency" dur="14s" values=".012 .018;.022 .01;.012 .018" repeatCount="indefinite" />
        </feTurbulence>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="9" />
      </filter>
      <filter id="goo"><feGaussianBlur in="SourceGraphic" stdDeviation="12" />
        <feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" /></filter>
    </defs></svg>
    <div className="liquid-bg" aria-hidden="true"><i /><i /><i /></div>
  </>);
}

export function LiquidCursor() {
  const x = useMotionValue(-100), y = useMotionValue(-100);
  const sx = useSpring(x, { stiffness: 170, damping: 19, mass: .6 }), sy = useSpring(y, { stiffness: 170, damping: 19, mass: .6 });
  const [big, setBig] = useState(false);
  useEffect(() => {
    const m = (e) => { x.set(e.clientX - 23); y.set(e.clientY - 23); setBig(!!e.target.closest?.('button,a,input,.glass-card')); };
    window.addEventListener('pointermove', m);
    return () => window.removeEventListener('pointermove', m);
  }, []);
  return <motion.div className="liquid-cursor" style={{ x: sx, y: sy }} animate={{ scale: big ? 1.8 : 1 }} transition={{ type: 'spring', stiffness: 260, damping: 18 }} />;
}

export function LiquidCard({ children, className = '', ...p }) {
  const ref = useRef(null);
  const rx = useSpring(0, { stiffness: 200, damping: 18 }), ry = useSpring(0, { stiffness: 200, damping: 18 });
  const move = (e) => {
    const r = ref.current.getBoundingClientRect(), px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
    ry.set((px - .5) * 6); rx.set(-(py - .5) * 6);
    ref.current.style.setProperty('--mx', px * 100 + '%'); ref.current.style.setProperty('--my', py * 100 + '%');
  };
  return <motion.section ref={ref} onPointerMove={move} onPointerLeave={() => { rx.set(0); ry.set(0); }}
    style={{ rotateX: rx, rotateY: ry, transformPerspective: 900 }} whileHover={{ y: -3, scale: 1.006 }}
    transition={{ type: 'spring', stiffness: 300, damping: 22 }} className={`glass-card ${className}`} {...p}>{children}</motion.section>;
}

export function Magnetic({ children }) {
  const x = useSpring(0, { stiffness: 200, damping: 15 }), y = useSpring(0, { stiffness: 200, damping: 15 });
  return <motion.span style={{ x, y, display: 'inline-block' }}
    onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - r.left - r.width / 2) * .3); y.set((e.clientY - r.top - r.height / 2) * .3); }}
    onPointerLeave={() => { x.set(0); y.set(0); }}>{children}</motion.span>;
}

export function CountUp({ to, prefix = '', suffix = '', dec = 0 }) {
  const [v, setV] = useState(0);
  useEffect(() => { const c = animate(0, to, { duration: 1.6, ease: [.2, .7, .2, 1], onUpdate: setV }); return () => c.stop(); }, [to]);
  return <>{prefix}{v.toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec })}{suffix}</>;
}
