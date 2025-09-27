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
import WelcomeCard from './components/WelcomeCard.jsx';
import LoadingIndicator from './components/LoadingIndicator.jsx';
import { useDAWControl } from './hooks/useDAWControl.js';
import { lightTheme, darkTheme } from './theme.js';

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const [darkMode, setDarkMode] = useState(prefersDarkMode);

  const {
    messages,
    isProcessing,
    systemStatus,
    conversationContext,
    modelPref,
    setModelPref,
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
          clearMessages={clearMessages}
        />

        {/* Messages */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
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

        {/* Input */}
        <ChatInput
          onSubmit={processControlCommand}
          onHelp={processHelpQuery}
          disabled={isProcessing}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
