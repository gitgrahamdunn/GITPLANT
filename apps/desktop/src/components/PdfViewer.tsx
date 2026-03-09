import { useEffect, useMemo, useState } from 'react';
import { createBaseRenderScene, withOverlayPdfLayer, type ViewerRenderer } from '@gitplant/viewer-core';

type Props = {
  bytes: Uint8Array | null;
  title: string;
  overlayBytes?: Uint8Array | null;
  onPageCount?: (n: number) => void;
  rendererFactory?: () => ViewerRenderer;
};

export function PdfViewer({ bytes, title, overlayBytes, onPageCount, rendererFactory }: Props) {
  const renderer = useMemo(() => (rendererFactory ? rendererFactory() : null), [rendererFactory]);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [image, setImage] = useState<string>('');
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [scene, setScene] = useState(() => createBaseRenderScene(1, 1));

  useEffect(() => {
    void (async () => {
      if (!bytes || !renderer) return;
      setState('loading');
      try {
        await renderer.openDocument(bytes);
        const count = await renderer.getPageCount();
        const initialScene = overlayBytes ? withOverlayPdfLayer(createBaseRenderScene(1, zoom), 'overlay') : createBaseRenderScene(1, zoom);
        setScene(initialScene);
        setPage(1);
        setPageCount(count);
        onPageCount?.(count);
        const render = await renderer.renderLayer(initialScene.layers[0], 1, { scale: zoom });
        setImage(render.imageDataUrl);
        setState('idle');
      } catch {
        setState('error');
      }
    })();
    return () => {
      if (renderer) void renderer.closeDocument();
    };
  }, [bytes, overlayBytes, renderer]);

  useEffect(() => {
    void (async () => {
      if (!bytes || !renderer || state === 'error' || pageCount === 0) return;
      setState('loading');
      try {
        const nextScene = {
          ...scene,
          pageNumber: page,
          viewport: { ...scene.viewport, scale: zoom }
        };
        setScene(nextScene);
        const render = await renderer.renderLayer(nextScene.layers[0], page, { scale: zoom });
        setImage(render.imageDataUrl);
        setState('idle');
      } catch {
        setState('error');
      }
    })();
  }, [page, zoom]);

  if (!bytes) return <div>Select a PDF to view.</div>;
  if (!renderer) return <div>Viewer renderer unavailable.</div>;
  if (state === 'error') return <div role="alert">Failed to render document.</div>;
  return (
    <div>
      <h3>{title}</h3>
      <div>
        <button onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
        <span>
          {page}/{pageCount}
        </span>
        <button onClick={() => setPage((p) => Math.min(pageCount, p + 1))}>Next</button>
        <button onClick={() => setZoom((z) => z + 0.1)}>Zoom In</button>
        <button onClick={() => setZoom((z) => Math.max(0.2, z - 0.1))}>Zoom Out</button>
        <button onClick={() => setZoom(1)}>Fit Width</button>
      </div>
      <div style={{ fontSize: 12, opacity: 0.7 }}>Scene layers: {scene.layers.map((l) => l.kind).join(', ')}</div>
      {state === 'loading' ? <div>Loading...</div> : <img src={image} alt="pdf page" style={{ maxWidth: '100%' }} />}
      <div id="overlay-layer" />
    </div>
  );
}
