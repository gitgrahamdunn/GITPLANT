import { useEffect, useMemo, useState } from "react";
import {
  createProject,
  downloadDocumentPdf,
  fetchMe,
  getProjectDetail,
  listDocuments,
  listProjects,
  login,
  markWorkingReady,
  mergeProjectToPlant,
  pullDocumentsForProject,
  resetDemoData,
  seedDemoData,
} from "./api";
import { logUiEvent } from "./logUiEvent";
import type { MeResponse, ProjectDetail, ProjectSummary, SearchDocument } from "./types";

const STORAGE_KEY = "gitplant.token";
const THEME_STORAGE_KEY = "gitplant.theme";
type Tab = "plant" | "projects";
type ProjectFilter = "OPEN" | "MERGED" | "CLOSED";
type ThemeMode = "dark" | "light";

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [me, setMe] = useState<MeResponse | null>(null);
  const [docs, setDocs] = useState<SearchDocument[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [tab, setTab] = useState<Tab>("plant");
  const [filter, setFilter] = useState<ProjectFilter>("OPEN");
  const [query, setQuery] = useState("");
  const [projectQuery, setProjectQuery] = useState("");
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [showPullModalForDoc, setShowPullModalForDoc] = useState<number | null>(null);
  const [selectedOpenProjectId, setSelectedOpenProjectId] = useState("");
  const [newProjectNumber, setNewProjectNumber] = useState("");
  const [newProjectTitle, setNewProjectTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return savedTheme === "light" ? "light" : "dark";
  });

  const authed = Boolean(token && me);

  const openProjects = useMemo(() => projects.filter((p) => p.status === "ACTIVE"), [projects]);
  const visibleDocs = useMemo(
    () => docs.filter((d) => `${d.document_number} ${d.title}`.toLowerCase().includes(query.toLowerCase())),
    [docs, query],
  );
  const visibleProjects = useMemo(() => {
    const statusMap: Record<ProjectFilter, string> = { OPEN: "ACTIVE", MERGED: "MERGED", CLOSED: "CLOSED" };
    return projects
      .filter((p) => p.status === statusMap[filter])
      .filter((p) => `${p.project_number} ${p.name ?? ""}`.toLowerCase().includes(projectQuery.toLowerCase()))
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }, [projects, filter, projectQuery]);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 2500);
    return () => window.clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  async function refreshAll(authToken: string): Promise<void> {
    const [profile, docsResp, projResp] = await Promise.all([
      fetchMe(authToken),
      listDocuments(authToken),
      listProjects(authToken),
    ]);
    setMe(profile);
    setDocs(docsResp.items);
    setProjects(projResp);
  }

  useEffect(() => {
    if (!token) {
      localStorage.removeItem(STORAGE_KEY);
      setMe(null);
      setDocs([]);
      setProjects([]);
      setSelectedProject(null);
      return;
    }
    localStorage.setItem(STORAGE_KEY, token);
    setLoading(true);
    setError(null);
    void refreshAll(token)
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load");
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function handleLogin(email: string, password: string): Promise<void> {
    try {
      logUiEvent(token, "login_click", { email });
      setError(null);
      setLoading(true);
      const result = await login(email, password);
      setToken(result.access_token);
    } catch (e) {
      console.error("[auth] Login failed", e);
      setError(e instanceof Error ? e.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function runSafe(name: string, action: () => Promise<void>, payload?: Record<string, unknown>): Promise<void> {
    try {
      logUiEvent(token, name, payload);
      setError(null);
      setLoading(true);
      await action();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Action failed";
      setError(msg);
      setToast(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="gh-root">
      <header className="gh-header">
        <strong>GITPLANT</strong>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search" />
        <div className="header-actions">
          <button
            type="button"
            className="theme-toggle"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
          >
            {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
          </button>
          {authed ? (
            <>
              <details>
                <summary>Demo</summary>
                <div className="menu">
                  <button onClick={() => void runSafe("seed_demo", async () => { await seedDemoData(token!); await refreshAll(token!); setToast("Demo data seeded"); })}>Seed</button>
                  <button onClick={() => void runSafe("reset_demo", async () => { await resetDemoData(token!); await refreshAll(token!); setToast("Demo data reset"); })}>Reset</button>
                </div>
              </details>
              <span>{me?.email} · dev</span>
              <button onClick={() => { logUiEvent(token, "logout_click"); setToken(null); }}>Logout</button>
            </>
          ) : null}
        </div>
      </header>

      {!authed ? (
        <section className="login-panel">
          <h2>Sign in</h2>
          <LoginForm onSubmit={handleLogin} loading={loading} error={error} />
        </section>
      ) : (
        <>
          <nav className="repo-tabs">
            <button className={tab === "plant" ? "active" : ""} onClick={() => setTab("plant")}>Code (Plant)</button>
            <button className={tab === "projects" ? "active" : ""} onClick={() => setTab("projects")}>Pull Requests (Projects)</button>
          </nav>

          {error ? <div className="banner-error">{error}</div> : null}
          {loading ? <div className="banner-info">Loading...</div> : null}

          {tab === "plant" ? (
            <section className="page-card">
              <h2>Plant documents</h2>
              <table>
                <thead><tr><th>Doc #</th><th>Title</th><th>Rev</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {visibleDocs.map((d) => (
                    <tr key={d.id}>
                      <td>{d.document_number}</td><td>{d.title}</td><td>{d.current_revision}</td><td>{d.status}</td>
                      <td className="toolbar">
                        <button onClick={() => void runSafe("open_file", async () => {
                          const blob = await downloadDocumentPdf(token!, d.id);
                          const url = URL.createObjectURL(blob);
                          window.open(url, "_blank", "noopener,noreferrer");
                        })}>Open file</button>
                        <button onClick={() => setShowPullModalForDoc(d.id)}>Pull into Project</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : (
            <section className="page-card">
              <h2>Pull Requests</h2>
              <div className="toolbar">
                <input placeholder="Search PRJ-### or title" value={projectQuery} onChange={(e) => setProjectQuery(e.target.value)} />
                {(["OPEN", "MERGED", "CLOSED"] as ProjectFilter[]).map((item) => (
                  <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>{item}</button>
                ))}
              </div>
              <ul className="project-list">
                {visibleProjects.map((p) => (
                  <li key={p.id}>
                    <button onClick={() => void runSafe("open_project", async () => { const detail = await getProjectDetail(token!, p.project_number); setSelectedProject(detail); }, { project: p.project_number })}>
                      <strong>{p.project_number}: {p.name}</strong> · {p.status === "ACTIVE" ? "Open" : p.status} · {p.working_doc_count} docs changed
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {selectedProject ? (
            <section className="page-card pr-page">
              <div className="pr-header"><h3>{selectedProject.project_number}: {selectedProject.name}</h3><span>{selectedProject.status === "ACTIVE" ? "Open" : selectedProject.status}</span></div>
              <div className="pr-grid">
                <div>
                  <h4>Files changed</h4>
                  <table><thead><tr><th>Doc #</th><th>Status</th><th>Actions</th></tr></thead><tbody>{selectedProject.working_docs.map((w) => <tr key={w.id}><td>{w.document_number}</td><td>{w.status}</td><td>{w.status === "WORKING" ? <button onClick={() => void runSafe("mark_ready", async () => { await markWorkingReady(token!, selectedProject.project_number, w.id); const detail = await getProjectDetail(token!, selectedProject.project_number); setSelectedProject(detail); await refreshAll(token!); })}>Mark READY</button> : null}</td></tr>)}</tbody></table>
                  <h4>Conversation</h4>
                  <ul>{selectedProject.events.map((e) => <li key={e.id}>{new Date(e.created_at).toLocaleString()} - {e.details}</li>)}</ul>
                </div>
                <aside className="merge-box">
                  <p>{selectedProject.working_docs.filter((w) => w.status === "READY").length} ready</p>
                  <button disabled={!selectedProject.working_docs.some((w) => w.status === "READY")} onClick={() => void runSafe("merge_to_plant", async () => { await mergeProjectToPlant(token!, selectedProject.project_number); const detail = await getProjectDetail(token!, selectedProject.project_number); setSelectedProject(detail); await refreshAll(token!); setToast("Merged to Plant"); }, { project: selectedProject.project_number })}>Merge</button>
                </aside>
              </div>
            </section>
          ) : null}

          {showPullModalForDoc ? (
            <div className="modal-backdrop"><div className="modal-card"><h4>Pull to Project</h4>
              <select value={selectedOpenProjectId} onChange={(e) => setSelectedOpenProjectId(e.target.value)}>
                <option value="">Select open project</option>
                {openProjects.map((p) => <option key={p.id} value={p.id}>{p.project_number}</option>)}
              </select>
              <input placeholder="New project number (required)" value={newProjectNumber} onChange={(e) => setNewProjectNumber(e.target.value)} />
              <input placeholder="New project title" value={newProjectTitle} onChange={(e) => setNewProjectTitle(e.target.value)} />
              <div className="toolbar">
                <button onClick={() => void runSafe("pull_to_project", async () => {
                  let projectId = selectedOpenProjectId;
                  if (!projectId && newProjectNumber.trim()) {
                    const created = await createProject(token!, { project_number: newProjectNumber.trim(), name: newProjectTitle.trim() || newProjectNumber.trim() });
                    projectId = created.id;
                  }
                  if (!projectId) throw new Error("Select an open project or provide a new project number.");
                  await pullDocumentsForProject(token!, projectId, [showPullModalForDoc]);
                  await refreshAll(token!);
                  setShowPullModalForDoc(null);
                  setSelectedOpenProjectId("");
                  setNewProjectNumber("");
                  setNewProjectTitle("");
                  setToast("Document pulled to project");
                }, { documentId: showPullModalForDoc })}>Pull</button>
                <button onClick={() => setShowPullModalForDoc(null)}>Cancel</button>
              </div>
            </div></div>
          ) : null}
        </>
      )}
      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  );
}

function LoginForm({ onSubmit, loading, error }: { onSubmit: (email: string, password: string) => Promise<void>; loading: boolean; error: string | null }): JSX.Element {
  const [email, setEmail] = useState("user@edms.local");
  const [password, setPassword] = useState("user123");
  return (
    <>
      <form onSubmit={(e) => { e.preventDefault(); void onSubmit(email, password); }} className="toolbar">
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button disabled={loading} type="submit">{loading ? "Signing in..." : "Sign in"}</button>
      </form>
      {error ? <div className="banner-error">{error}</div> : null}
    </>
  );
}
