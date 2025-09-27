/**
 * WelcomeCard Component
 * Displays welcome message and examples when no messages are present
 */

import {
  Container,
  Paper,
  Box,
  Typography,
  Grid,
  Card,
  CardContent
} from '@mui/material';

function WelcomeCard() {
  return (
    <Container maxWidth="md" sx={{ textAlign: 'center', mt: 8 }}>
      <Paper elevation={2} sx={{ p: 6, borderRadius: 4 }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
            borderRadius: 4,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            mx: 'auto',
            mb: 3,
          }}
        >
          🎛️
        </Box>
        <Typography variant="h4" component="h2" gutterBottom fontWeight="bold">
          Welcome to Fadebender
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          Control your DAW with natural language commands and get expert help
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" color="primary.main" fontWeight="bold" gutterBottom>
                  🎚️ Volume Control
                </Typography>
                <Typography variant="body2" color="text.primary">
                  "set track 1 volume to -6 dB"
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" color="success.main" fontWeight="bold" gutterBottom>
                  🔄 Panning
                </Typography>
                <Typography variant="body2" color="text.primary">
                  "pan track 2 left by 20%"
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" color="secondary.main" fontWeight="bold" gutterBottom>
                  ❓ Get Help
                </Typography>
                <Typography variant="body2" color="text.primary">
                  "how to sidechain in Ableton?"
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
}

export default WelcomeCard;