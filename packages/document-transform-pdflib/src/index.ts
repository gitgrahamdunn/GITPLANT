import type { DocumentTransformEngine, TransformationRequest, TransformationResult } from '@gitplant/document-transform-core';

export class PdfLibTransformAdapter implements DocumentTransformEngine {
  async run(_request: TransformationRequest): Promise<TransformationResult> {
    throw new Error('Transformation adapter is implemented in Tauri Rust for desktop-managed storage.');
  }
}
