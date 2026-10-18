import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { ThemeProvider } from './context/ThemeContext.jsx';
import { AuthProvider } from './context/AuthContext.jsx';
import { DataProvider } from './context/DataContext.jsx';
import './styles.css';
import './theme.css';
import './auth.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode><BrowserRouter><ThemeProvider><AuthProvider><DataProvider><App /></DataProvider></AuthProvider></ThemeProvider></BrowserRouter></React.StrictMode>
);
