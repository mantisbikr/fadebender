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
  Redo as RedoIcon,
  Menu as MenuIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import SystemStatus from './SystemStatus.jsx';
import { useState } from 'react';
import SettingsModal from './SettingsModal.jsx';

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
  historyState,
  onToggleSidebar
}) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  return (
    <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
      <Toolbar sx={{ justifyContent: 'space-between', py: 0.75, minHeight: '48px' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', flex: 1, gap: 1 }}>
          {/* Mobile menu button for sidebar */}
          <Box sx={{ display: { xs: 'block', md: 'none' } }}>
            <IconButton onClick={onToggleSidebar} color="inherit" title="Menu" size="small">
              <MenuIcon fontSize="small" />
            </IconButton>
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="bold" color="text.primary" sx={{ lineHeight: 1.1, fontSize: '1.1rem' }}>
              FADEBENDER
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: 'block', textAlign: 'right', fontSize: '0.65rem' }}>
              Bend your mix with AI
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* Moved Execute/Model/System to Settings modal */}

          <IconButton
            onClick={undoLast}
            color="inherit"
            title="Undo last change"
            disabled={!historyState?.undo_available}
            size="small"
          >
            <UndoIcon fontSize="small" />
          </IconButton>

          <IconButton
            onClick={redoLast}
            color="inherit"
            title="Redo last change"
            disabled={!historyState?.redo_available}
            size="small"
          >
            <RedoIcon fontSize="small" />
          </IconButton>

          <IconButton
            onClick={() => setDarkMode(!darkMode)}
            color="inherit"
            title="Toggle theme"
            size="small"
          >
            {darkMode ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
          </IconButton>

          <IconButton
            onClick={() => setSettingsOpen(true)}
            color="inherit"
            title="Settings"
            size="small"
          >
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Box>
      </Toolbar>
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        confirmExecute={confirmExecute}
        setConfirmExecute={setConfirmExecute}
        systemStatus={systemStatus}
      />
    </AppBar>
  );
}

export default Header;
