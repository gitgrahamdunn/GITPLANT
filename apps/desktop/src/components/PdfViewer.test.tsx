import { render, screen } from '@testing-library/react';
import { PdfViewer } from './PdfViewer';
import { createBaseRenderScene, withOverlayPdfLayer } from '@gitplant/viewer-core';
import fs from 'node:fs';
import path from 'node:path';

describe('PdfViewer states', () => {
  it('shows empty state', () => {
    render(<PdfViewer bytes={null} title="" />);
    expect(screen.getByText('Select a PDF to view.')).toBeInTheDocument();
  });

  it('supports base scene then optional overlay scene', () => {
    const base = createBaseRenderScene(1, 1);
    expect(base.layers).toHaveLength(1);
    expect(base.layers[0].kind).toBe('base_pdf');
    const compare = withOverlayPdfLayer(base, 'r2');
    expect(compare.layers).toHaveLength(2);
    expect(compare.layers[1].kind).toBe('overlay_pdf');
  });

  it('ui-level code avoids direct pdfjs imports', () => {
    const appSource = fs.readFileSync(path.resolve(__dirname, '../App.tsx'), 'utf8');
    expect(appSource).not.toContain('pdfjs-dist');
    expect(appSource).not.toContain('@gitplant/viewer-pdfjs');
  });
});
