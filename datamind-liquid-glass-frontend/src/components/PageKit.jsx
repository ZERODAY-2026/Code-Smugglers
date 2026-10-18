import React from 'react';
import { motion } from 'framer-motion';

export const ease = [.2, .7, .2, 1];
export const list = { hidden: {}, show: { transition: { staggerChildren: .08 } } };
export const item = { hidden: { opacity: 0, y: 18, filter: 'blur(8px)' }, show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: .55, ease } } };
export const Head = ({ eyebrow, title, sub, animated = true }) => {
  const content = <div><div className="eyebrow"><span className="eyebrow-line" /> {eyebrow}</div><h1>{title}<span className="heading-period">.</span></h1><p className="heading-subtitle">{sub}</p></div>;
  return animated ? <motion.div className="page-heading" variants={item}>{content}</motion.div> : <div className="page-heading">{content}</div>;
};
export const Page = ({ children, animated = true }) => animated
  ? <motion.div className="page-content pg" variants={list} initial="hidden" animate="show">{children}</motion.div>
  : <div className="page-content pg">{children}</div>;

export function curve(a, w, h) {
  const lo = Math.min(...a), hi = Math.max(...a), n = a.length;
  const P = a.map((v, i) => [i / (n - 1) * w, h - 4 - (v - lo) / (hi - lo || 1) * (h - 8)]);
  let d = `M${P[0][0]} ${P[0][1]}`;
  for (let i = 1; i < n; i++) { const m = [(P[i - 1][0] + P[i][0]) / 2, (P[i - 1][1] + P[i][1]) / 2]; d += ` Q${P[i - 1][0]} ${P[i - 1][1]} ${m[0]} ${m[1]}`; }
  return d + ` L${P[n - 1][0]} ${P[n - 1][1]}`;
}
