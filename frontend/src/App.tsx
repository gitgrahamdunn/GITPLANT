import { useEffect, useMemo, useState } from "react";
import {
  createProject,
  fetchDashboard,
  fetchMe,
  getProjectDetail,
  listDocuments,
  listProjects,
  pullDocumentsForProject,
  resetDemoData,
  seedDemoData,
} from "./api";
import DashboardPanel from "./components/DashboardPanel";
import DocumentSearchPanel from "./components/DocumentSearchPanel";
import LoginPanel from "./components/LoginPanel";
import PlantUploadPanel from "./components/PlantUploadPanel";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
import ProjectsSummaryPanel from "./components/ProjectsSummaryPanel";
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import Skeleton from "./components/ui/Skeleton";
import Toast from "./components/ui/Toast";
import type {
  DashboardSummary,
  MeResponse,
  ProjectCreateRequest,
  ProjectDetail,
  ProjectSummary,
  SearchDocument,
} from "./types";

const STORAGE_KEY = "gitplant.token";

type NavSection = "dashboard" | "projects" | "documents" | "plant_upload";

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );
  const [me, setMe] = useState<MeResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProjects, setActiveProjects] = useState<ProjectSummary[]>([]);
  const [documents, setDocuments] = useState<SearchDocument[]>([]);
  const [activeProjectNumber, setActiveProjectNumber] = useState<string | null>(
    null,
  );
  const [activeProject, setActiveProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchRefreshKey, setSearchRefreshKey] = useState(0);
  const [createdDocuments, setCreatedDocuments] = useState<SearchDocument[]>([]);
  const [activeSection, setActiveSection] = useState<NavSection>("dashboard");
  const [toast, setToast] = useState<string | null>(null);
  const [isRunningDemoAction, setIsRunningDemoAction] = useState(false);

  const isAuthed = useMemo(() => Boolean(token && me), [token, me]);

  async function refreshProjects(authToken: string): Promise<void> {
    const [allProjects, activeOnly] = await Promise.all([
      listProjects(authToken),
      listProjects(authToken, "ACTIVE"),
    ]);
    setProjects(allProjects);
    setActiveProjects(activeOnly);

    if (activeProjectNumber) {
      const detail = await getProjectDetail(authToken, activeProjectNumber);
      setActiveProject(detail);
    }
  }

  async function refreshDocuments(authToken: string): Promise<void> {
    const result = await listDocuments(authToken);
    setDocuments(result.items);
  }

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeout = window.setTimeout(() => setToast(null), 2400);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  useEffect(() => {
    if (!token) {
      setMe(null);
      setSummary(null);
      setProjects([]);
      setActiveProjects([]);
      setDocuments([]);
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
        const [profile, dashboard] = await Promise.all([
          fetchMe(authToken),
          fetchDashboard(authToken),
        ]);
        setMe(profile);
        setSummary(dashboard);
        await Promise.all([refreshProjects(authToken), refreshDocuments(authToken)]);
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

  async function handleCreateProject(payload: ProjectCreateRequest): Promise<void> {
    if (!token) {
      return;
    }

    const created = await createProject(token, payload);
    await refreshProjects(token);
    setActiveProjectNumber(created.project_number);
    setActiveProject(await getProjectDetail(token, created.project_number));
    setActiveSection("projects");
    setToast(`Project ${created.project_number} created.`);
  }

  function handleLogout(): void {
    setToken(null);
    setMe(null);
    setSummary(null);
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
      setToast(
        `${action === "seed" ? "Seeded" : "Reset"} demo data: ${result.documents_created} docs, ${result.approvals_created} approval(s).`,
      );
      const dashboard = await fetchDashboard(token);
      setSummary(dashboard);
      await Promise.all([refreshProjects(token), refreshDocuments(token)]);
    } catch (demoError) {
      setError(
        demoError instanceof Error ? demoError.message : "Demo action failed",
      );
    } finally {
      setIsRunningDemoAction(false);
    }
  }

  async function handlePullForProject(
    documentIds: number[],
    projectId: string,
  ): Promise<void> {
    if (!token) {
      return;
    }

    const result = await pullDocumentsForProject(token, projectId, documentIds);
    await refreshProjects(token);
    const skipped = result.skipped_document_ids.length;
    setToast(
      `Pulled ${result.created.length} document(s) into ${result.project_number}${skipped ? ` (${skipped} skipped)` : ""}.`,
    );
    setActiveProjectNumber(result.project_number);
    setActiveProject(await getProjectDetail(token, result.project_number));
    setActiveSection("projects");
    setSearchRefreshKey((value) => value + 1);
  }

  async function refreshActiveProject(): Promise<void> {
    if (!token || !activeProjectNumber) {
      return;
    }

    setActiveProject(await getProjectDetail(token, activeProjectNumber));
    await refreshProjects(token);
  }

  async function handleProjectMerged(): Promise<void> {
    if (!token) {
      return;
    }

    await Promise.all([
      refreshProjects(token),
      refreshDocuments(token),
      fetchDashboard(token).then(setSummary),
    ]);
    setSearchRefreshKey((value) => value + 1);
    setToast("Project merged into plant revisions.");
  }

  function handleDocumentUpdated(document: SearchDocument): void {
    setSearchRefreshKey((value) => value + 1);
    setCreatedDocuments((existing) => [
      document,
      ...existing.filter((item) => item.id !== document.id),
    ]);
    setDocuments((existing) => [
      document,
      ...existing.filter((item) => item.id !== document.id),
    ]);
    setToast("Plant revision uploaded successfully.");
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <h1>GitPlant EDMS</h1>
        <p className="muted">Professional document control workspace.</p>
        <nav className="stack-sm" aria-label="Primary">
          {[
            ["dashboard", "Dashboard"],
            ["projects", "Projects"],
            ["documents", "Documents (Plant)"],
            ["plant_upload", "Plant Upload"],
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
                <Button type="button" variant="secondary" onClick={handleLogout}>
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

            {(activeSection === "dashboard" || activeSection === "documents") &&
            summary ? (
              <DashboardPanel summary={summary} />
            ) : null}

            {activeSection === "projects" && (
              <ProjectsSummaryPanel
                projects={projects}
                onCreateProject={handleCreateProject}
                onOpenProject={(projectNumber) => {
                  void openProject(projectNumber);
                }}
              />
            )}

            {activeSection === "projects" && activeProject ? (
              <ProjectDetailPanel
                token={token!}
                project={activeProject}
                onRefresh={refreshActiveProject}
                onMerged={handleProjectMerged}
              />
            ) : null}

            {activeSection === "documents" && (
              <DocumentSearchPanel
                token={token!}
                refreshKey={searchRefreshKey}
                createdDocuments={createdDocuments}
                activeProjects={activeProjects}
                onCreateProjectCta={() => setActiveSection("projects")}
                onPullForProject={handlePullForProject}
              />
            )}

            {activeSection === "plant_upload" && (
              <PlantUploadPanel
                token={token!}
                documents={documents}
                onUploaded={handleDocumentUpdated}
              />
            )}
          </>
        ) : null}
      </section>

      {toast ? <Toast message={toast} /> : null}
    </main>
  );
}
