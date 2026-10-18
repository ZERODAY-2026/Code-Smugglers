import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getHealth, getSchema, askQuestion as requestQuery } from '../api/client.js';

const HISTORY_KEY = 'datamind-query-history';
const Ctx = createContext(null);

function loadHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function DataProvider({ children }) {
  const [health, setHealth] = useState(null);
  const [schema, setSchema] = useState(null);
  const [schemaError, setSchemaError] = useState('');
  const [history, setHistory] = useState(loadHistory);

  const refreshConnection = useCallback(async () => {
    try {
      const [healthPayload, schemaPayload] = await Promise.all([getHealth(), getSchema()]);
      setHealth(healthPayload);
      setSchema(schemaPayload);
      setSchemaError('');
      return schemaPayload;
    } catch (error) {
      setHealth(null);
      setSchemaError(error.message);
      throw error;
    }
  }, []);

  useEffect(() => {
    refreshConnection().catch(() => {});
  }, [refreshConnection]);

  const runQuery = useCallback(async (question, signal) => {
    const result = await requestQuery(question, signal);
    const entry = { id: crypto.randomUUID?.() || `${Date.now()}`, question, result, createdAt: new Date().toISOString() };
    setHistory((current) => {
      const next = [entry, ...current].slice(0, 30);
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); } catch {}
      return next;
    });
    return result;
  }, []);

  const value = useMemo(() => ({
    health, schema, schemaError, history, runQuery, refreshConnection,
    connected: health?.status === 'ok' && schema?.status === 'ok',
  }), [health, schema, schemaError, history, runQuery, refreshConnection]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useData = () => useContext(Ctx);
