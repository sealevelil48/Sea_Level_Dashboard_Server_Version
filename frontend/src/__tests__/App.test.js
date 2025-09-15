import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

describe('App Component', () => {
  test('loads stations on mount', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/All Stations/i)).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    // Mock API failure
    global.fetch = jest.fn(() => Promise.reject(new Error('API Error')));
    
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});