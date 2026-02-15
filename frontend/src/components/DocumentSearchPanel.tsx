import { FormEvent, useEffect, useState } from 'react';
import { searchDocuments } from '../api';
import type { SearchDocument } from '../types';

interface DocumentSearchPanelProps {
  token: string;
}

export default function DocumentSearchPanel({ token }: DocumentSearchPanelProps): JSX.Element {
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState<SearchDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments(searchTerm: string): Promise<void> {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchDocuments(token, searchTerm);
      setDocuments(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDocuments('');
  }, []);

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
          placeholder="Search by title, document number, or discipline"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Searching…' : 'Search'}
        </button>
      </form>

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
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>{document.id}</td>
                <td>{document.doc_number}</td>
                <td>{document.title}</td>
                <td>{document.discipline}</td>
                <td>{document.current_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
