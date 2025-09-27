/**
 * LoadingIndicator Component
 * Shows processing state during requests
 */

import {
  Box,
  Paper,
  CircularProgress,
  Typography
} from '@mui/material';

function LoadingIndicator() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
      <Paper elevation={1} sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" fontWeight="medium">
          Processing your request...
        </Typography>
      </Paper>
    </Box>
  );
}

export default LoadingIndicator;