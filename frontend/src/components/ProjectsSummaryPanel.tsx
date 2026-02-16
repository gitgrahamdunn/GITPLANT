import { FormEvent, useState } from "react";
import type { ProjectCreateRequest, ProjectSummary } from "../types";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface ProjectsSummaryPanelProps {
  projects: ProjectSummary[];
  onOpenProject: (projectNumber: string) => void;
  onCreateProject: (payload: ProjectCreateRequest) => Promise<void>;
}

export default function ProjectsSummaryPanel({
  projects,
  onOpenProject,
  onCreateProject,
}: ProjectsSummaryPanelProps): JSX.Element {
  const [projectNumber, setProjectNumber] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleCreate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await onCreateProject({
      project_number: projectNumber.trim(),
      name: name.trim() || undefined,
      description: description.trim() || undefined,
    });
    setProjectNumber("");
    setName("");
    setDescription("");
  }

  return (
    <Card
      title="Projects"
      subtitle="Create a project first, then pull Plant documents into an active project workspace."
    >
      <form className="stack" onSubmit={(event) => void handleCreate(event)}>
        <div className="field-grid">
          <label className="field-label">
            <span>Project number (required)</span>
            <input
              className="input"
              value={projectNumber}
              onChange={(event) => setProjectNumber(event.target.value)}
              placeholder="PRJ-200"
              required
            />
          </label>
          <label className="field-label">
            <span>Name (optional)</span>
            <input
              className="input"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
        </div>
        <label className="field-label">
          <span>Description (optional)</span>
          <input
            className="input"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <div>
          <Button type="submit">Create project</Button>
        </div>
      </form>

      {!projects.length ? (
        <p className="hint">No projects yet. Create a project to start pulling documents.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Project Number</th>
                <th>Name</th>
                <th>Working docs</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>{project.project_number}</td>
                  <td>{project.name ?? "—"}</td>
                  <td>{project.working_doc_count}</td>
                  <td>{project.status}</td>
                  <td>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => onOpenProject(project.project_number)}
                    >
                      Open
                    </Button>
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
