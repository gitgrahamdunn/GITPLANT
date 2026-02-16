import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  downloadDocumentPdf,
  pullDocumentForRevision,
  searchDocuments,
} from "../api";
import type { SearchDocument } from "../types";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";
import Skeleton from "./ui/Skeleton";

interface DocumentSearchPanelProps {
  token: string;
  refreshKey?: number;
  createdDocuments?: SearchDocument[];
}

type SortField = "document_number" | "title" | "status";

function mergeDocuments(
  primary: SearchDocument[],
  secondary: SearchDocument[],
): SearchDocument[] {
  const byId = new Map<number, SearchDocument>();
  [...secondary, ...primary].forEach((document) => {
    byId.set(document.id, document);
  });

  return Array.from(byId.values());
}

export default function DocumentSearchPanel({
  token,
  refreshKey = 0,
  createdDocuments = [],
}: DocumentSearchPanelProps): JSX.Element {
  const [query, setQuery] = useState("");
  const [documents, setDocuments] = useState<SearchDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [visibleCount, setVisibleCount] = useState(10);
  const [sortField, setSortField] = useState<SortField>("document_number");
  const [sortAscending, setSortAscending] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mergedDocuments = useMemo(
    () => mergeDocuments(documents, createdDocuments),
    [documents, createdDocuments],
  );

  const sortedDocuments = useMemo(() => {
    const sorted = [...mergedDocuments].sort((left, right) => {
      const leftValue = left[sortField].toLowerCase();
      const rightValue = right[sortField].toLowerCase();
      return sortAscending
        ? leftValue.localeCompare(rightValue)
        : rightValue.localeCompare(leftValue);
    });
    return sorted;
  }, [mergedDocuments, sortAscending, sortField]);

  const visibleDocuments = useMemo(
    () => sortedDocuments.slice(0, visibleCount),
    [sortedDocuments, visibleCount],
  );

  async function loadDocuments(searchTerm: string): Promise<void> {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchDocuments(token, searchTerm);
      setDocuments(result.items);
      setVisibleCount(10);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Failed to load documents",
      );
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

  async function handlePullForRevision(documentId: number): Promise<void> {
    setError(null);
    setActionMessage(null);

    try {
      const pulled = await pullDocumentForRevision(token, documentId);
      setActionMessage(pulled.message);
    } catch (actionError) {
      setError(
        actionError instanceof Error
          ? actionError.message
          : "Failed to pull document for revision",
      );
    }
  }

  async function openPdf(documentId: number): Promise<void> {
    setError(null);

    try {
      const fileBlob = await downloadDocumentPdf(token, documentId);
      const objectUrl = URL.createObjectURL(fileBlob);
      window.open(objectUrl, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(objectUrl), 120000);
    } catch (downloadError) {
      setError(
        downloadError instanceof Error
          ? downloadError.message
          : "Failed to open document PDF",
      );
    }
  }

  return (
    <Card title="Documents" subtitle="Search, sort, and review uploaded files.">
      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          className="input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by title or document number"
        />
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Searching…" : "Search"}
        </Button>
      </form>

      <div className="inline-form">
        <label className="field-label">
          <span>Sort by</span>
          <select
            value={sortField}
            onChange={(event) => setSortField(event.target.value as SortField)}
          >
            <option value="document_number">Document number</option>
            <option value="title">Title</option>
            <option value="status">Status</option>
          </select>
        </label>

        <Button
          type="button"
          variant="secondary"
          onClick={() => setSortAscending((value) => !value)}
        >
          {sortAscending ? "Ascending" : "Descending"}
        </Button>
      </div>

      <p className="hint">{sortedDocuments.length} document(s) available.</p>
      {actionMessage ? <Banner tone="success" message={actionMessage} /> : null}
      {error ? <Banner tone="error" message={error} /> : null}

      {isLoading ? <Skeleton lines={6} /> : null}

      {!isLoading && !sortedDocuments.length ? (
        <Banner
          tone="info"
          message="No documents found. Upload a PDF to get started."
        />
      ) : null}

      {!!sortedDocuments.length && (
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
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visibleDocuments.map((document) => (
                <tr key={document.id}>
                  <td>{document.id}</td>
                  <td>{document.document_number}</td>
                  <td>{document.title}</td>
                  <td>{document.discipline}</td>
                  <td>{document.status}</td>
                  <td>{document.current_revision}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className="subtle-button"
                        onClick={() => {
                          void handlePullForRevision(document.id);
                        }}
                      >
                        Pull for revision
                      </button>
                      <button
                        type="button"
                        className="subtle-button"
                        onClick={() => {
                          void openPdf(document.id);
                        }}
                      >
                        Open PDF
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {visibleCount < sortedDocuments.length ? (
        <Button
          type="button"
          variant="secondary"
          onClick={() => setVisibleCount((count) => count + 10)}
        >
          Load more
        </Button>
      ) : null}
    </Card>
  );
}
