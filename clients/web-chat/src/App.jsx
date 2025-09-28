/**
 * Main App Component
 * Orchestrates the chat interface
 */

import { useEffect, useState, useMemo } from 'react';
import {
  ThemeProvider,
  CssBaseline,
  Box,
  Container
} from '@mui/material';
import { useMediaQuery } from '@mui/material';
import ChatMessage from './components/ChatMessage.jsx';
import ChatInput from './components/ChatInput.jsx';
import Header from './components/Header.jsx';
import { Sidebar, SIDEBAR_WIDTH } from './components/Sidebar.jsx';
import WelcomeCard from './components/WelcomeCard.jsx';
import LoadingIndicator from './components/LoadingIndicator.jsx';
import { useDAWControl } from './hooks/useDAWControl.js';
import { lightTheme, darkTheme } from './theme.js';

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const isDesktop = useMediaQuery('(min-width:900px)');
  const [darkMode, setDarkMode] = useState(prefersDarkMode);
  const [sidebarOpen, setSidebarOpen] = useState(false);
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
    clearMessages
  } = useDAWControl();

  const theme = useMemo(
    () => darkMode ? darkTheme : lightTheme,
    [darkMode]
  );

  useEffect(() => {
    checkSystemHealth();
  }, [checkSystemHealth]);

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

        {/* Content area: sidebar + main chat */}
        <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
          {/* Sidebar */}
          <Box sx={{ display: { xs: 'block', md: 'none' } }}>
            <Sidebar
              messages={messages}
              onReplay={(cmd) => processControlCommand(cmd)}
              variant="temporary"
              open={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
              onSetDraft={(cmd) => setDraftInput({ text: cmd, ts: Date.now() })}
            />
          </Box>
          <Box sx={{ display: { xs: 'none', md: 'block' } }}>
            <Sidebar
              messages={messages}
              onReplay={(cmd) => processControlCommand(cmd)}
              variant="permanent"
              onSetDraft={(cmd) => setDraftInput({ text: cmd, ts: Date.now() })}
            />
          </Box>

          {/* Main chat area */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 3, ml: { xs: 0, md: `${SIDEBAR_WIDTH}px` } }}>
          {messages.length === 0 ? (
            <WelcomeCard />
          ) : (
            <Container maxWidth="lg">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    onSuggestedIntent={(intent) => processControlCommand(intent)}
                  />
                ))}
              </Box>
            </Container>
          )}

          {isProcessing && <LoadingIndicator />}
          </Box>
        </Box>

        {/* Input: offset for sidebar so it doesn't sit underneath */}
        <Box sx={{ ml: { xs: 0, md: `${SIDEBAR_WIDTH}px` } }}>
          <ChatInput
            onSubmit={processControlCommand}
            onHelp={processHelpQuery}
            disabled={isProcessing}
            draft={draftInput}
          />
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
