import React from 'react';
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx';
import { LiquidCursor, LiquidDefs } from './components/liquid.jsx';
import AppLayout from './layouts/AppLayout.jsx';
import Login from './pages/Login.jsx';
import Overview from './pages/Overview.jsx';
import AskData from './pages/AskData.jsx';
import Live from './pages/Live.jsx';
import History from './pages/History.jsx';
import Sources from './pages/Sources.jsx';

function RequireAuth() {
  const { user } = useAuth(); const loc = useLocation();
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: loc.pathname }} />;
}

export default function App() {
  const { user } = useAuth();
  return <>
    <LiquidDefs /><LiquidCursor />
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<Overview />} />
          <Route path="ask" element={<AskData />} />
          <Route path="live" element={<Live />} />
          <Route path="history" element={<History />} />
          <Route path="sources" element={<Sources />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </>;
}
