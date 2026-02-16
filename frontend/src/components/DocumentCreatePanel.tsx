import { FormEvent, useState } from 'react';
import { createDocument } from '../api';
import type { SearchDocument } from '../types';

interface DocumentCreatePanelProps {
  token: string;
  onCreated: (document: SearchDocument) => void;
}

export default function DocumentCreatePanel({ token, onCreated }: DocumentCreatePanelProps): JSX.Element {
  const [projectCode, setProjectCode] = useState('PRJ-1');
  const [documentNumber, setDocumentNumber] = useState('DOC-1001');
  const [title, setTitle] = useState('New document');
  const [discipline, setDiscipline] = useState('General');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const created = await createDocument(token, {
        project_code: projectCode,
        document_number: documentNumber,
        title,
        discipline,
      });
      onCreated(created);
      setDocumentNumber('');
      setTitle('');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to create document');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card">
      <h2>Add document</h2>
      <form onSubmit={handleSubmit} className="stack">
        <label>
          Project code
          <input value={projectCode} onChange={(event) => setProjectCode(event.target.value)} required />
        </label>

        <label>
          Document number
          <input
            value={documentNumber}
            onChange={(event) => setDocumentNumber(event.target.value)}
            required
          />
        </label>

        <label>
          Title
          <input value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>

        <label>
          Discipline
          <input value={discipline} onChange={(event) => setDiscipline(event.target.value)} required />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Create document'}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
