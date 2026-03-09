export interface RenderSpec {
  scale: number;
}

export interface DocumentMetadata {
  title?: string;
  pageCount: number;
}

export interface PageInfo {
  pageNumber: number;
  width: number;
  height: number;
}

export interface RenderResult {
  width: number;
  height: number;
  imageDataUrl: string;
}

export type LayerKind = 'base_pdf' | 'overlay_pdf' | 'markup_overlay' | 'selection_overlay';

export interface LayerVisibility {
  visible: boolean;
}

export interface LayerTransform {
  offsetX: number;
  offsetY: number;
  rotationDeg?: number;
}

export interface RenderLayer {
  id: string;
  kind: LayerKind;
  documentKey?: string;
  opacity: number;
  visibility: LayerVisibility;
  transform?: LayerTransform;
}

export interface ViewportState {
  scale: number;
  scrollX: number;
  scrollY: number;
}

export interface RenderScene {
  pageNumber: number;
  viewport: ViewportState;
  layers: RenderLayer[];
}

export interface PageRenderRequest {
  pageNumber: number;
  renderSpec: RenderSpec;
  scene: RenderScene;
}

export interface ViewerRenderer {
  openDocument(source: Uint8Array): Promise<void>;
  closeDocument(): Promise<void>;
  getDocumentMetadata(): Promise<DocumentMetadata>;
  getPageCount(): Promise<number>;
  getPageInfo(pageNumber: number): Promise<PageInfo>;
  renderPage(pageNumber: number, spec: RenderSpec): Promise<RenderResult>;
  renderLayer(layer: RenderLayer, pageNumber: number, spec: RenderSpec): Promise<RenderResult>;
  getTextContent(pageNumber: number): Promise<string>;
  screenToPage(x: number, y: number): { x: number; y: number };
  pageToScreen(x: number, y: number): { x: number; y: number };
}

export function createBaseRenderScene(pageNumber = 1, scale = 1): RenderScene {
  return {
    pageNumber,
    viewport: { scale, scrollX: 0, scrollY: 0 },
    layers: [
      {
        id: 'base',
        kind: 'base_pdf',
        opacity: 1,
        visibility: { visible: true },
        transform: { offsetX: 0, offsetY: 0 }
      }
    ]
  };
}

export function withOverlayPdfLayer(scene: RenderScene, overlayDocumentKey: string): RenderScene {
  return {
    ...scene,
    layers: [
      ...scene.layers,
      {
        id: 'overlay',
        kind: 'overlay_pdf',
        documentKey: overlayDocumentKey,
        opacity: 0.5,
        visibility: { visible: true },
        transform: { offsetX: 0, offsetY: 0 }
      }
    ]
  };
}
