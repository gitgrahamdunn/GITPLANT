import { FormEvent, useEffect, useState } from 'react';
import { searchDocuments } from '../api';
import type { SearchDocument } from '../types';

interface DocumentSearchPanelProps {
  token: string;
  refreshKey?: number;
}

export default function DocumentSearchPanel({ token, refreshKey = 0 }: DocumentSearchPanelProps): JSX.Element {
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState<SearchDocument[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments(searchTerm: string): Promise<void> {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchDocuments(token, searchTerm);
      setDocuments(result.items);
      setTotal(result.total);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDocuments(query);
  }, [token, refreshKey]);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void loadDocuments(query);
  }

  return (
    <section className="card">
      <h2>Document search</h2>
      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by title or document number"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Searching…' : 'Search'}
        </button>
      </form>

      <p className="hint">{total} document(s) found.</p>
      {error ? <p className="error">{error}</p> : null}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Document No.</th>
              <th>Title</th>
              <th>Discipline</th>
              <th>Status</th>
              <th>Current revision</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>{document.id}</td>
                <td>{document.document_number}</td>
                <td>{document.title}</td>
                <td>{document.discipline}</td>
                <td>{document.status}</td>
                <td>{document.current_revision}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
