import { useMemo, useState } from "react";
import { uploadPlantRevision } from "../api";
import type { SearchDocument } from "../types";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface PlantUploadPanelProps {
  token: string;
  documents: SearchDocument[];
  onUploaded: (document: SearchDocument) => void;
}

export default function PlantUploadPanel({
  token,
  documents,
  onUploaded,
}: PlantUploadPanelProps): JSX.Element {
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sortedDocs = useMemo(
    () => [...documents].sort((a, b) => a.document_number.localeCompare(b.document_number)),
    [documents],
  );

  async function submit(): Promise<void> {
    if (!selectedDocumentId || !file) {
      setError("Select a Plant document and a PDF file.");
      return;
    }

    setError(null);
    const updated = await uploadPlantRevision(token, Number(selectedDocumentId), file);
    onUploaded(updated);
    setMessage(`Updated Plant current revision for ${updated.document_number}.`);
    setFile(null);
  }

  return (
    <Card
      title="Plant Upload"
      subtitle="Upload or replace Plant current revisions (separate from project working uploads)."
    >
      <div className="stack">
        <label className="field-label">
          <span>Plant document</span>
          <select
            value={selectedDocumentId}
            onChange={(event) => setSelectedDocumentId(event.target.value)}
          >
            <option value="">Select document</option>
            {sortedDocs.map((document) => (
              <option key={document.id} value={document.id}>
                {document.document_number} — rev {document.current_revision}
              </option>
            ))}
          </select>
        </label>

        <label className="field-label">
          <span>PDF file</span>
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        <div>
          <Button type="button" onClick={() => void submit()}>
            Upload to Plant
          </Button>
        </div>
      </div>

      {message ? <Banner tone="success" message={message} /> : null}
      {error ? <Banner tone="error" message={error} /> : null}
    </Card>
  );
}
