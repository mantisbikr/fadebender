/**
 * Header Component
 * Main application header with logo, model selector, and system status
 */

import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Button,
  IconButton,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Clear as ClearIcon,
  Undo as UndoIcon,
  Redo as RedoIcon
} from '@mui/icons-material';
import SystemStatus from './SystemStatus.jsx';

function Header({
  modelPref,
  setModelPref,
  systemStatus,
  conversationContext,
  isProcessing,
  darkMode,
  setDarkMode,
  confirmExecute,
  setConfirmExecute,
  undoLast,
  redoLast,
  clearMessages,
  historyState
}) {
  return (
    <AppBar position="static" color="inherit" elevation={1}>
      <Toolbar sx={{ justifyContent: 'space-between', py: 2, minHeight: '80px' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', flex: 1 }}>
          <Box>
            <Typography variant="h5" fontWeight="bold" color="text.primary" sx={{ lineHeight: 1.1 }}>
              FADEBENDER
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: 'block', textAlign: 'right' }}>
              Bend your mix with AI
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={confirmExecute}
                onChange={(e) => setConfirmExecute(e.target.checked)}
                color="primary"
                disabled={isProcessing}
              />
            }
            label={confirmExecute ? 'Execute' : 'Preview only'}
          />

          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Model</InputLabel>
            <Select
              value={modelPref}
              onChange={(e) => setModelPref(e.target.value)}
              disabled={isProcessing}
              label="Model"
            >
              <MenuItem value="gemini-2.5-flash">Gemini Flash</MenuItem>
              <MenuItem value="llama">Llama 8B</MenuItem>
            </Select>
          </FormControl>

          <SystemStatus
            systemStatus={systemStatus}
            conversationContext={conversationContext}
          />

          <IconButton
            onClick={undoLast}
            color="inherit"
            title="Undo last change"
            disabled={!historyState?.undo_available}
          >
            <UndoIcon />
          </IconButton>

          <IconButton
            onClick={redoLast}
            color="inherit"
            title="Redo last change"
            disabled={!historyState?.redo_available}
          >
            <RedoIcon />
          </IconButton>

          <IconButton
            onClick={() => setDarkMode(!darkMode)}
            color="inherit"
            title="Toggle theme"
          >
            {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>

          <Button
            onClick={clearMessages}
            startIcon={<ClearIcon />}
            variant="outlined"
            size="small"
          >
            Clear Chat
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
