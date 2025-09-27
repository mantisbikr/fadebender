/**
 * useDAWControl Hook
 * Business rules for DAW command processing
 */

import { useState, useCallback } from 'react';
import { apiService } from '../services/api.js';
import { textProcessor } from '../utils/textProcessor.js';

export function useDAWControl() {
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [conversationContext, setConversationContext] = useState(null);

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }]);
  }, []);

  const processControlCommand = useCallback(async (rawInput) => {
    setIsProcessing(true);

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

      // Execute end-to-end via server /chat (handles NLP -> intent -> UDP)
      const result = await apiService.chat(processed.processed, true);

      // Handle preview-only or unsupported intents
      if (!result.ok) {
        addMessage({
          type: 'info',
          content: `ℹ️ ${result.reason || 'Preview only'}`,
          data: result
        });
        // If server provided a question, surface it
        if (result.intent && result.intent.intent === 'clarification_needed' && result.intent.question) {
          setConversationContext(result.intent.context || null);
          addMessage({ type: 'question', content: result.intent.question, data: result.intent });
        }
        return;
      }

      addMessage({
        type: 'success',
        content: `✅ Executed`,
        data: result
      });

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
        content: response.answer
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

      addMessage({
        type: 'info',
        content: `System status: ${health.status} | AI: ${health.ai_parser_available ? '✅' : '❌'}`
      });
    } catch (error) {
      setSystemStatus({ status: 'error' });
      addMessage({
        type: 'error',
        content: '❌ Cannot connect to services'
      });
    }
  }, [addMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isProcessing,
    systemStatus,
    conversationContext,
    processControlCommand,
    processHelpQuery,
    checkSystemHealth,
    clearMessages
  };
}
