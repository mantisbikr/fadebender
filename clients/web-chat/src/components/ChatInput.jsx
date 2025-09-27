/**
 * ChatInput Component
 * Handles user input with validation and submission
 */

import { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Container,
  InputAdornment
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as AIIcon
} from '@mui/icons-material';

export default function ChatInput({ onSubmit, onHelp, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    // Unified handler - the backend will determine if it's a command or help query
    onSubmit(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <Paper elevation={2} sx={{ borderTop: 1, borderColor: 'divider' }}>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            variant="outlined"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask questions or send commands: 'set track 1 volume to -6 dB' or 'how to sidechain in Ableton?'"
            disabled={disabled}
            autoComplete="off"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <AIIcon color="primary" />
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                pr: 1 // Reduce right padding to align better with button
              }
            }}
          />
          <IconButton
            type="submit"
            disabled={!input.trim() || disabled}
            color="primary"
            size="large"
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'grey.300',
                color: 'grey.500',
              },
              width: 48,
              height: 48,
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, px: 1, display: 'block' }}>
          💬 Send commands to control your DAW or ask questions about audio production • Press Enter to send
        </Typography>
      </Container>
    </Paper>
  );
}
