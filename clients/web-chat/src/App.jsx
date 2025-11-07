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
  Fade,
  Drawer,
  ClickAwayListener
} from '@mui/material';
import { useMediaQuery } from '@mui/material';
import { Close as CloseIcon, Tune as TuneIcon, PushPin as PushPinIcon, PushPinOutlined as PushPinOutlinedIcon } from '@mui/icons-material';
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
  const [leftDrawerOpen, setLeftDrawerOpen] = useState(true);
  const [leftDrawerPinned, setLeftDrawerPinned] = useState(true);

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
    setCapabilitiesDrawerOpen,
    capabilitiesDrawerPinned,
    setCapabilitiesDrawerPinned,
    typoCorrections
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

  // Resizer handlers (desktop only)
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

  // Close left drawer on outside click when not pinned (desktop only)
  const handleLeftClickAway = (event) => {
    if (!leftDrawerOpen) return;
    if (leftDrawerPinned) return;
    // Ignore clicks on resizer to avoid accidental close while resizing
    const resizer = document.querySelector('#left-resizer');
    const path = event.composedPath ? event.composedPath() : [];
    if (resizer && (path.includes(resizer) || (event.target && (resizer === event.target || resizer.contains(event.target))))) return;
    setLeftDrawerOpen(false);
  };

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
          {/* Sidebar - persistent drawer for desktop */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, height: '100%' }}>
            <ClickAwayListener onClickAway={handleLeftClickAway} mouseEvent="onMouseDown" touchEvent="onTouchStart">
              <Box sx={{ display: 'flex', height: '100%' }}>
                {leftDrawerOpen && (
                  <Drawer
                    anchor="left"
                    variant="persistent"
                    open={leftDrawerOpen}
                    hideBackdrop
                    ModalProps={{ keepMounted: true, disableEnforceFocus: true }}
                    PaperProps={{ sx: { width: sidebarWidth, boxSizing: 'border-box', position: 'relative' } }}
                  >
                    {/* Inline controls (pin/close) overlay */}
                    <Box sx={{ position: 'absolute', top: 8, right: 8, zIndex: 2, display: 'flex', gap: 0.5 }}>
                      <Tooltip title={leftDrawerPinned ? 'Unpin' : 'Pin'}>
                        <IconButton size="small" onClick={() => setLeftDrawerPinned(v => !v)}>
                          {leftDrawerPinned ? <PushPinIcon fontSize="small" /> : <PushPinOutlinedIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Close">
                        <IconButton size="small" onClick={() => setLeftDrawerOpen(false)}>
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Sidebar
                      messages={messages}
                      onReplay={(cmd) => processControlCommand(cmd)}
                      variant="permanent"
                      onSetDraft={(cmd) => setDraftInput({ text: cmd, ts: Date.now() })}
                      widthPx={sidebarWidth}
                    />
                  </Drawer>
                )}
                {/* Resizer handle (only when open) */}
                {leftDrawerOpen && (
                  <Box
                    id="left-resizer"
                    onMouseDown={() => setIsResizing(true)}
                    sx={{
                      width: '6px',
                      height: '100%',
                      cursor: 'col-resize',
                      backgroundColor: 'transparent',
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  />
                )}
                {/* Collapsed opener: compact vertical tab with grip lines */}
                {!leftDrawerOpen && (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center' }}>
                    <Box
                      onClick={() => setLeftDrawerOpen(true)}
                      title="Open Mixer Controls"
                      sx={{
                        width: 32,
                        height: 120,
                        backgroundColor: 'background.paper',
                        borderRight: 1,
                        borderTop: 1,
                        borderBottom: 1,
                        borderColor: 'divider',
                        borderTopRightRadius: 8,
                        borderBottomRightRadius: 8,
                        boxShadow: 1,
                        cursor: 'pointer',
                        userSelect: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        position: 'relative',
                        '&:hover': (theme) => ({ backgroundColor: theme.palette.action.hover })
                      }}
                    >
                      {/* Vertical label */}
                      <Box sx={{
                        transform: 'rotate(-90deg)',
                        whiteSpace: 'nowrap',
                        fontSize: '11px',
                        letterSpacing: '0.06em',
                        color: 'text.secondary'
                      }}>
                        Mixer Controls
                      </Box>
                      {/* Grip with vertical lines (theme-aware, beveled for depth) */}
                      <Box sx={(theme) => {
                        const isDark = theme.palette.mode === 'dark';
                        if (isDark) {
                          const colorA = 'rgba(255,255,255,0.60)';
                          const colorB = 'rgba(0,0,0,0.40)';
                          return {
                            position: 'absolute',
                            right: 3,
                            top: 10,
                            bottom: 10,
                            width: 6,
                            borderRadius: 1,
                            backgroundImage: `repeating-linear-gradient(90deg, ${colorA} 0, ${colorA} 1px, transparent 1px, transparent 3px), repeating-linear-gradient(90deg, transparent 0, transparent 1px, ${colorB} 1px, ${colorB} 2px, transparent 2px, transparent 3px)`,
                            backgroundSize: '3px 100%, 3px 100%',
                            backgroundPosition: '0 0, 1px 0',
                            boxShadow: 'inset 0 0 5px rgba(0,0,0,0.28)'
                          };
                        }
                        // Light mode: softer single-layer lines with gentle inset shadow
                        return {
                          position: 'absolute',
                          right: 3,
                          top: 10,
                          bottom: 10,
                          width: 6,
                          borderRadius: 1,
                          backgroundImage: 'repeating-linear-gradient(90deg, rgba(0,0,0,0.22) 0, rgba(0,0,0,0.22) 1px, transparent 1px, transparent 3px)',
                          boxShadow: 'inset 0 0 4px rgba(0,0,0,0.08)'
                        };
                      }} />
                    </Box>
                  </Box>
                )}
              </Box>
            </ClickAwayListener>
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
                typoCorrections={typoCorrections}
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
          pinned={capabilitiesDrawerPinned}
          onPinnedChange={setCapabilitiesDrawerPinned}
          initialGroup={drawerInit?.group}
          initialParam={drawerInit?.param}
          ignoreCloseSelectors={[ '#chat-input-root' ]}
        />
      )}
    </ThemeProvider>
  );
}

export default App;
