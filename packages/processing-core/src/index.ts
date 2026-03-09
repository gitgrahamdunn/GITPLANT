import type { ProcessingJobStatus, ProcessingJobType } from '@gitplant/shared-types';

export interface ProcessingJobRequest {
  revisionId: string;
  jobType: ProcessingJobType;
  payload?: Record<string, unknown>;
}

export interface ProcessingProvider {
  supports(jobType: ProcessingJobType): boolean;
  run(jobId: string, request: ProcessingJobRequest): Promise<void>;
}

export interface OcrProvider {
  extractFromImagePdf(_revisionId: string): Promise<void>;
}

export interface ProcessingJobState {
  id: string;
  status: ProcessingJobStatus;
}
