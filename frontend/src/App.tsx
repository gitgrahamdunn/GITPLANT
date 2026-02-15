import { useEffect, useMemo, useState } from 'react';
import { fetchDashboard, fetchMe } from './api';
import DashboardPanel from './components/DashboardPanel';
import DocumentSearchPanel from './components/DocumentSearchPanel';
import LoginPanel from './components/LoginPanel';
import type { DashboardSummary, MeResponse } from './types';

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<MeResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isAuthed = useMemo(() => Boolean(token && me), [token, me]);

  useEffect(() => {
    if (!token) {
      setMe(null);
      setSummary(null);
      return;
    }

    async function loadData(): Promise<void> {
      setError(null);
      try {
        const [profile, dashboard] = await Promise.all([fetchMe(token), fetchDashboard(token)]);
        setMe(profile);
        setSummary(dashboard);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load app data');
        setToken(null);
      }
    }

    void loadData();
  }, [token]);

  return (
    <main className="container">
      <header>
        <h1>GitPlant EDMS Frontend</h1>
        <p className="hint">React + Vite client for auth, dashboard summary, and document search.</p>
      </header>

      {!isAuthed ? <LoginPanel onToken={setToken} /> : null}

      {error ? <p className="error">{error}</p> : null}

      {isAuthed && me && summary ? (
        <>
          <section className="card">
            <h2>Session</h2>
            <p>
              Signed in as <strong>{me.username}</strong> ({me.role})
            </p>
            <button type="button" onClick={() => setToken(null)}>
              Sign out
            </button>
          </section>
          <DashboardPanel summary={summary} />
          <DocumentSearchPanel token={token!} />
        </>
      ) : null}
    </main>
  );
}
