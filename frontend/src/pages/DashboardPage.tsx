/**
 * Dashboard Page
 *
 * Main landing page for authenticated users.
 * Displays household list and placeholder for todos (Task 5.5).
 */

import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Link,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listHouseholds, type Household } from '../api/households';
import { useAuthStore } from '../stores/authStore';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * DashboardPage - Main dashboard for logged-in users
 *
 * Shows household list and placeholder for todos (Task 5.5).
 */
export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [households, setHouseholds] = useState<Household[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHouseholds();
  }, []);

  const loadHouseholds = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listHouseholds();
      setHouseholds(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load households'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome, {user?.full_name || user?.email}!
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        This is your household management dashboard. Here you can manage
        households, expenses, chores, and to-do lists.
      </Typography>

      {/* Households Section */}
      <Card sx={{ mt: 4, mb: 4 }}>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6" component="h2">
              Your Households
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/households')}
            >
              View All Households
            </Button>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : error ? (
            <Typography color="error" paragraph>
              {error}
            </Typography>
          ) : households.length === 0 ? (
            <Typography variant="body2" color="text.secondary" paragraph>
              You don't have any households yet. Create one to get started!
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {households.slice(0, 5).map((household) => (
                <Box
                  key={household.id}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    py: 1,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Box>
                    <Typography variant="body1">{household.name}</Typography>
                    {household.description && (
                      <Typography variant="body2" color="text.secondary">
                        {household.description}
                      </Typography>
                    )}
                  </Box>
                  <Button
                    size="small"
                    onClick={() => navigate(`/households/${household.id}`)}
                  >
                    View
                  </Button>
                </Box>
              ))}
              {households.length > 5 && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  And {households.length - 5} more household
                  {households.length - 5 > 1 ? 's' : ''}...
                </Typography>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Todos Section - Placeholder for Task 5.5 */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6" component="h2">
              Recent To-Dos
            </Typography>
            <Link
              component="button"
              variant="body2"
              onClick={() => {
                // TODO: Navigate to todos page when Task 5.5 is implemented
                alert('To-do list coming soon!');
              }}
              sx={{ cursor: 'pointer' }}
            >
              View All Todos
            </Link>
          </Box>
          <Typography variant="body2" color="text.secondary">
            To-do list feature coming soon. This will show your first 5
            user-created or assigned todos.
          </Typography>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/households/new')}
        >
          Create Household
        </Button>
        <Button
          variant="outlined"
          onClick={() => {
            // TODO: Navigate to expenses page when implemented
            alert('Expense tracking coming soon!');
          }}
        >
          View Expenses
        </Button>
        <Button
          variant="outlined"
          onClick={() => {
            // TODO: Navigate to chores page when implemented
            alert('Chore management coming soon!');
          }}
        >
          View Chores
        </Button>
      </Box>
    </Box>
  );
};

