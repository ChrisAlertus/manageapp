/**
 * Material UI Theme Configuration
 *
 * This file sets up the default theme for Material UI components.
 * You can customize colors, typography, spacing, etc. here.
 */

import { createTheme } from '@mui/material/styles';

/**
 * Create the MUI theme
 * This theme will be used by all MUI components throughout the app
 */
export const theme = createTheme({
  palette: {
    primary: {
      main: '#9c27b0', // Purple
    },
    secondary: {
      main: '#1976d2', // Blue
    },
    background: {
      default: '#f5f5f5', // Light gray background
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  // You can add more customizations here as needed
});




