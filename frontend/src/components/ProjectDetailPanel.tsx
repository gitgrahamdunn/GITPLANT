import { useMemo, useState } from "react";
import {
  abandonWorkingRevision,
  markWorkingReady,
  mergeProjectToPlant,
  uploadProjectWorkingRevision,
} from "../api";
import type { ProjectDetail, ProjectWorkingDoc } from "../types";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface ProjectDetailPanelProps {
  token: string;
  project: ProjectDetail;
  onRefresh: () => Promise<void>;
  onMerged: () => Promise<void>;
}

type ProjectTab = "WORKING" | "READY" | "MERGED";

export default function ProjectDetailPanel({
  token,
  project,
  onRefresh,
  onMerged,
}: ProjectDetailPanelProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<ProjectTab>("WORKING");
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readyCount = useMemo(
    () => project.working_docs.filter((item) => item.status === "READY").length,
    [project.working_docs],
  );

  const filteredDocs = useMemo(() => {
    if (activeTab === "WORKING") {
      return project.working_docs.filter((item) => item.status === "WORKING");
    }
    return project.working_docs.filter((item) => item.status === activeTab);
  }, [activeTab, project.working_docs]);

  async function setReady(workingId: number): Promise<void> {
    setError(null);
    await markWorkingReady(token, project.project_number, workingId);
    await onRefresh();
  }

  async function abandon(workingId: number): Promise<void> {
    setError(null);
    await abandonWorkingRevision(token, project.project_number, workingId);
    await onRefresh();
  }

  async function uploadWorking(workingId: number, file?: File): Promise<void> {
    if (!file) {
      return;
    }
    setError(null);
    await uploadProjectWorkingRevision(token, project.id, workingId, file);
    await onRefresh();
  }

  async function mergeToPlant(): Promise<void> {
    setError(null);
    await mergeProjectToPlant(token, project.project_number);
    setShowMergeConfirm(false);
    await onMerged();
  }

  return (
    <Card
      title={`Project ${project.project_number}`}
      subtitle={project.description ?? "Working set details"}
      actions={
        <Button
          type="button"
          disabled={!readyCount}
          onClick={() => setShowMergeConfirm(true)}
        >
          Push to Plant
        </Button>
      }
    >
      <p className="hint">Created by {project.created_by} · status {project.status}</p>
      {error ? <Banner tone="error" message={error} /> : null}

      <div className="table-actions">
        <Button
          type="button"
          variant={activeTab === "WORKING" ? "primary" : "secondary"}
          onClick={() => setActiveTab("WORKING")}
        >
          Working
        </Button>
        <Button
          type="button"
          variant={activeTab === "READY" ? "primary" : "secondary"}
          onClick={() => setActiveTab("READY")}
        >
          Ready
        </Button>
        <Button
          type="button"
          variant={activeTab === "MERGED" ? "primary" : "secondary"}
          onClick={() => setActiveTab("MERGED")}
        >
          Merged
        </Button>
      </div>

      {!filteredDocs.length ? (
        <Banner tone="info" message={`No ${activeTab.toLowerCase()} docs in this project.`} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Doc #</th>
                <th>Title</th>
                <th>Plant rev</th>
                <th>Working rev</th>
                <th>Status</th>
                <th>Pulled by</th>
                <th>Last updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map((item) => (
                <ProjectRow
                  key={item.id}
                  item={item}
                  onSetReady={setReady}
                  onAbandon={abandon}
                  onUploadWorking={uploadWorking}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showMergeConfirm ? (
        <div className="modal-backdrop" role="presentation">
          <div className="modal-card" role="dialog" aria-modal="true">
            <h3>Push ready revisions to Plant?</h3>
            <p className="hint">{readyCount} READY document(s) will be merged to Plant current revisions.</p>
            <div className="table-actions">
              <Button type="button" onClick={() => void mergeToPlant()}>
                Confirm Push
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowMergeConfirm(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

interface ProjectRowProps {
  item: ProjectWorkingDoc;
  onSetReady: (workingId: number) => Promise<void>;
  onAbandon: (workingId: number) => Promise<void>;
  onUploadWorking: (workingId: number, file?: File) => Promise<void>;
}

function ProjectRow({
  item,
  onSetReady,
  onAbandon,
  onUploadWorking,
}: ProjectRowProps): JSX.Element {
  return (
    <tr>
      <td>{item.document_number}</td>
      <td>{item.title}</td>
      <td>{item.current_plant_revision}</td>
      <td>{item.working_revision_label}</td>
      <td>
        <span className={`status-badge status-${item.status.toLowerCase()}`}>
          {item.status}
        </span>
      </td>
      <td>{item.pulled_by}</td>
      <td>{new Date(item.updated_at).toLocaleString()}</td>
      <td>
        <div className="table-actions">
          {item.status === "WORKING" ? (
            <>
              <label className="subtle-button">
                Upload working revision
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  hidden
                  onChange={(event) => {
                    void onUploadWorking(item.id, event.target.files?.[0]);
                    event.target.value = "";
                  }}
                />
              </label>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void onSetReady(item.id)}
              >
                Mark Ready for Merge
              </Button>
            </>
          ) : null}
          {(item.status === "WORKING" || item.status === "READY") && (
            <Button
              type="button"
              variant="danger"
              onClick={() => void onAbandon(item.id)}
            >
              Abandon
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}
