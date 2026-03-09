import { render, screen } from '@testing-library/react';
import { App } from './App';
import { vi } from 'vitest';

vi.mock('./lib/tauriGateway', () => ({
  tauriGateway: {
    listRecentDocuments: vi.fn().mockResolvedValue([]),
    importPdfFromPicker: vi.fn(),
    openDocument: vi.fn(),
    readDocumentBytes: vi.fn(),
    updatePageCount: vi.fn()
  }
}));

describe('App smoke', () => {
  it('shows boot state and empty recent list', async () => {
    render(<App />);
    expect(screen.getByText('Gitplant Desktop')).toBeInTheDocument();
    expect(await screen.findByText('No recent documents.')).toBeInTheDocument();
  });
});
