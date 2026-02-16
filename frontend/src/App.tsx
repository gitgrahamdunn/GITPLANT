import { useEffect, useMemo, useState } from "react";
import {
  fetchMe,
  getProjectDetail,
  listProjects,
  pullDocumentsForProject,
  resetDemoData,
  seedDemoData,
} from "./api";
import DocumentCreatePanel from "./components/DocumentCreatePanel";
import DocumentSearchPanel from "./components/DocumentSearchPanel";
import LoginPanel from "./components/LoginPanel";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
import ProjectsSummaryPanel from "./components/ProjectsSummaryPanel";
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import Skeleton from "./components/ui/Skeleton";
import Toast from "./components/ui/Toast";
import type {
  MeResponse,
  ProjectDetail,
  ProjectSummary,
  SearchDocument,
} from "./types";

const STORAGE_KEY = "gitplant.token";

type NavSection = "projects" | "documents" | "upload" | "audit";

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );
  const [me, setMe] = useState<MeResponse | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProjectNumber, setActiveProjectNumber] = useState<string | null>(
    null,
  );
  const [activeProject, setActiveProject] = useState<ProjectDetail | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchRefreshKey, setSearchRefreshKey] = useState(0);
  const [createdDocuments, setCreatedDocuments] = useState<SearchDocument[]>(
    [],
  );
  const [activeSection, setActiveSection] = useState<NavSection>("projects");
  const [toast, setToast] = useState<string | null>(null);
  const [isRunningDemoAction, setIsRunningDemoAction] = useState(false);

  const isAuthed = useMemo(() => Boolean(token && me), [token, me]);

  async function refreshProjects(authToken: string): Promise<void> {
    const allProjects = await listProjects(authToken);
    setProjects(allProjects);

    if (activeProjectNumber) {
      const detail = await getProjectDetail(authToken, activeProjectNumber);
      setActiveProject(detail);
    }
  }

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeout = window.setTimeout(() => setToast(null), 2600);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  useEffect(() => {
    if (!token) {
      setMe(null);
      setProjects([]);
      setActiveProjectNumber(null);
      setActiveProject(null);
      localStorage.removeItem(STORAGE_KEY);
      return;
    }

    const authToken = token;
    localStorage.setItem(STORAGE_KEY, authToken);

    async function loadData(): Promise<void> {
      setError(null);
      setIsLoading(true);
      try {
        const profile = await fetchMe(authToken);
        setMe(profile);
        await refreshProjects(authToken);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load app data",
        );
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    }

    void loadData();
  }, [token]);

  async function openProject(projectNumber: string): Promise<void> {
    if (!token) {
      return;
    }

    setActiveProjectNumber(projectNumber);
    const detail = await getProjectDetail(token, projectNumber);
    setActiveProject(detail);
    setActiveSection("projects");
  }

  function handleLogout(): void {
    setToken(null);
    setMe(null);
    setProjects([]);
    setActiveProjectNumber(null);
    setActiveProject(null);
    setError(null);
    setCreatedDocuments([]);
    localStorage.removeItem(STORAGE_KEY);
    setToast("Signed out.");
  }

  async function runDemoAction(action: "seed" | "reset"): Promise<void> {
    if (!token) {
      return;
    }

    setError(null);
    setIsRunningDemoAction(true);
    try {
      const result =
        action === "seed"
          ? await seedDemoData(token)
          : await resetDemoData(token);
      setCreatedDocuments([]);
      setSearchRefreshKey((value) => value + 1);
      await refreshProjects(token);
      setToast(
        `${action === "seed" ? "Seeded" : "Reset"} demo data: ${result.documents_created} docs`,
      );
    } catch (demoError) {
      setError(
        demoError instanceof Error ? demoError.message : "Demo action failed",
      );
    } finally {
      setIsRunningDemoAction(false);
    }
  }

  function handleDocumentCreated(document: SearchDocument): void {
    setSearchRefreshKey((value) => value + 1);
    setCreatedDocuments((existing) => [
      document,
      ...existing.filter((item) => item.id !== document.id),
    ]);
    setToast("Document record created successfully.");
  }

  async function handlePullForProject(
    documentIds: number[],
    projectNumber: string,
  ): Promise<void> {
    if (!token) {
      return;
    }

    await pullDocumentsForProject(token, projectNumber, documentIds);
    await refreshProjects(token);
    await openProject(projectNumber);
    setSearchRefreshKey((value) => value + 1);
    setToast(`Pulled ${documentIds.length} docs to ${projectNumber}.`);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <h1>GitPlant EDMS</h1>
        <p className="muted">Plant & project working sets.</p>
        <nav className="stack-sm" aria-label="Primary">
          {[
            ["projects", "Projects"],
            ["documents", "Documents"],
            ["upload", "Upload PDFs"],
            ["audit", "Audit"],
          ].map(([key, label]) => (
            <button
              key={key}
              className={`nav-link${activeSection === key ? " is-active" : ""}`}
              onClick={() => setActiveSection(key as NavSection)}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="content">
        {!isAuthed ? <LoginPanel onToken={setToken} /> : null}

        {error ? <p className="banner banner-error">{error}</p> : null}

        {isAuthed && me ? (
          <>
            <Card
              title="Session"
              subtitle={`Signed in as ${me.email} (${me.role}).`}
              actions={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleLogout}
                >
                  Sign out
                </Button>
              }
            />

            {isLoading ? <Skeleton lines={4} /> : null}

            <Card
              title="Demo data tools"
              subtitle="Development-only controls. Reset will wipe current documents and files."
            >
              <div className="table-actions">
                <Button
                  type="button"
                  variant="secondary"
                  disabled={isRunningDemoAction}
                  onClick={() => {
                    void runDemoAction("seed");
                  }}
                >
                  Seed demo data
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  disabled={isRunningDemoAction}
                  onClick={() => {
                    void runDemoAction("reset");
                  }}
                >
                  Reset demo
                </Button>
              </div>
              <p className="hint">
                Only enabled when backend sets ENABLE_DEMO_TOOLS=true.
              </p>
            </Card>

            {(activeSection === "projects" ||
              activeSection === "documents") && (
              <ProjectsSummaryPanel
                projects={projects}
                onOpenProject={(projectNumber) => {
                  void openProject(projectNumber);
                }}
              />
            )}

            {activeSection === "projects" && activeProject ? (
              <ProjectDetailPanel
                token={token!}
                project={activeProject}
                onRefresh={async () => {
                  await openProject(activeProject.project_number);
                }}
                onMerged={async () => {
                  await openProject(activeProject.project_number);
                  await refreshProjects(token!);
                  setSearchRefreshKey((value) => value + 1);
                  setToast("Project merged to Plant.");
                }}
              />
            ) : null}

            {(activeSection === "upload" || activeSection === "documents") && (
              <DocumentCreatePanel
                token={token!}
                onCreated={handleDocumentCreated}
              />
            )}

            {(activeSection === "documents" || activeSection === "audit") && (
              <DocumentSearchPanel
                token={token!}
                refreshKey={searchRefreshKey}
                createdDocuments={createdDocuments}
                onPullForProject={handlePullForProject}
              />
            )}
          </>
        ) : null}
      </section>

      {toast ? <Toast message={toast} /> : null}
    </main>
  );
}
