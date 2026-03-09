import { useEffect, useState } from 'react';
import { tauriGateway } from './lib/tauriGateway';
import { PdfViewer } from './components/PdfViewer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { createViewerRenderer } from './lib/viewerRenderer';
import type { ExtractedPageTextRecord, RecentDocumentView } from '@gitplant/shared-types';

export function App() {
  const [recent, setRecent] = useState<RecentDocumentView[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [currentRevisionId, setCurrentRevisionId] = useState<string | null>(null);
  const [bytes, setBytes] = useState<Uint8Array | null>(null);
  const [overlayBytes, setOverlayBytes] = useState<Uint8Array | null>(null);
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [extractedText, setExtractedText] = useState<ExtractedPageTextRecord[]>([]);

  const refreshRecent = async () => setRecent(await tauriGateway.listRecentDocuments());
  useEffect(() => {
    void refreshRecent();
  }, []);

  const openDocument = async (documentId: string) => {
    const data = await tauriGateway.openDocument(documentId);
    const raw = await tauriGateway.readDocumentBytes(documentId, data.revisionId);
    setCurrentId(documentId);
    setCurrentRevisionId(data.revisionId);
    setTitle(data.title);
    setBytes(new Uint8Array(raw));
    setOverlayBytes(null);
    setExtractedText([]);
    await refreshRecent();
  };

  const importPdf = async () => {
    setError('');
    try {
      const imported = await tauriGateway.importPdfFromPicker();
      await openDocument(imported.documentId);
    } catch (e) {
      setError((e as Error).message || 'Import failure');
    }
  };

  const runTextExtraction = async () => {
    if (!currentRevisionId) return;
    await tauriGateway.triggerTextExtraction(currentRevisionId);
    const rows = await tauriGateway.listExtractedPageText(currentRevisionId);
    setExtractedText(rows);
  };

  const runExtractProof = async () => {
    if (!currentRevisionId || !currentId) return;
    const derived = await tauriGateway.extractPagesToDerivedRevision(currentRevisionId, 1, 1);
    const base = await tauriGateway.readDocumentBytes(currentId, derived.sourceRevisionId);
    const overlay = await tauriGateway.readDocumentBytes(currentId, derived.derivedRevisionId);
    setBytes(new Uint8Array(base));
    setOverlayBytes(new Uint8Array(overlay));
    setCurrentRevisionId(derived.derivedRevisionId);
    await refreshRecent();
  };

  return (
    <ErrorBoundary>
      <div>
        <header>
          <h1>Gitplant Desktop</h1>
          <button onClick={importPdf}>Import PDF</button>
        </header>
        {error && <div role="alert">{error}</div>}
        <aside>
          <h2>Recent Documents</h2>
          {recent.length === 0 ? (
            <div>No recent documents.</div>
          ) : (
            recent.map((r) => (
              <button key={r.documentId} onClick={() => void openDocument(r.documentId)}>
                {r.title}
              </button>
            ))
          )}
        </aside>
        <section>
          <h2>Dev scaffolding</h2>
          <button onClick={() => void runTextExtraction()} disabled={!currentRevisionId}>Trigger text extraction</button>
          <button onClick={() => void runExtractProof()} disabled={!currentRevisionId}>Extract page 1 to derived revision</button>
          <div>Extracted page text rows: {extractedText.length}</div>
        </section>
        <main>
          <PdfViewer
            bytes={bytes}
            overlayBytes={overlayBytes}
            title={title}
            rendererFactory={createViewerRenderer}
            onPageCount={(n) => {
              if (currentRevisionId) void tauriGateway.updatePageCount(currentRevisionId, n);
            }}
          />
        </main>
      </div>
    </ErrorBoundary>
  );
}
