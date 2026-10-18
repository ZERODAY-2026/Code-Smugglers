import React, { createContext, useCallback, useContext, useLayoutEffect, useState } from 'react';
import { flushSync } from 'react-dom';

const Ctx = createContext(null);
export const useTheme = () => useContext(Ctx);
const initial = () => {
  try { const s = localStorage.getItem('dm-theme'); if (s) return s; } catch {}
  return matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(initial);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name=theme-color]')?.setAttribute('content', theme === 'dark' ? '#0b0b0b' : '#f1f0ea');
    try { localStorage.setItem('dm-theme', theme); } catch {}
  }, [theme]);
  // Circular "liquid" reveal from the clicked button (View Transitions API, graceful fallback)
  const toggle = useCallback((e) => {
    const next = theme === 'dark' ? 'light' : 'dark';
    if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) return setTheme(next);
    const x = e?.clientX ?? innerWidth / 2, y = e?.clientY ?? 0;
    const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    const t = document.startViewTransition(() => flushSync(() => setTheme(next)));
    t.ready.then(() => document.documentElement.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] },
      { duration: 750, easing: 'cubic-bezier(.2,.7,.2,1)', pseudoElement: '::view-transition-new(root)' }));
  }, [theme]);
  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
}
