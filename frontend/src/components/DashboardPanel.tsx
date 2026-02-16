import type { DashboardSummary } from '../types';

interface DashboardPanelProps {
  summary: DashboardSummary;
}

export default function DashboardPanel({ summary }: DashboardPanelProps): JSX.Element {
  return (
    <section className="card">
      <h2>Dashboard summary</h2>
      <div className="stats-grid">
        <article>
          <p className="label">Total documents</p>
          <p className="value">{summary.total_documents}</p>
        </article>
        <article>
          <p className="label">Documents in IFA</p>
          <p className="value">{summary.documents_ifa}</p>
        </article>
        <article>
          <p className="label">Documents in IFC</p>
          <p className="value">{summary.documents_ifc}</p>
        </article>
        <article>
          <p className="label">Open approvals</p>
          <p className="value">{summary.open_approvals}</p>
        </article>
        <article>
          <p className="label">Total transmittals</p>
          <p className="value">{summary.total_transmittals}</p>
        </article>
      </div>
    </section>
  );
}
