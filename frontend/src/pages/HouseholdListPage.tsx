/**
 * Household List Page
 *
 * Displays all households the user is a member of and provides
 * a button to create a new household.
 */

import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listHouseholds, type Household } from '../api/households';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * HouseholdListPage - Lists all user's households
 */
export const HouseholdListPage: React.FC = () => {
  const navigate = useNavigate();
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Households
        </Typography>
        <Typography color="error" paragraph>
          {error}
        </Typography>
        <Button variant="contained" onClick={loadHouseholds}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Typography variant="h4" component="h1">
          Households
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate('/households/new')}
        >
          Create Household
        </Button>
      </Box>

      {households.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              You don't have any households yet. Create one to get started!
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button
                variant="contained"
                onClick={() => navigate('/households/new')}
              >
                Create Your First Household
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {households.map((household) => (
            <Card
              key={household.id}
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/households/${household.id}`)}
            >
              <CardContent>
                <Typography variant="h6" component="h2" gutterBottom>
                  {household.name}
                </Typography>
                {household.description && (
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {household.description}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary">
                  Created {new Date(household.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
};

