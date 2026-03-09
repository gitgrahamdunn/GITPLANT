import { useEffect, useState } from 'react';
import { tauriGateway } from './lib/tauriGateway';
import { PdfViewer } from './components/PdfViewer';
import { ErrorBoundary } from './components/ErrorBoundary';
import type { RecentDocumentView } from '@gitplant/shared-types';

export function App() {
  const [recent, setRecent] = useState<RecentDocumentView[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [bytes, setBytes] = useState<Uint8Array | null>(null);
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');

  const refreshRecent = async () => setRecent(await tauriGateway.listRecentDocuments());
  useEffect(() => { void refreshRecent(); }, []);

  const openDocument = async (documentId: string) => {
    const data = await tauriGateway.openDocument(documentId);
    const raw = await tauriGateway.readDocumentBytes(documentId);
    setCurrentId(documentId);
    setTitle(data.title);
    setBytes(new Uint8Array(raw));
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

  return <ErrorBoundary><div>
    <header><h1>Gitplant Desktop</h1><button onClick={importPdf}>Import PDF</button></header>
    {error && <div role="alert">{error}</div>}
    <aside>
      <h2>Recent Documents</h2>
      {recent.length === 0 ? <div>No recent documents.</div> : recent.map((r) => (
        <button key={r.documentId} onClick={() => void openDocument(r.documentId)}>{r.title}</button>
      ))}
    </aside>
    <main><PdfViewer bytes={bytes} title={title} onPageCount={(n) => { if (currentId) void tauriGateway.updatePageCount(currentId, n); }} /></main>
  </div></ErrorBoundary>;
}
