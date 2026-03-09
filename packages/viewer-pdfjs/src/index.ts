import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy } from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import type {
  DocumentMetadata,
  PageInfo,
  RenderLayer,
  RenderResult,
  RenderSpec,
  ViewerRenderer
} from '@gitplant/viewer-core';

GlobalWorkerOptions.workerSrc = pdfWorker;

export class PdfjsRendererAdapter implements ViewerRenderer {
  private document: PDFDocumentProxy | null = null;

  async openDocument(source: Uint8Array): Promise<void> {
    this.document = await getDocument({ data: source }).promise;
  }

  async closeDocument(): Promise<void> {
    if (this.document) {
      await this.document.destroy();
      this.document = null;
    }
  }

  async getDocumentMetadata(): Promise<DocumentMetadata> {
    const pageCount = await this.getPageCount();
    return { pageCount };
  }

  async getPageCount(): Promise<number> {
    if (!this.document) throw new Error('No document opened');
    return this.document.numPages;
  }

  async getPageInfo(pageNumber: number): Promise<PageInfo> {
    if (!this.document) throw new Error('No document opened');
    const page = await this.document.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1 });
    return { pageNumber, width: viewport.width, height: viewport.height };
  }

  async renderPage(pageNumber: number, spec: RenderSpec): Promise<RenderResult> {
    return this.renderBasePdfPage(pageNumber, spec);
  }

  async renderLayer(layer: RenderLayer, pageNumber: number, spec: RenderSpec): Promise<RenderResult> {
    if (layer.kind === 'base_pdf' || layer.kind === 'overlay_pdf') {
      return this.renderBasePdfPage(pageNumber, spec);
    }
    const page = await this.getPageInfo(pageNumber);
    const canvas = document.createElement('canvas');
    canvas.width = page.width;
    canvas.height = page.height;
    return {
      width: page.width,
      height: page.height,
      imageDataUrl: canvas.toDataURL('image/png')
    };
  }

  private async renderBasePdfPage(pageNumber: number, spec: RenderSpec): Promise<RenderResult> {
    if (!this.document) throw new Error('No document opened');
    const page = await this.document.getPage(pageNumber);
    const viewport = page.getViewport({ scale: spec.scale });
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Failed to initialize canvas context');
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await page.render({ canvasContext: context, viewport }).promise;
    return {
      width: viewport.width,
      height: viewport.height,
      imageDataUrl: canvas.toDataURL('image/png')
    };
  }

  async getTextContent(pageNumber: number): Promise<string> {
    if (!this.document) return '';
    const page = await this.document.getPage(pageNumber);
    const text = await page.getTextContent();
    return text.items.map((i: any) => i.str ?? '').join(' ');
  }

  screenToPage(x: number, y: number): { x: number; y: number } {
    return { x, y };
  }

  pageToScreen(x: number, y: number): { x: number; y: number } {
    return { x, y };
  }
}
