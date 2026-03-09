import { render, screen } from '@testing-library/react';
import { PdfViewer } from './PdfViewer';

describe('PdfViewer states', () => {
  it('shows empty state', () => {
    render(<PdfViewer bytes={null} title="" />);
    expect(screen.getByText('Select a PDF to view.')).toBeInTheDocument();
  });
});
