/**
 * Dashboard Page
 *
 * Main landing page for authenticated users.
 * This is a placeholder that will be expanded with household management features.
 */

import { Box, Button, Card, CardContent, Typography } from '@mui/material';
import { useAuthStore } from '../stores/authStore';

/**
 * DashboardPage - Main dashboard for logged-in users
 *
 * Currently shows a welcome message and placeholders for future features.
 */
export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome, {user?.full_name || user?.email}!
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        This is your household management dashboard. Here you'll be able to manage
        households, expenses, chores, and to-do lists.
      </Typography>

      <Box sx={{ mt: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Card sx={{ minWidth: 275 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Households
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Manage your households and members.
            </Typography>
            <Button
              variant="contained"
              onClick={() => {
                // TODO: Navigate to households page when implemented
                alert('Household management coming soon!');
              }}
            >
              View Households
            </Button>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 275 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Expenses
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Track and split expenses with your household.
            </Typography>
            <Button
              variant="contained"
              onClick={() => {
                // TODO: Navigate to expenses page when implemented
                alert('Expense tracking coming soon!');
              }}
            >
              View Expenses
            </Button>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 275 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Chores
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Schedule and track household chores.
            </Typography>
            <Button
              variant="contained"
              onClick={() => {
                // TODO: Navigate to chores page when implemented
                alert('Chore management coming soon!');
              }}
            >
              View Chores
            </Button>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 275 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              To-Do Lists
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Create and manage shared to-do lists.
            </Typography>
            <Button
              variant="contained"
              onClick={() => {
                // TODO: Navigate to todos page when implemented
                alert('To-do lists coming soon!');
              }}
            >
              View To-Dos
            </Button>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

