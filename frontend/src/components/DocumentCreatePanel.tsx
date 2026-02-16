import { ChangeEvent, DragEvent, FormEvent, useMemo, useRef, useState } from 'react';
import { createDocument } from '../api';
import type { SearchDocument } from '../types';

interface DocumentCreatePanelProps {
  token: string;
  onCreated: (document: SearchDocument) => void;
}

function toDocumentNumber(fileName: string, index: number): string {
  const base = fileName.replace(/\.pdf$/i, '').trim();
  const normalized = base
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toUpperCase();

  if (!normalized) {
    return `PDF-${Date.now()}-${index + 1}`;
  }

  return normalized;
}

function toTitle(fileName: string): string {
  return fileName.replace(/\.pdf$/i, '').trim() || 'Untitled PDF document';
}

function filterPdfFiles(fileList: FileList | File[]): File[] {
  return Array.from(fileList).filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'));
}

export default function DocumentCreatePanel({ token, onCreated }: DocumentCreatePanelProps): JSX.Element {
  const [projectCode, setProjectCode] = useState('PRJ-1');
  const [discipline, setDiscipline] = useState('General');
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const totalFileSizeLabel = useMemo(() => {
    const bytes = files.reduce((sum, file) => sum + file.size, 0);
    if (bytes < 1024 * 1024) {
      return `${Math.round(bytes / 1024)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }, [files]);

  function addFiles(newFiles: File[]): void {
    if (!newFiles.length) {
      setError('Only PDF files are supported right now.');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setFiles((existing) => {
      const incoming = newFiles.filter((newFile) => !existing.some((currentFile) => currentFile.name === newFile.name && currentFile.size === newFile.size));
      return [...existing, ...incoming];
    });
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>): void {
    if (!event.target.files) {
      return;
    }

    addFiles(filterPdfFiles(event.target.files));
    event.target.value = '';
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setIsDragging(false);
    addFiles(filterPdfFiles(event.dataTransfer.files));
  }

  function removeFile(targetIndex: number): void {
    setFiles((existing) => existing.filter((_, index) => index !== targetIndex));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!files.length) {
      setError('Please drop at least one PDF file or use the file picker.');
      return;
    }

    setIsSubmitting(true);

    let createdCount = 0;
    for (const [index, file] of files.entries()) {
      try {
        const created = await createDocument(token, {
          project_code: projectCode,
          document_number: toDocumentNumber(file.name, index),
          title: toTitle(file.name),
          discipline,
        });
        onCreated(created);
        createdCount += 1;
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : 'Failed to create documents from selected PDFs');
        break;
      }
    }

    if (createdCount > 0) {
      setSuccessMessage(`Created ${createdCount} document record(s) from PDF selection.`);
      setFiles((existing) => existing.slice(createdCount));
    }

    setIsSubmitting(false);
  }

  return (
    <section className="card">
      <h2>Add documents (PDF)</h2>
      <p className="hint">Drag & drop PDF files or pick from your folders. The app creates document records from file names.</p>

      <form onSubmit={handleSubmit} className="stack">
        <div className="field-grid">
          <label>
            Project code
            <input value={projectCode} onChange={(event) => setProjectCode(event.target.value)} required />
          </label>

          <label>
            Discipline
            <input value={discipline} onChange={(event) => setDiscipline(event.target.value)} required />
          </label>
        </div>

        <div
          className={`dropzone ${isDragging ? 'is-dragging' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              fileInputRef.current?.click();
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            multiple
            onChange={handleFileInput}
            hidden
          />
          <p className="dropzone-title">Drop PDF files here</p>
          <p className="hint">or click to browse folders</p>
        </div>

        {files.length ? (
          <div className="file-list-wrap">
            <div className="list-meta">
              <strong>{files.length}</strong> file(s) selected · <strong>{totalFileSizeLabel}</strong>
            </div>
            <ul className="file-list">
              {files.map((file, index) => (
                <li key={`${file.name}-${file.size}`}>
                  <span>{file.name}</span>
                  <button type="button" className="subtle-button" onClick={() => removeFile(index)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <button type="submit" disabled={isSubmitting || !files.length}>
          {isSubmitting ? 'Creating…' : 'Create document records'}
        </button>
      </form>

      {successMessage ? <p className="success">{successMessage}</p> : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
