import type { ViewerRenderer } from '@gitplant/viewer-core';
import { PdfjsRendererAdapter } from '@gitplant/viewer-pdfjs';

export function createViewerRenderer(): ViewerRenderer {
  return new PdfjsRendererAdapter();
}
