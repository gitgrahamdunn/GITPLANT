import type { ProjectSummary } from "../types";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface ProjectsSummaryPanelProps {
  projects: ProjectSummary[];
  onOpenProject: (projectNumber: string) => void;
}

export default function ProjectsSummaryPanel({
  projects,
  onOpenProject,
}: ProjectsSummaryPanelProps): JSX.Element {
  return (
    <Card
      title="Projects Summary"
      subtitle="Active project working sets and pulled document counts."
    >
      {!projects.length ? (
        <p className="hint">
          No projects yet. Pull documents into a project to begin.
        </p>
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
