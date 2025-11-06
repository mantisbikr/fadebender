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
  const [featureFlags, setFeatureFlags] = useState({ use_intents_for_chat: false, sticky_capabilities_card: false });
  const [liveSnapshot, setLiveSnapshot] = useState(null);
  const [currentCapabilities, setCurrentCapabilities] = useState(null);
  const [capabilitiesDrawerOpen, setCapabilitiesDrawerOpen] = useState(false);
  const [capabilitiesDrawerPinned, setCapabilitiesDrawerPinned] = useState(false);

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
    const newMessage = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  const updateMessageStatus = useCallback((messageId, status) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, status } : msg
    ));
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
            const unit = r?.unit || '';
            let disp = r?.display_value;
            if (disp != null && disp !== '') {
              const s = String(disp);
              const m = s.match(/-?\d+(?:\.\d+)?/);
              if (m) {
                const num = parseFloat(m[0]);
                const rounded = Math.round(num * 100) / 100;
                const numStr = (rounded.toFixed(2)).replace(/\.?0+$/, '');
                disp = s.slice(0, m.index) + numStr + s.slice(m.index + m[0].length);
              }
              return unit ? `${disp} ${unit}`.trim() : String(disp);
            }
            if (r?.normalized_value != null) {
              const x = Number(r.normalized_value);
              const rounded = Math.round(x * 100) / 100;
              return String((rounded.toFixed(2)).replace(/\.?0+$/, ''));
            }
            return '';
          };
          const dv = makeDV(result);

          // Build min/max display range info
          let rangeInfo = '';
          if (result.min_display != null && result.max_display != null) {
            const fmt = (n) => {
              const x = Number(n);
              if (!Number.isFinite(x)) return String(n);
              const r2 = Math.round(x * 100) / 100;
              return (r2.toFixed(2)).replace(/\.?0+$/, '');
            };
            rangeInfo = ` Range: ${fmt(result.min_display)} to ${fmt(result.max_display)}.`;
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
          // For continuous parameters: suggest low/mid/high using display range when available
          else if (deviceRef && (result.min_display !== undefined || result.min !== undefined) && (result.max_display !== undefined || result.max !== undefined)) {
            const min = (result.min_display !== undefined) ? Number(result.min_display) : Number(result.min);
            const max = (result.max_display !== undefined) ? Number(result.max_display) : Number(result.max);
            const mid = (min + max) / 2;
            const unit = result.unit || '';
            // Format numbers to max 2 decimal places, remove trailing zeros
            const formatNum = (n) => {
              const rounded = Math.round(n * 100) / 100;
              return rounded % 1 === 0 ? rounded.toString() : rounded.toFixed(2).replace(/\.?0+$/, '');
            };
            suggested_intents = [
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(min)}${unit ? ' ' + unit : ''}`,
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(mid)}${unit ? ' ' + unit : ''}`,
              `set Return ${letter} ${deviceRef} ${paramName} to ${formatNum(max)}${unit ? ' ' + unit : ''}`
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

      const userMessageId = addMessage({
        type: 'user',
        content: rawInput,
        original: processed.original,
        processed: processed.processed,
        corrections: processed.corrections
      });

      if (!processed.validation.valid) {
        updateMessageStatus(userMessageId, 'error');
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
        updateMessageStatus(userMessageId, 'error');
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
          updateMessageStatus(userMessageId, 'error');
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

      // Auto-close drawer if this intent targets a different entity than the open drawer
      try {
        if (capabilitiesDrawerOpen && parsed && parsed.ok && parsed.intent) {
          const ci = parsed.intent;
          const cap = currentCapabilities;
          const normalizeCtx = (obj) => {
            if (!obj) return null;
            // Device context
            if (typeof obj.device_index === 'number') {
              const scope = (typeof obj.track_index === 'number') ? 'track' : (typeof obj.return_index === 'number' ? 'return' : 'unknown');
              return { type: 'device', scope, track_index: obj.track_index, return_index: obj.return_index, device_index: obj.device_index };
            }
            // Mixer context signaled by entity_type
            if (typeof obj.entity_type === 'string') {
              const et = obj.entity_type; // e.g., 'track' | 'return' | 'master'
              return { type: 'mixer', entity_type: et, track_index: obj.track_index, return_index: obj.return_index };
            }
            return null;
          };
          const capCtx = normalizeCtx(cap);
          const intentCtx = (() => {
            if (!ci) return null;
            if (ci.domain === 'device' && typeof ci.device_index === 'number') {
              // Prefer explicit indices; derive return_index from ref if needed
              let ri = ci.return_index;
              if (ri == null && typeof ci.return_ref === 'string') {
                ri = ci.return_ref.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0);
              }
              return { type: 'device', scope: 'return', return_index: ri, device_index: ci.device_index };
            }
            if (ci.domain === 'track' && ci.field) {
              return { type: 'mixer', entity_type: 'track', track_index: (typeof ci.track_index === 'number') ? (Number(ci.track_index) - 1) : undefined };
            }
            if (ci.domain === 'return' && ci.field) {
              let ri = ci.return_index;
              if (ri == null && typeof ci.return_ref === 'string') {
                ri = ci.return_ref.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0);
              }
              return { type: 'mixer', entity_type: 'return', return_index: ri };
            }
            if (ci.domain === 'master' && ci.field) {
              return { type: 'mixer', entity_type: 'master' };
            }
            return null;
          })();
          const differs = () => {
            if (!capCtx || !intentCtx) return false; // no strong signal; do not close
            if (capCtx.type !== intentCtx.type) return true;
            if (capCtx.type === 'device') {
              return (capCtx.return_index !== intentCtx.return_index) || (capCtx.device_index !== intentCtx.device_index);
            }
            if (capCtx.type === 'mixer') {
              if (capCtx.entity_type !== intentCtx.entity_type) return true;
              if (capCtx.entity_type === 'track') return capCtx.track_index !== intentCtx.track_index;
              if (capCtx.entity_type === 'return') return capCtx.return_index !== intentCtx.return_index;
              return false;
            }
            return false;
          };
          if (differs()) {
            setCapabilitiesDrawerOpen(false);
          }
        }
      } catch {}

      let result;
      let deviceCapabilities = null; // Store device capabilities to include in success message
      let mixerCapabilities = null;  // Store mixer capabilities to include in success message
      if (featureFlags.use_intents_for_chat && (parsed && parsed.ok) && parsed.intent) {
        // Execute canonical intent directly; on error surface message and stop
        try {
          result = await apiService.executeCanonicalIntent(parsed.intent);
          // If server attached capabilities, use them when client-side fetch hasn't populated yet
          try {
            const caps = result && result.data && result.data.capabilities;
            if (caps) {
              // Heuristic: device caps include device_index; mixer caps include entity_type
              if (typeof caps.device_index === 'number') {
                deviceCapabilities = deviceCapabilities || caps;
              } else {
                mixerCapabilities = mixerCapabilities || caps;
              }
            }
          } catch {}
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
                  deviceCapabilities = deviceCapabilities || caps.data; // Only use if not already set by backend
                }
              } catch {}
            }
            // If it's a mixer op, fetch mixer capabilities for the relevant entity
            try {
              if (ci.domain === 'track' && typeof ci.track_index === 'number' && ci.field) {
                // Canonical track_index is 1-based; capabilities expect 0-based
                const caps = await apiService.getTrackMixerCapabilities(Number(ci.track_index) - 1);
                if (caps && caps.ok) mixerCapabilities = mixerCapabilities || caps.data;
              } else if (ci.domain === 'return' && (typeof ci.return_index === 'number' || typeof ci.return_ref === 'string') && ci.field) {
                const ri = typeof ci.return_index === 'number' ? Number(ci.return_index) : (ci.return_ref ? (ci.return_ref.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0)) : 0);
                const caps = await apiService.getReturnMixerCapabilities(ri);
                if (caps && caps.ok) mixerCapabilities = mixerCapabilities || caps.data;
              } else if (ci.domain === 'master' && ci.field) {
                const caps = await apiService.getMasterMixerCapabilities();
                if (caps && caps.ok) mixerCapabilities = mixerCapabilities || caps.data;
              }
            } catch {}
          } catch {}
        } catch (e) {
          const msg = String(e && e.message || 'Intent execute failed');
          // Friendly clarification for device selection errors
          const devNotFound = msg.startsWith('device_not_found_for_hint:') && msg.includes('devices=[');
          const ordOutOfRange = msg.startsWith('device_ordinal_out_of_range:') && msg.includes('devices=[');
          if (devNotFound || ordOutOfRange) {
            try {
              // Extract device list from message: devices=[0:Name, 1:Other, ...]
              const m = msg.match(/devices=\[(.*)\]$/);
              const listPart = m ? m[1] : '';
              const pairs = listPart.split(',').map(s => s.trim()).filter(Boolean);
              const devices = pairs.map(p => {
                const sp = p.split(':');
                const idx = Number(sp[0]);
                const name = sp.slice(1).join(':').trim();
                return { index: isNaN(idx) ? null : idx, name };
              }).filter(d => d.index !== null);
              // Build suggested intents using current canonical or raw context
              const ci = parsed?.intent || {};
              // Determine location (Return letter preferred)
              let retRef = null;
              if (typeof ci.return_ref === 'string') retRef = ci.return_ref.toUpperCase();
              if (!retRef && typeof ci.return_index === 'number') retRef = String.fromCharCode('A'.charCodeAt(0) + Number(ci.return_index));
              // Parameter and value from intent
              const param = ci.param_ref || ci.field || 'decay';
              const val = (ci.display ? ci.display : (typeof ci.value !== 'undefined' ? String(ci.value) : ''));
              const unit = (ci.unit && ci.unit !== 'display') ? ` ${ci.unit}` : '';
              const base = retRef ? `set Return ${retRef}` : (typeof ci.track_index === 'number' ? `set track ${ci.track_index}` : `set Return A`);
              // Prefer plugin hint if present
              const plugin = (ci.device_name_hint || '').toLowerCase();
              const hasPlugin = plugin && !['device','fx','effect','plugin'].includes(plugin);
              const labelPart = val ? `${val}${unit}` : '';
              let suggestions = devices.slice(0, 6).map(d => {
                const ord = (d.index + 1); // show 1-based ordinal
                if (hasPlugin) {
                  return {
                    label: `${d.name || plugin} (${ord})`,
                    value: `${base} ${d.name} ${param} ${labelPart ? 'to ' + labelPart : ''}`.trim()
                  };
                }
                return {
                  label: `${d.name || 'Device'} (${ord})`,
                  value: `${base} device ${ord} ${param} ${labelPart ? 'to ' + labelPart : ''}`.trim()
                };
              });
              // Also suggest other returns where the plugin exists (if name given)
              if (hasPlugin) {
                try {
                  const returnsResp = await apiService.getReturnTracks();
                  const rets = (returnsResp && returnsResp.data && returnsResp.data.returns) || [];
                  const extras = [];
                  for (const r of rets) {
                    const ri2 = Number(r.index);
                    const letter2 = String.fromCharCode('A'.charCodeAt(0) + ri2);
                    // Skip current return if known
                    if (retRef && letter2.toUpperCase() === String(retRef).toUpperCase()) continue;
                    try {
                      const devsResp = await apiService.getReturnDevices(ri2);
                      const list = (devsResp && devsResp.data && devsResp.data.devices) || [];
                      const matches = list.filter(dv => String(dv.name || '').toLowerCase().replace(/\s+/g,' ') .includes(String(plugin).toLowerCase()));
                      if (matches.length > 0) {
                        const ord2 = 1; // default to first match for suggestion
                        extras.push({
                          label: `Return ${letter2}: ${matches[0].name || plugin} (${ord2})`,
                          value: `set Return ${letter2} ${matches[0].name} ${param} ${labelPart ? 'to ' + labelPart : ''}`.trim()
                        });
                      }
                    } catch {}
                    if (extras.length >= 3) break; // limit extra suggestions
                  }
                  suggestions = suggestions.concat(extras);
                } catch {}
              }
              addMessage({
                type: 'question',
                content: devNotFound
                  ? (retRef
                      ? `I couldn't find “${plugin}” on Return ${retRef}. Here’s what’s on Return ${retRef}:`
                      : `I couldn't find that device there. Here are the available devices:`)
                  : (retRef
                      ? `That ${plugin || 'device'} number isn’t available on Return ${retRef}. Here’s what’s on Return ${retRef}:`
                      : `That device number isn’t available there. Here are the available devices:`),
                data: { suggested_intents: suggestions }
              });
              return;
            } catch (_) {
              // Fall through to error
            }
          }
          // Friendly handling for device_ambiguous (no clear device match)
          const devAmbiguous = msg.startsWith('device_ambiguous') && msg.includes('devices=[');
          if (devAmbiguous) {
            try {
              // Extract device list from message: devices=[0:Name, 1:Other, ...]
              const m = msg.match(/devices=\[(.*)\]$/);
              const listPart = m ? m[1] : '';
              const pairs = listPart.split(',').map(s => s.trim()).filter(Boolean);
              const devices = pairs.map(p => {
                const sp = p.split(':');
                const idx = Number(sp[0]);
                const name = sp.slice(1).join(':').trim();
                return { index: isNaN(idx) ? null : idx, name };
              }).filter(d => d.index !== null);

              const ci = parsed?.intent || {};
              const plugin = (ci.device_name_hint || '').toLowerCase();
              let retRef = null;
              if (typeof ci.return_ref === 'string') retRef = ci.return_ref.toUpperCase();
              if (!retRef && typeof ci.return_index === 'number') retRef = String.fromCharCode('A'.charCodeAt(0) + Number(ci.return_index));

              const param = ci.param_ref || ci.field || 'decay';
              const val = (ci.display ? ci.display : (typeof ci.value !== 'undefined' ? String(ci.value) : ''));
              const unit = (ci.unit && ci.unit !== 'display') ? ` ${ci.unit}` : '';
              const base = retRef ? `set Return ${retRef}` : 'set Return A';

              // Build suggestions for devices on current return
              let suggestions = devices.slice(0, 4).map(d => ({
                label: `${d.name} on Return ${retRef || 'A'}`,
                value: `${base} ${d.name} ${param} ${val ? 'to ' + val + unit : ''}`.trim()
              }));

              // Check if plugin exists on other returns
              if (plugin) {
                try {
                  const returnsResp = await apiService.getReturnTracks();
                  const rets = (returnsResp && returnsResp.data && returnsResp.data.returns) || [];
                  for (const r of rets) {
                    const ri2 = Number(r.index);
                    const letter2 = String.fromCharCode('A'.charCodeAt(0) + ri2);
                    if (retRef && letter2.toUpperCase() === String(retRef).toUpperCase()) continue;
                    try {
                      const devsResp = await apiService.getReturnDevices(ri2);
                      const list = (devsResp && devsResp.data && devsResp.data.devices) || [];
                      const matches = list.filter(dv => String(dv.name || '').toLowerCase().includes(plugin));
                      if (matches.length > 0) {
                        suggestions.push({
                          label: `${matches[0].name} on Return ${letter2}`,
                          value: `set Return ${letter2} ${matches[0].name} ${param} ${val ? 'to ' + val + unit : ''}`.trim()
                        });
                        if (suggestions.length >= 6) break;
                      }
                    } catch {}
                  }
                } catch {}
              }

              addMessage({
                type: 'question',
                content: plugin && suggestions.length > devices.length
                  ? `I couldn't find "${plugin}" on Return ${retRef || 'A'}, but I found it on other returns. Which one did you mean?`
                  : `I couldn't find "${plugin}" on Return ${retRef || 'A'}. Here's what's available:`,
                data: { suggested_intents: suggestions }
              });
              return;
            } catch (_) {}
          }

          // Friendly handling for parameter name issues
          const paramNotFound = msg.startsWith('param_not_found:');
          const paramAmbiguous = msg.startsWith('param_ambiguous:');
          if (paramNotFound || paramAmbiguous) {
            try {
              // Build candidates from error message if present
              let candidates = [];
              const m = msg.match(/candidates=\[?([^\]]+)\]?$/);
              if (m && m[1]) {
                candidates = m[1].split(',').map(s => s.replace(/^\s*['\"]?|['\"]?\s*$/g,'').trim()).filter(Boolean);
              }
              const ci = parsed?.intent || {};

              // Check if this is a mixer operation (track/return/master without device context)
              // Mixer operations have 'field' (volume, pan, mute, solo, send)
              // Device operations have 'param_ref' (decay, feedback, etc.) and domain='device'
              const hasTrackContext = typeof ci.track_index === 'number';
              const hasReturnContext = (typeof ci.return_index === 'number' || typeof ci.return_ref === 'string');
              const hasMasterContext = ci.domain === 'master';
              const hasDeviceContext = (typeof ci.device_index === 'number'
                                        || ci.device_name_hint
                                        || ci.device_ordinal_hint);

              const isMixerOp = ((hasTrackContext || hasReturnContext || hasMasterContext)
                                && !hasDeviceContext
                                && ci.domain !== 'device')
                                || (ci.field && !ci.param_ref); // Has 'field' but no 'param_ref' indicates mixer

              let capabilities = null;
              let base = '';

              if (isMixerOp) {
                // Fetch MIXER capabilities for track/return/master
                try {
                  if (ci.domain === 'track' && typeof ci.track_index === 'number') {
                    const caps = await apiService.getTrackMixerCapabilities(Number(ci.track_index) - 1);
                    if (caps && caps.ok) capabilities = caps.data;
                    base = `set track ${ci.track_index}`;
                  } else if (ci.domain === 'return') {
                    let retRef = null;
                    if (typeof ci.return_ref === 'string') retRef = ci.return_ref.toUpperCase();
                    if (!retRef && typeof ci.return_index === 'number') retRef = String.fromCharCode('A'.charCodeAt(0) + Number(ci.return_index));
                    if (retRef) {
                      const ri = retRef.charCodeAt(0) - 'A'.charCodeAt(0);
                      const caps = await apiService.getReturnMixerCapabilities(ri);
                      if (caps && caps.ok) capabilities = caps.data;
                      base = `set Return ${retRef}`;
                    }
                  } else if (ci.domain === 'master') {
                    const caps = await apiService.getMasterMixerCapabilities();
                    if (caps && caps.ok) capabilities = caps.data;
                    base = 'set master';
                  }
                } catch {}
              } else {
                // Fetch DEVICE capabilities
                let retRef = null;
                if (typeof ci.return_ref === 'string') retRef = ci.return_ref.toUpperCase();
                if (!retRef && typeof ci.return_index === 'number') retRef = String.fromCharCode('A'.charCodeAt(0) + Number(ci.return_index));

                let deviceIdx = (typeof ci.device_index === 'number') ? Number(ci.device_index) : 0;
                const plugin = (ci.device_name_hint || '').toLowerCase();
                if ((deviceIdx === 0 || isNaN(deviceIdx)) && retRef) {
                  try {
                    const ri = retRef.charCodeAt(0) - 'A'.charCodeAt(0);
                    const devsResp = await apiService.getReturnDevices(ri);
                    const list = (devsResp && devsResp.data && devsResp.data.devices) || [];
                    if (plugin) {
                      const match = list.find(d => String(d.name || '').toLowerCase().includes(plugin));
                      if (match) deviceIdx = Number(match.index);
                    }
                  } catch {}
                }

                try {
                  if (retRef && deviceIdx >= 0) {
                    const ri = retRef.charCodeAt(0) - 'A'.charCodeAt(0);
                    const caps = await apiService.getReturnDeviceCapabilities(ri, deviceIdx);
                    if (caps && caps.ok) capabilities = caps.data;
                  }
                } catch {}

                const hasPlugin = plugin && !['device','fx','effect','plugin'].includes(plugin);
                const ord = (typeof ci.device_ordinal_hint === 'number') ? Number(ci.device_ordinal_hint) : 1;
                base = retRef ? (hasPlugin ? `set Return ${retRef} ${plugin} ${ord}` : `set Return ${retRef} device ${ord}`) : 'set Return A device 1';
              }

              // Build suggested intents using candidates or the first few params
              const labelPart = ci.display ? String(ci.display) : (typeof ci.value !== 'undefined' ? String(ci.value) : '');
              const unit = (ci.unit && ci.unit !== 'display' && labelPart) ? ` ${ci.unit}` : '';

              const aFewParams = () => {
                try {
                  if (capabilities && Array.isArray(capabilities.groups)) {
                    const params = [];
                    capabilities.groups.forEach(g => (g.params || []).forEach(p => params.push(p.name)));
                    if (Array.isArray(capabilities.ungrouped)) capabilities.ungrouped.forEach(p => params.push(p.name));
                    return params.slice(0, 6);
                  }
                } catch {}
                return [];
              };

              const paramsList = candidates.length ? candidates.slice(0, 6) : aFewParams();
              const suggestions = paramsList.map(pn => ({
                label: pn,
                value: `${base} ${pn} ${labelPart ? 'to ' + labelPart + unit : ''}`.trim()
              }));

              addMessage({
                type: 'question',
                content: paramNotFound
                  ? `I couldn't find that parameter. Try one of these or pick from the list:`
                  : `That parameter name is ambiguous. Pick one below or choose from the list:`,
                data: { suggested_intents: suggestions, capabilities }
              });
              return;
            } catch (_) {}
          }
          updateMessageStatus(userMessageId, 'error');
          addMessage({ type: 'error', content: `Intent error: ${msg}` });
          return;
        }
      } else {
        // Legacy path
        result = await apiService.chat(processed.processed, confirmExecute, modelPref);
      }

      // Prefer a clean, chat-like summary; only include details when there is an error
      if (!result.ok) {
        // Friendly handling for common mapping errors without throwing exceptions
        const summary = String(result.summary || '');
        const isParamIssue = summary.startsWith('param_not_found:') || summary.startsWith('param_ambiguous:');
        const isDevIssue = summary.startsWith('device_not_found_for_hint:') || summary.startsWith('device_ordinal_out_of_range:');
        if (isParamIssue || isDevIssue) {
          try {
            // Build suggestions similar to exception path
            const ci = parsed?.intent || {};
            let retRef = null;
            if (typeof ci.return_ref === 'string') retRef = ci.return_ref.toUpperCase();
            if (!retRef && typeof ci.return_index === 'number') retRef = String.fromCharCode('A'.charCodeAt(0) + Number(ci.return_index));
            const param = ci.param_ref || ci.field || 'decay';
            const val = (ci.display ? ci.display : (typeof ci.value !== 'undefined' ? String(ci.value) : ''));
            const unit = (ci.unit && ci.unit !== 'display') ? ` ${ci.unit}` : '';
            const base = retRef ? `set Return ${retRef}` : (typeof ci.track_index === 'number' ? `set track ${ci.track_index}` : `set Return A`);
            const plugin = (ci.device_name_hint || '').toLowerCase();
            const hasPlugin = plugin && !['device','fx','effect','plugin'].includes(plugin);
            let capabilities = null;
            // Try to fetch device capabilities for param issues to show a full card
            if (retRef && typeof ci.device_index === 'number') {
              try {
                const ri = retRef.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0);
                const caps = await apiService.getReturnDeviceCapabilities(ri, ci.device_index);
                if (caps && caps.ok) capabilities = caps.data;
              } catch {}
            }
            const suggestions = [];
            if (capabilities && Array.isArray(capabilities.groups)) {
              const params = [];
              capabilities.groups.forEach(g => (g.params || []).forEach(p => params.push(p.name)));
              (capabilities.ungrouped || []).forEach(p => params.push(p.name));
              params.slice(0, 6).forEach(pn => suggestions.push({
                label: pn,
                value: hasPlugin ? `${base} ${plugin} ${ci.device_ordinal_hint || 1} ${pn} ${val ? 'to ' + val + unit : ''}`.trim()
                                  : `${base} device ${ci.device_ordinal_hint || 1} ${pn} ${val ? 'to ' + val + unit : ''}`.trim()
              }));
            }
            addMessage({ type: 'question', content: summary, data: { suggested_intents: suggestions, capabilities } });
            return;
          } catch {}
        }
        // Default info path
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
        updateMessageStatus(userMessageId, 'error');
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
      if (mixerCapabilities) {
        successData.capabilities = mixerCapabilities;
      }
      // Also include capabilities from result.data if present (from /chat endpoint)
      if (!successData.capabilities && result.data && result.data.capabilities) {
        successData.capabilities = result.data.capabilities;
      }

      // Update capabilities and auto-open drawer if feature is enabled
      if (featureFlags.sticky_capabilities_card && successData.capabilities) {
        setCurrentCapabilities(successData.capabilities);
        setCapabilitiesDrawerOpen(true); // Auto-open drawer on successful command
      }

      // Mark user message as successful
      updateMessageStatus(userMessageId, 'success');

      // Only show success message card if sticky capabilities feature is disabled
      if (!featureFlags.sticky_capabilities_card) {
        addMessage({
          type: 'success',
          content: result.summary || (deviceCapabilities
            ? 'Executed. Click a parameter below to view its current value.'
            : 'Executed'),
          data: Object.keys(successData).length > 0 ? successData : undefined
        });
      }
      // Refresh history state after an executed command
      try { const hs = await apiService.getHistoryState(); setHistoryState(hs); } catch {}
      // Clear clarification banner on success
      setConversationContext(null);

    } catch (error) {
      updateMessageStatus(userMessageId, 'error');
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
      clearMessages,
      currentCapabilities,
      featureFlags,
      capabilitiesDrawerOpen,
      setCapabilitiesDrawerOpen,
      capabilitiesDrawerPinned,
      setCapabilitiesDrawerPinned
    };
}
