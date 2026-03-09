import { useEffect, useMemo, useState } from 'react';
import { PdfjsRendererAdapter } from '@gitplant/viewer-pdfjs';

type Props = { bytes: Uint8Array | null; title: string; onPageCount?: (n: number) => void };

export function PdfViewer({ bytes, title, onPageCount }: Props) {
  const renderer = useMemo(() => new PdfjsRendererAdapter(), []);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [image, setImage] = useState<string>('');
  const [state, setState] = useState<'idle'|'loading'|'error'>('idle');

  useEffect(() => { void (async () => {
    if (!bytes) return;
    setState('loading');
    try {
      await renderer.openDocument(bytes);
      const count = await renderer.getPageCount();
      setPage(1); setPageCount(count); onPageCount?.(count);
      const render = await renderer.renderPage(1, { scale: zoom });
      setImage(render.imageDataUrl);
      setState('idle');
    } catch {
      setState('error');
    }
  })(); return () => { void renderer.closeDocument(); }; }, [bytes]);

  useEffect(() => { void (async () => {
    if (!bytes || state === 'error' || pageCount === 0) return;
    setState('loading');
    try {
      const render = await renderer.renderPage(page, { scale: zoom });
      setImage(render.imageDataUrl);
      setState('idle');
    } catch { setState('error'); }
  })(); }, [page, zoom]);

  if (!bytes) return <div>Select a PDF to view.</div>;
  if (state === 'error') return <div role="alert">Failed to render document.</div>;
  return <div>
    <h3>{title}</h3>
    <div>
      <button onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
      <span>{page}/{pageCount}</span>
      <button onClick={() => setPage((p) => Math.min(pageCount, p + 1))}>Next</button>
      <button onClick={() => setZoom((z) => z + 0.1)}>Zoom In</button>
      <button onClick={() => setZoom((z) => Math.max(0.2, z - 0.1))}>Zoom Out</button>
      <button onClick={() => setZoom(1)}>Fit Width</button>
    </div>
    {state === 'loading' ? <div>Loading...</div> : <img src={image} alt="pdf page" style={{ maxWidth: '100%' }} />}
    <div id="overlay-layer" />
  </div>;
}
