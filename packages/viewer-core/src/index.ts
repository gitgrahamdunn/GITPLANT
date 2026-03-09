export interface RenderSpec {
  scale: number;
}

export interface DocumentMetadata {
  title?: string;
  pageCount: number;
}

export interface RenderResult {
  width: number;
  height: number;
  imageDataUrl: string;
}

export interface ViewerRenderer {
  openDocument(source: Uint8Array): Promise<void>;
  closeDocument(): Promise<void>;
  getDocumentMetadata(): Promise<DocumentMetadata>;
  getPageCount(): Promise<number>;
  renderPage(pageNumber: number, spec: RenderSpec): Promise<RenderResult>;
  getTextContent(pageNumber: number): Promise<string>;
  screenToPage(x: number, y: number): { x: number; y: number };
  pageToScreen(x: number, y: number): { x: number; y: number };
}
