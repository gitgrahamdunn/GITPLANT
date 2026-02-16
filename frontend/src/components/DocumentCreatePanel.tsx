import {
  ChangeEvent,
  DragEvent,
  FormEvent,
  useMemo,
  useRef,
  useState,
} from "react";
import { uploadPdfDocuments } from "../api";
import type { SearchDocument } from "../types";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface DocumentCreatePanelProps {
  token: string;
  onCreated: (document: SearchDocument) => void;
}

function filterPdfFiles(fileList: FileList | File[]): File[] {
  return Array.from(fileList).filter(
    (file) =>
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf"),
  );
}

export default function DocumentCreatePanel({
  token,
  onCreated,
}: DocumentCreatePanelProps): JSX.Element {
  const [projectCode, setProjectCode] = useState("PRJ-1");
  const [discipline, setDiscipline] = useState("General");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const totalFileSizeLabel = useMemo(() => {
    const bytes = files.reduce((sum, file) => sum + file.size, 0);
    if (bytes < 1024 * 1024) {
      return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }, [files]);

  function addFiles(newFiles: File[]): void {
    if (!newFiles.length) {
      setError("Only PDF files are supported right now.");
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setFiles((existing) => {
      const incoming = newFiles.filter(
        (newFile) =>
          !existing.some(
            (currentFile) =>
              currentFile.name === newFile.name &&
              currentFile.size === newFile.size,
          ),
      );
      return [...existing, ...incoming];
    });
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>): void {
    if (!event.target.files) {
      return;
    }

    addFiles(filterPdfFiles(event.target.files));
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setIsDragging(false);
    addFiles(filterPdfFiles(event.dataTransfer.files));
  }

  function removeFile(targetIndex: number): void {
    setFiles((existing) =>
      existing.filter((_, index) => index !== targetIndex),
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!files.length) {
      setError("Please drop at least one PDF file or use the file picker.");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = new FormData();
      payload.append("project_code", projectCode);
      payload.append("discipline", discipline);
      files.forEach((file) => {
        payload.append("files", file, file.name);
      });

      const result = await uploadPdfDocuments(token, payload);
      result.items.forEach((document) => onCreated(document));
      setSuccessMessage(
        `Created ${result.total_created} document record(s) from PDF selection.`,
      );
      setFiles([]);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Failed to create documents from selected PDFs",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card
      title="Upload PDFs"
      subtitle="Create document records directly from selected PDF files."
    >
      <form onSubmit={handleSubmit} className="stack">
        <div className="field-grid">
          <label className="field-label">
            <span>Project code</span>
            <input
              className="input"
              value={projectCode}
              onChange={(e) => setProjectCode(e.target.value)}
              required
            />
          </label>

          <label className="field-label">
            <span>Discipline</span>
            <input
              className="input"
              value={discipline}
              onChange={(e) => setDiscipline(e.target.value)}
              required
            />
          </label>
        </div>

        <div
          className={`dropzone ${isDragging ? "is-dragging" : ""}`}
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
            if (event.key === "Enter" || event.key === " ") {
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
              <strong>{files.length}</strong> file(s) selected ·{" "}
              <strong>{totalFileSizeLabel}</strong>
            </div>
            <ul className="file-list">
              {files.map((file, index) => (
                <li key={`${file.name}-${file.size}`}>
                  <span>{file.name}</span>
                  <button
                    type="button"
                    className="subtle-button"
                    onClick={() => removeFile(index)}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <Button type="submit" disabled={isSubmitting || !files.length}>
          {isSubmitting ? "Creating…" : "Create document records"}
        </Button>
      </form>

      {successMessage ? (
        <Banner tone="success" message={successMessage} />
      ) : null}
      {error ? <Banner tone="error" message={error} /> : null}
    </Card>
  );
}
