import { useEffect, useMemo, useState } from 'react';
import { fetchDashboard, fetchMe } from './api';
import DashboardPanel from './components/DashboardPanel';
import DocumentSearchPanel from './components/DocumentSearchPanel';
import LoginPanel from './components/LoginPanel';
import type { DashboardSummary, MeResponse } from './types';

const STORAGE_KEY = 'gitplant.token';

function canViewDashboard(role: MeResponse['role']): boolean {
  return role === 'document_controller' || role === 'approver';
}

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [me, setMe] = useState<MeResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isAuthed = useMemo(() => Boolean(token && me), [token, me]);

  useEffect(() => {
    if (!token) {
      setMe(null);
      setSummary(null);
      localStorage.removeItem(STORAGE_KEY);
      return;
    }

    localStorage.setItem(STORAGE_KEY, token);

    async function loadData(): Promise<void> {
      setError(null);
      try {
        const profile = await fetchMe(token);
        setMe(profile);

        if (canViewDashboard(profile.role)) {
          const dashboard = await fetchDashboard(token);
          setSummary(dashboard);
        } else {
          setSummary(null);
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load app data');
        setToken(null);
      }
    }

    void loadData();
  }, [token]);

  function handleLogout(): void {
    setToken(null);
    setMe(null);
    setSummary(null);
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
  }

  return (
    <main className="container">
      <header>
        <h1>GitPlant EDMS Frontend</h1>
        <p className="hint">React + Vite client for auth, dashboard summary, and document search.</p>
      </header>

      {!isAuthed ? <LoginPanel onToken={setToken} /> : null}

      {error ? <p className="error">{error}</p> : null}

      {isAuthed && me ? (
        <>
          <section className="card">
            <h2>Session</h2>
            <p>
              Signed in as <strong>{me.email}</strong> ({me.role})
            </p>
            <button type="button" onClick={handleLogout}>
              Sign out
            </button>
          </section>

          {summary ? (
            <DashboardPanel summary={summary} />
          ) : (
            <section className="card">
              <h2>Dashboard summary</h2>
              <p className="hint">Dashboard metrics are available for approver and document controller roles.</p>
            </section>
          )}

          <DocumentSearchPanel token={token!} />
        </>
      ) : null}
    </main>
  );
}
