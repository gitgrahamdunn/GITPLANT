import type { DashboardSummary } from "../types";
import Card from "./ui/Card";

interface DashboardPanelProps {
  summary: DashboardSummary;
}

export default function DashboardPanel({
  summary,
}: DashboardPanelProps): JSX.Element {
  return (
    <Card title="Dashboard" subtitle="Live document control metrics.">
      <div className="stats-grid">
        <article className="metric-card">
          <p className="metric-label">Total documents</p>
          <p className="metric-value">{summary.total_documents}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Documents in IFA</p>
          <p className="metric-value">{summary.documents_ifa}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Documents in IFC</p>
          <p className="metric-value">{summary.documents_ifc}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Open approvals</p>
          <p className="metric-value">{summary.open_approvals}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Total transmittals</p>
          <p className="metric-value">{summary.total_transmittals}</p>
        </article>
      </div>
    </Card>
  );
}
