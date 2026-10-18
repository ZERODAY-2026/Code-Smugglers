const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
    });
  } catch (error) {
    throw new Error(`Cannot reach DataMind at ${API_BASE_URL}. Start the backend and try again.`);
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === 'string' ? payload.detail : 'The DataMind backend returned an error.';
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return payload;
}

export const apiBaseUrl = API_BASE_URL;
export const getHealth = () => request('/health');
export const getSchema = () => request('/api/schema');
export const askQuestion = (question, signal) => request('/api/query', {
  method: 'POST',
  body: JSON.stringify({ question }),
  signal,
});
