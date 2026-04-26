import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { App } from './App';

test('renders the local EPF audit shell', () => {
  render(<App />);

  expect(screen.getByRole('heading', { name: /check salary slip pf/i })).toBeInTheDocument();
  expect(screen.getByText(/files stay on this device/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /add salary slip/i })).toBeInTheDocument();
  expect(screen.getByText(/confirmed mismatch/i)).toBeInTheDocument();
});
