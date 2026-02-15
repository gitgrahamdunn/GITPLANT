import type { DashboardSummary } from '../types';

interface DashboardPanelProps {
  summary: DashboardSummary;
}

export default function DashboardPanel({ summary }: DashboardPanelProps): JSX.Element {
  return (
    <section className="card">
      <h2>Dashboard</h2>
      <div className="stats-grid">
        <article>
          <p className="label">Total documents</p>
          <p className="value">{summary.total_documents}</p>
        </article>
        <article>
          <p className="label">Approvals pending</p>
          <p className="value">{summary.approvals_pending}</p>
        </article>
        <article>
          <p className="label">Open transmittals</p>
          <p className="value">{summary.open_transmittals}</p>
        </article>
      </div>

      <h3>Status breakdown</h3>
      <ul className="status-list">
        {Object.entries(summary.by_status).map(([status, count]) => (
          <li key={status}>
            <span>{status}</span>
            <strong>{count}</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}
