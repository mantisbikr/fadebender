/**
 * useDAWControl Hook
 * Business rules for DAW command processing
 */

import { useState, useCallback, useEffect } from 'react';
import { apiService } from '../services/api.js';
import { textProcessor } from '../utils/textProcessor.js';

export function useDAWControl() {
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [conversationContext, setConversationContext] = useState(null);
  const [modelPref, setModelPref] = useState('gemini-2.5-flash');
  const [confirmExecute, setConfirmExecute] = useState(true);
  const [historyState, setHistoryState] = useState({ undo_available: false, redo_available: false });

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }]);
  }, []);

  const processControlCommand = useCallback(async (rawInput) => {
    setIsProcessing(true);
    // New command resets any prior clarification state
    setConversationContext(null);

    try {
      // Step 1: Process and validate input
      const processed = textProcessor.processInput(rawInput);

      addMessage({
        type: 'user',
        content: rawInput,
        original: processed.original,
        processed: processed.processed,
        corrections: processed.corrections
      });

      if (!processed.validation.valid) {
        addMessage({
          type: 'error',
          content: `Invalid command: ${processed.validation.error}`
        });
        return;
      }

      // First: parse to canonical intent for clear UI preview
      let parsed;
      try {
        parsed = await apiService.parseIntent(processed.processed, modelPref, undefined);
      } catch (e) {
        addMessage({ type: 'error', content: `Intent parse error: ${e.message}` });
        return;
      }

      const rawIntent = parsed?.raw_intent || null;

      // If this looks like a help/conceptual query, route to /help and stop.
      if (rawIntent && (rawIntent.intent === 'question_response')) {
        try {
          const help = await apiService.getHelp(processed.processed);
          addMessage({ type: 'info', content: help.answer, data: help });
        } catch (e) {
          addMessage({ type: 'error', content: `Help error: ${e.message}` });
        }
        return;
      }

      // If clarification is needed, surface question and stop.
      if (rawIntent && rawIntent.intent === 'clarification_needed' && rawIntent.question) {
        setConversationContext(rawIntent.context || null);
        addMessage({ type: 'question', content: rawIntent.question, data: rawIntent });
        return;
      }

      // Hold canonical intent for details, but don't render a separate intent card.
      const canonicalIntent = (parsed && parsed.ok) ? parsed.intent : undefined;

      // Then: execute end-to-end via server /chat (NLP -> intent -> UDP)
      const result = await apiService.chat(processed.processed, confirmExecute, modelPref);

      // Prefer a clean, chat-like summary; only include details when there is an error
      if (!result.ok) {
        addMessage({
          type: 'info',
          content: result.summary || result.reason || 'Preview only',
          data: (result.answer || result.suggested_intents) ? result : undefined
        });
        if (result.intent && result.intent.intent === 'clarification_needed' && result.intent.question) {
          setConversationContext(result.intent.context || null);
          addMessage({ type: 'question', content: result.intent.question, data: result.intent });
        }
        return;
      }

      addMessage({
        type: 'success',
        content: result.summary || '✅ Executed',
        // Include canonical + raw intent for optional details view, but keep chat clean
        data: canonicalIntent ? { canonical_intent: canonicalIntent, raw_intent: rawIntent } : undefined
      });
      // Refresh history state after an executed command
      try { const hs = await apiService.getHistoryState(); setHistoryState(hs); } catch {}
      // Clear clarification banner on success
      setConversationContext(null);

    } catch (error) {
      addMessage({
        type: 'error',
        content: `❌ Error: ${error.message}`
      });
    } finally {
      setIsProcessing(false);
    }
  }, [addMessage, conversationContext]);

  const processHelpQuery = useCallback(async (query) => {
    setIsProcessing(true);

    try {
      addMessage({
        type: 'user',
        content: `❓ ${query}`
      });

      const response = await apiService.getHelp(query);
      addMessage({
        type: 'info',
        content: response.answer,
        data: response
      });

    } catch (error) {
      addMessage({
        type: 'error',
        content: `❌ Help error: ${error.message}`
      });
    } finally {
      setIsProcessing(false);
    }
  }, [addMessage]);

  const checkSystemHealth = useCallback(async () => {
    try {
      const health = await apiService.checkHealth();
      setSystemStatus(health);
    } catch (error) {
      setSystemStatus({ status: 'error' });
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const undoLast = useCallback(async () => {
    try {
      const res = await apiService.undoLast();
      if (res.ok) {
        addMessage({ type: 'success', content: 'Undid last change', data: res });
      } else {
        addMessage({ type: 'info', content: res.error || 'Nothing to undo', data: res });
      }
      try { const hs = await apiService.getHistoryState(); setHistoryState(hs); } catch {}
    } catch (e) {
      addMessage({ type: 'error', content: `Undo error: ${e.message}` });
    }
  }, [addMessage]);

  const redoLast = useCallback(async () => {
    try {
      const res = await apiService.redoLast();
      if (res.ok) {
        addMessage({ type: 'success', content: 'Redid last change', data: res });
      } else {
        addMessage({ type: 'info', content: res.error || 'Nothing to redo', data: res });
      }
      try { const hs = await apiService.getHistoryState(); setHistoryState(hs); } catch {}
    } catch (e) {
      addMessage({ type: 'error', content: `Redo error: ${e.message}` });
    }
  }, [addMessage]);

  // Initialize history state once
  useEffect(() => {
    (async () => {
      try { const hs = await apiService.getHistoryState(); setHistoryState(hs); } catch {}
    })();
  }, []);

  return {
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
  };
}
