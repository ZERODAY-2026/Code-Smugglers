import React from 'react';
import { motion } from 'framer-motion';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../context/ThemeContext.jsx';

export default function ThemeToggle() {
  const { theme, toggle } = useTheme(); const dark = theme === 'dark';
  return <button className="icon-button theme-toggle" onClick={toggle} aria-label={`Switch to ${dark ? 'light' : 'dark'} mode`} title="Toggle theme">
    <motion.span key={theme} style={{ display: 'grid' }} initial={{ rotate: -90, scale: .4, opacity: 0 }} animate={{ rotate: 0, scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 16 }}>{dark ? <Moon size={17} /> : <Sun size={17} />}</motion.span>
  </button>;
}
