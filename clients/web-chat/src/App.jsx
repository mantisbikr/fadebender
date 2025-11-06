/**
 * Main App Component
 * Orchestrates the chat interface
 */

import { useEffect, useState, useMemo } from 'react';
import {
  ThemeProvider,
  CssBaseline,
  Box,
  Container,
  IconButton,
  Tooltip,
  Fade
} from '@mui/material';
import { useMediaQuery } from '@mui/material';
import { Close as CloseIcon, Tune as TuneIcon } from '@mui/icons-material';
import ChatMessage from './components/ChatMessage.jsx';
import ChatInput from './components/ChatInput.jsx';
import Header from './components/Header.jsx';
import { Sidebar } from './components/Sidebar.jsx';
import { apiService } from './services/api.js';
import WelcomeCard from './components/WelcomeCard.jsx';
import LoadingIndicator from './components/LoadingIndicator.jsx';
import { useDAWControl } from './hooks/useDAWControl.js';
import { lightTheme, darkTheme } from './theme.js';
import TransportBar from './components/TransportBar.jsx';
import CapabilitiesDrawer from './components/CapabilitiesDrawer.jsx';

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const isDesktop = useMediaQuery('(min-width:900px)');
  const [darkMode, setDarkMode] = useState(prefersDarkMode);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(360);
  const [isResizing, setIsResizing] = useState(false);
  const [draftInput, setDraftInput] = useState(null);

  const {
    messages,
    isProcessing,
    systemStatus,
    conversationContext,
    modelPref,
    setModelPref,
    confirmExecute,
    setConfirmExecute,
    undoLast,
    redoLast,
    historyState,
    processControlCommand,
    processHelpQuery,
    checkSystemHealth,
    clearMessages,
    currentCapabilities,
    featureFlags,
    capabilitiesDrawerOpen,
    setCapabilitiesDrawerOpen
  } = useDAWControl();

  const theme = useMemo(
    () => darkMode ? darkTheme : lightTheme,
    [darkMode]
  );

  useEffect(() => {
    checkSystemHealth();
  }, [checkSystemHealth]);

  // Load app config once to configure sidebar width
  useEffect(() => {
    (async () => {
      try {
        const cfg = await apiService.getAppConfig();
        const ui = cfg?.ui || {};
        if (ui.sidebar_width_px) setSidebarWidth(Number(ui.sidebar_width_px));
      } catch {}
    })();
  }, []);

  // Resizer handlers
  useEffect(() => {
    if (!isResizing) return;
    const onMove = (e) => {
      const x = Math.max(240, Math.min(600, e.clientX || 360));
      setSidebarWidth(x);
    };
    const onUp = async () => {
      setIsResizing(false);
      // Persist width back to server config (best effort)
      try {
        await fetch(`${window.location.origin.replace('3000','8722')}/config/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ui: { sidebar_width_px: Math.round(sidebarWidth) } })
        });
      } catch {}
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp, { once: true });
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [isResizing, sidebarWidth]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Header
          modelPref={modelPref}
          setModelPref={setModelPref}
          systemStatus={systemStatus}
          conversationContext={conversationContext}
          isProcessing={isProcessing}
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          confirmExecute={confirmExecute}
          setConfirmExecute={setConfirmExecute}
          undoLast={undoLast}
          redoLast={redoLast}
          historyState={historyState}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          clearMessages={clearMessages}
        />

        {/* Transport controls - full width */}
        <TransportBar />

        {/* Content area: sidebar + main chat */}
        <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
          {/* Sidebar - temporary for small screens */}
          <Box sx={{ display: { xs: 'block', md: 'none' } }}>
            <Sidebar
              messages={messages}
              onReplay={(cmd) => processControlCommand(cmd)}
              variant="temporary"
              open={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
              onSetDraft={(cmd) => setDraftInput({ text: cmd, ts: Date.now() })}
              widthPx={sidebarWidth}
            />
          </Box>
          {/* Sidebar - permanent for desktop */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, height: '100%' }}>
            <Sidebar
              messages={messages}
              onReplay={(cmd) => processControlCommand(cmd)}
              variant="permanent"
              onSetDraft={(cmd) => setDraftInput({ text: cmd, ts: Date.now() })}
              widthPx={sidebarWidth}
            />
            {/* Resizer handle */}
            <Box
              onMouseDown={() => setIsResizing(true)}
              sx={{
                width: '6px',
                height: '100%',
                cursor: 'col-resize',
                backgroundColor: 'transparent',
                '&:hover': { backgroundColor: 'action.hover' }
              }}
            />
          </Box>

          {/* Main chat area */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <Box
              sx={{
                flex: 1,
                overflow: 'auto',
                p: 3,
                position: 'relative',
                // Add scroll padding to prevent content from scrolling under sticky elements
                scrollPaddingTop: '140px'
              }}
            >
              {/* Sticky Clear Chat Button - stays at top right */}
              {messages.length > 0 && (
                <Fade in={true}>
                  <Tooltip title="Clear Chat" arrow>
                    <IconButton
                      onClick={clearMessages}
                      size="small"
                      sx={{
                        position: 'sticky',
                        top: 16,
                        float: 'right',
                        marginBottom: '-40px',
                        bgcolor: 'background.paper',
                        boxShadow: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        zIndex: 10,
                        '&:hover': {
                          bgcolor: '#dc2626',
                          color: 'white',
                          borderColor: '#dc2626'
                        }
                      }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Fade>
              )}

              {/* Reopen Capabilities Drawer Button - shows when drawer is closed */}
              {!capabilitiesDrawerOpen && currentCapabilities && featureFlags?.sticky_capabilities_card && (
                <Fade in={true}>
                  <Tooltip title="Show Controls" arrow>
                    <IconButton
                      onClick={() => setCapabilitiesDrawerOpen(true)}
                      size="small"
                      sx={{
                        position: 'sticky',
                        top: 64,
                        float: 'right',
                        marginBottom: '-40px',
                        bgcolor: 'primary.main',
                        color: 'white',
                        boxShadow: 2,
                        border: '1px solid',
                        borderColor: 'primary.dark',
                        zIndex: 10,
                        '&:hover': {
                          bgcolor: 'primary.dark'
                        }
                      }}
                    >
                      <TuneIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Fade>
              )}
              {messages.length === 0 ? (
                <WelcomeCard />
              ) : (
                <Container maxWidth="lg" sx={{ position: 'relative' }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        message={message}
                        onSuggestedIntent={(intent) => processControlCommand(intent)}
                        showCapabilitiesInline={!featureFlags?.sticky_capabilities_card}
                      />
                    ))}
                  </Box>
                </Container>
              )}
              {isProcessing && <LoadingIndicator />}
            </Box>
            {/* Chat input aligned with chat pane width */}
            <Box>
              <ChatInput
                onSubmit={processControlCommand}
                onHelp={processHelpQuery}
                disabled={isProcessing}
                draft={draftInput}
                clearMessages={clearMessages}
              />
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Capabilities Drawer - only render when feature is enabled */}
      {featureFlags?.sticky_capabilities_card && (
        <CapabilitiesDrawer
          open={capabilitiesDrawerOpen}
          onClose={() => setCapabilitiesDrawerOpen(false)}
          capabilities={currentCapabilities}
        />
      )}
    </ThemeProvider>
  );
}

export default App;
