/**
 * Create Household Page
 *
 * Form for creating a new household with name and description.
 */

import {
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createHousehold, type HouseholdCreate } from '../api/households';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * CreateHouseholdPage - Form to create a new household
 */
export const CreateHouseholdPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<HouseholdCreate>({
    name: '',
    description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    setNameError(null);

    if (!formData.name.trim()) {
      setNameError('Name is required');
      return false;
    }

    if (formData.name.length > 255) {
      setNameError('Name must be 255 characters or less');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const household = await createHousehold({
        name: formData.name.trim(),
        description: formData.description?.trim() || undefined,
      });

      navigate(`/households/${household.id}`);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to create household'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Create Household
      </Typography>

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="Household Name"
          value={formData.name}
          onChange={(e) =>
            setFormData({ ...formData, name: e.target.value })
          }
          error={!!nameError}
          helperText={nameError}
          required
          disabled={loading}
          sx={{ mb: 2 }}
          inputProps={{ maxLength: 255 }}
        />

        <TextField
          fullWidth
          label="Description"
          value={formData.description}
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
          multiline
          rows={4}
          disabled={loading}
          sx={{ mb: 2 }}
        />

        {error && (
          <Typography color="error" paragraph>
            {error}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/households')}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Creating...' : 'Create Household'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

