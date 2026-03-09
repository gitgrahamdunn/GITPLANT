export interface PageText {
  pageNumber: number;
  text: string;
}

export interface TextExtractionProvider {
  extractPageText(revisionId: string): Promise<PageText[]>;
}
