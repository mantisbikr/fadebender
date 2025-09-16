/**
 * useDAWControl Hook
 * Business logic for DAW command processing
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

      // Step 2: Parse with AI (include conversation context and recent history)
      const recentMessages = messages.slice(-5).map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp
      }));

      const contextWithHistory = {
        ...conversationContext,
        recentHistory: recentMessages
      };

      const intent = await apiService.parseCommand(processed.processed, contextWithHistory);

      // Handle clarification needed
      if (intent.intent === 'clarification_needed') {
        setConversationContext(intent.context);
        addMessage({
          type: 'question',
          content: intent.question,
          data: intent
        });
        return;
      }

      // Handle question responses (no execution needed)
      if (intent.intent === 'question_response') {
        setConversationContext(null);
        addMessage({
          type: 'info',
          content: intent.answer,
          data: intent
        });
        return;
      }

      // Clear context after successful parsing
      setConversationContext(null);

      addMessage({
        type: 'info',
        content: `Parsed intent: ${intent.intent}`,
        data: intent
      });

      // Step 3: Execute through controller
      const result = await apiService.executeIntent(intent);

      addMessage({
        type: 'success',
        content: `✅ Command executed successfully`,
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