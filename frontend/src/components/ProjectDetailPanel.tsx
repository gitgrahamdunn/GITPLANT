import {
  abandonWorkingRevision,
  markWorkingReady,
  mergeProjectToPlant,
} from "../api";
import type { ProjectDetail } from "../types";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface ProjectDetailPanelProps {
  token: string;
  project: ProjectDetail;
  onRefresh: () => Promise<void>;
  onMerged: () => Promise<void>;
}

export default function ProjectDetailPanel({
  token,
  project,
  onRefresh,
  onMerged,
}: ProjectDetailPanelProps): JSX.Element {
  async function setReady(workingId: number): Promise<void> {
    await markWorkingReady(token, project.project_number, workingId);
    await onRefresh();
  }

  async function abandon(workingId: number): Promise<void> {
    await abandonWorkingRevision(token, project.project_number, workingId);
    await onRefresh();
  }

  async function mergeToPlant(): Promise<void> {
    await mergeProjectToPlant(token, project.project_number);
    await onMerged();
  }

  return (
    <Card
      title={`Project ${project.project_number}`}
      subtitle={project.description ?? "Working set details"}
      actions={
        <Button type="button" onClick={() => void mergeToPlant()}>
          Merge to Plant
        </Button>
      }
    >
      <p className="hint">
        Created by {project.created_by} · status {project.status}
      </p>

      {!project.working_docs.length ? (
        <Banner tone="info" message="No pulled documents in this project." />
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
                <th>Pulled at</th>
                <th>Last updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {project.working_docs.map((item) => (
                <tr key={item.id}>
                  <td>{item.document_number}</td>
                  <td>{item.title}</td>
                  <td>{item.current_plant_revision}</td>
                  <td>{item.working_revision_label}</td>
                  <td>
                    <span
                      className={`status-badge status-${item.status.toLowerCase()}`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td>{item.pulled_by}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                  <td>
                    <div className="table-actions">
                      {item.status === "WORKING" ? (
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => void setReady(item.id)}
                        >
                          Mark ready
                        </Button>
                      ) : null}
                      {(item.status === "WORKING" ||
                        item.status === "READY") && (
                        <Button
                          type="button"
                          variant="danger"
                          onClick={() => void abandon(item.id)}
                        >
                          Abandon
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
