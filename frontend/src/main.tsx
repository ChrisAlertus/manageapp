/**
 * Application Entry Point
 *
 * This is the first file that runs when the app loads.
 * It sets up React, applies the Material UI theme, and renders the App component.
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from './theme';
import './index.css';
import App from './App.tsx';

// Create the root and render the app
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* ThemeProvider makes the MUI theme available to all components */}
    <ThemeProvider theme={theme}>
      {/* CssBaseline provides consistent default styles */}
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
);
