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
  const [featureFlags, setFeatureFlags] = useState({ use_intents_for_chat: false });
  const [liveSnapshot, setLiveSnapshot] = useState(null);

  // Load feature flags once
  useEffect(() => {
    (async () => {
      try {
        console.log('Loading app config...');
        const cfg = await apiService.getAppConfig();
        console.log('App config loaded:', cfg);
        console.log('cfg.features:', cfg.features);
        console.log('cfg.features exists?', !!cfg.features);
        const feats = (cfg && cfg.features) ? cfg.features : {};
        console.log('Feature flags extracted:', feats);
        setFeatureFlags(prev => {
          const merged = { ...prev, ...feats };
          console.log('setFeatureFlags merging prev:', prev, 'with feats:', feats, '= result:', merged);
          return merged;
        });
      } catch (e) {
        console.error('Failed to load app config:', e);
      }
    })();
  }, []);

  // Load snapshot for inline suggestions (best-effort)
  useEffect(() => {
    (async () => {
      try {
        const snap = await apiService.getSnapshot();
        setLiveSnapshot(snap);
      } catch {}
    })();
  }, []);

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
      // Fast path: internal param read directive from UI
      if (rawInput && rawInput.startsWith('__READ_PARAM__|')) {
        try {
          const parts = rawInput.split('|');
          const letter = parts[1];
          const deviceIdx = Number(parts[2]);
          const paramName = parts[3];
          const deviceName = parts[4] || null; // Get device name if available
          const result = await apiService.readIntent({
            domain: 'device',
            return_ref: letter,
            device_index: deviceIdx,
            param_ref: paramName
          });
          const makeDV = (r) => {
            const disp = r?.display_value;
            const unit = r?.unit;
            if (disp != null && disp !== '') return unit ? `${disp} ${unit}`.trim() : String(disp);
            if (r?.normalized_value != null) return String(r.normalized_value);
            return '';
          };
          const dv = makeDV(result);

          // Build min/max display range info
          let rangeInfo = '';
          if (result.min_display && result.max_display) {
            rangeInfo = ` Range: ${result.min_display} to ${result.max_display}.`;
          }

          // Build answer with sonic context if available
          let answer = `${paramName} is currently set to ${dv}.${rangeInfo}`;

          // Add audio knowledge context if available
          if (result.audio_knowledge) {
            const audioFunc = result.audio_knowledge.audio_function;
            if (audioFunc) {
              answer += ` ${audioFunc}`;
            }
          }

          // Generate better suggested intents based on parameter type and metadata
          let suggested_intents = [];

          // Build device reference - use device name if available
          // The intent parser expects device name (e.g., "reverb"), not "device 0"
          const deviceRef = deviceName || null;

          // Only generate suggestions if we have device name (otherwise commands won't work)
          if (!deviceRef) {
            suggested_intents = [];
          }

          // If parameter has label_map (discrete values like "Low/Med/High"), use those
          else if (deviceRef && result.has_label_map && result.label_map) {
            const labels = Object.keys(result.label_map);
            // Use up to 3 labels for suggestions
            suggested_intents = labels.slice(0, 3).map(label =>
              `set Return ${letter} ${deviceRef} ${paramName} to ${label}`
            );
          }
          // If we have typical values from audio knowledge, use those
          else if (deviceRef && result.audio_knowledge && result.audio_knowledge.typical_values) {
            const typicalValues = result.audio_knowledge.typical_values;
            // Use up to 3 typical values for suggestions
            suggested_intents = Object.entries(typicalValues)
              .slice(0, 3)
              .map(([_, value]) => {
                // Parse the value - it might be a range like "10-30" or single value like "50"
                // Extract just the numeric part(s)
                const numMatch = String(value).match(/^(\d+(?:\.\d+)?)/);
                if (!numMatch) return null;

                const numericValue = numMatch[1];
                const unit = result.unit || '';

                // Format: "set Return A reverb Decay Time to <value> <unit>" (clean, executable command)
                return `set Return ${letter} ${deviceRef} ${paramName} to ${numericValue} ${unit}`.trim();
              })
              .filter(Boolean); // Remove any null entries
          }
          // For continuous parameters with min/max, suggest low/mid/high based on range
          else if (deviceRef && result.min !== undefined && result.max !== undefined && result.unit) {
            const min = result.min;
            const max = result.max;
            const mid = (min + max) / 2;
            const unit = result.unit;
            // Format numbers to max 2 decimal places, remove trailing zeros
            const formatNum = (n) => {
              const rounded = Math.round(n * 100) / 100;
              return rounded % 1 === 0 ? rounded.toString() : rounded.toFixed(2).replace(/\.?0+$/, '');
            };
            suggested_intents = [
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(min)} ${unit}`,
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(mid)} ${unit}`,
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(max)} ${unit}`
            ];
          }
          // No fallback - only suggest commands if we have proper metadata

          // Also attach a single-param editor inside this info card
          try {
            const caps = await apiService.getReturnDeviceCapabilities(letter.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0), deviceIdx);
            const params = [];
            (caps?.data?.groups || []).forEach(g => (g.params || []).forEach(p => params.push(p)));
            (caps?.data?.ungrouped || []).forEach(p => params.push(p));
            const pmeta = params.find(p => String(p.name).toLowerCase() === String(paramName).toLowerCase()) || { name: paramName };
            const editor = {
              return_index: caps?.data?.return_index,
              return_letter: letter,
              device_index: deviceIdx,
              device_name: caps?.data?.device_name || deviceName || '',
              title: `${paramName} • Return ${letter} ${caps?.data?.device_name || ''}`,
              param: pmeta,
              current: { value: result.normalized_value, display_value: result.display_value },
              suggested: suggested_intents,
            };
            addMessage({ type: 'info', content: `Edit ${paramName}`, data: { answer, suggested_intents, param_editor: editor } });
          } catch {
            addMessage({ type: 'info', content: answer, data: { answer, suggested_intents } });
          }
        } catch (e) {
          addMessage({ type: 'error', content: `Read error: ${e.message}` });
        } finally {
          setIsProcessing(false);
        }
        return;
      }

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
          const help = await apiService.getHelp(processed.processed, conversationContext);
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

      console.log('DEBUG:', {
        use_intents_for_chat: featureFlags.use_intents_for_chat,
        parsed_ok: parsed?.ok,
        has_intent: !!parsed?.intent,
        confirmExecute,
        featureFlags,
        intent: parsed?.intent
      });

      let result;
      let deviceCapabilities = null; // Store capabilities to include in success message
      if (featureFlags.use_intents_for_chat && (parsed && parsed.ok) && parsed.intent) {
        // Execute canonical intent directly; on error surface message and stop
        try {
          result = await apiService.executeCanonicalIntent(parsed.intent);
          // Update conversational focus for follow-ups (e.g., device questions)
          try {
            const ci = parsed.intent;
            const ctx = {};
            if (ci.domain === 'return') {
              if (typeof ci.return_index === 'number') ctx.return_index = ci.return_index;
              if (typeof ci.return_ref === 'string') ctx.return_ref = ci.return_ref;
            }
            if (ci.domain === 'device') {
              if (typeof ci.return_index === 'number') ctx.return_index = ci.return_index;
              if (typeof ci.return_ref === 'string') ctx.return_ref = ci.return_ref;
              if (typeof ci.device_index === 'number') ctx.device_index = ci.device_index;
            }
            // Keep last known focus if anything set
            if (Object.keys(ctx).length > 0) setConversationContext(ctx);
            // If we have a device context, fetch capabilities to include in success message
            if ((ctx.return_index !== undefined || ctx.return_ref) && ctx.device_index !== undefined) {
              try {
                const ri = typeof ctx.return_index === 'number' ? ctx.return_index : (typeof ctx.return_ref === 'string' ? (ctx.return_ref.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0)) : 0);
                const caps = await apiService.getReturnDeviceCapabilities(ri, ctx.device_index);
                if (caps && caps.ok) {
                  deviceCapabilities = caps.data; // Store for later
                }
              } catch {}
            }
          } catch {}
        } catch (e) {
          addMessage({ type: 'error', content: `Intent error: ${e.message}` });
          return;
        }
      } else {
        // Legacy path
        result = await apiService.chat(processed.processed, confirmExecute, modelPref);
      }

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

      if (result && result.ok === false) {
        addMessage({ type: 'error', content: result.error || result.reason || 'Execution failed', data: result });
        return;
      }

      // Build success message data
      const successData = {};
      if (canonicalIntent) {
        successData.canonical_intent = canonicalIntent;
        successData.raw_intent = rawIntent;
      }
      if (deviceCapabilities) {
        successData.capabilities = deviceCapabilities;
      }

      addMessage({
        type: 'success',
        content: result.summary || (deviceCapabilities
          ? 'Executed. Click a parameter below to view its current value.'
          : 'Executed'),
        data: Object.keys(successData).length > 0 ? successData : undefined
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
  }, [
    addMessage,
    conversationContext,
    featureFlags.use_intents_for_chat,
    modelPref,
    confirmExecute
  ]);

  const processHelpQuery = useCallback(async (query) => {
    setIsProcessing(true);

    try {
      addMessage({
        type: 'user',
        content: `❓ ${query}`
      });

      const response = await apiService.getHelp(query, conversationContext);
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
      const [server, controller] = await Promise.allSettled([
        apiService.checkHealth(),
        apiService.checkControllerHealth()
      ]);
      const status = (server.status === 'fulfilled' ? server.value : { status: 'error' }) || {};
      if (controller.status === 'fulfilled' && controller.value) {
        status.controller_status = controller.value.status;
        status.controller_endpoint = controller.value.endpoint;
      } else if (controller.status === 'rejected') {
        status.controller_status = 'offline';
      }
      setSystemStatus(status);
    } catch (error) {
      setSystemStatus({ status: 'error', controller_status: 'offline' });
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
