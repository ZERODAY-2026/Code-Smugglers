import React, { createContext, useCallback, useContext, useState } from 'react';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);
const KEY = 'dm-session';
const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || sessionStorage.getItem(KEY)); } catch { return null; } };

/* FRONTEND-ONLY DEMO AUTH.
   Replace `authenticate()` with a call to your backend (e.g. POST /api/auth/login) and
   store the returned session/token securely (httpOnly cookie recommended). Passwords are never stored here. */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(load);
  const authenticate = useCallback(async ({ email }) => {
    await new Promise((r) => setTimeout(r, 1100));
    const name = email.split('@')[0].replace(/[._-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    return { email, name };
  }, []);
  const signIn = useCallback((u, remember) => { try { (remember ? localStorage : sessionStorage).setItem(KEY, JSON.stringify(u)); } catch {} setUser(u); }, []);
  const logout = useCallback(() => { try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY); } catch {} setUser(null); }, []);
  return <Ctx.Provider value={{ user, authenticate, signIn, logout }}>{children}</Ctx.Provider>;
}
