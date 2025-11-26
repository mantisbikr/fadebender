/**
 * CapabilitiesDrawer Component
 * Right-anchored drawer showing capabilities for current track/return/device
 */

import { Box, Drawer, Typography, IconButton, Divider, ClickAwayListener, Tooltip } from '@mui/material';
import { Close as CloseIcon, PushPin as PushPinIcon, PushPinOutlined as PushPinOutlinedIcon, ArrowBack as ArrowBackIcon, ArrowForward as ArrowForwardIcon, Home as HomeIcon } from '@mui/icons-material';
import ParamAccordion from './ParamAccordion.jsx';
import { useEffect, useState, useCallback } from 'react';
import { apiService } from '../services/api.js';
import { useMixerEvents } from '../hooks/useMixerEvents.js';

export default function CapabilitiesDrawer({
  open,
  onClose,
  capabilities,
  pinned = false,
  onPinnedChange,
  ignoreCloseSelectors = [],
  initialGroup = null,
  initialParam = null,
  historyIndex = -1,
  historyLength = 0,
  onHistoryBack = null,
  onHistoryForward = null,
  onHistoryHome = null
}) {
  // Local state for capabilities with live-updated values
  const [liveCapabilities, setLiveCapabilities] = useState(capabilities);

  // Update local state when prop changes
  useEffect(() => {
    setLiveCapabilities(capabilities);
  }, [capabilities]);

  // Real-time event handlers for Live parameter changes
  // IMPORTANT: Must be defined before any conditional returns (Rules of Hooks)
  // Use functional setState to avoid recreating callbacks on every state change
  const handleMixerChanged = useCallback((payload) => {
    setLiveCapabilities(prev => {
      if (!prev || !prev.values) return prev;

      // Track mixer events - payload.track is a number (0-based index from Ableton)
      if (prev.entity_type === 'track') {
        const trackIndex = typeof payload.track === 'number' ? payload.track : null;

        if (trackIndex === prev.track_index) {
          // Update mixer value in capabilities
          const field = payload.field; // e.g., "volume", "pan", "mute", "solo"
          const value = payload.value;

          console.log('[CapabilitiesDrawer] Received mixer_changed:', { trackIndex, field, value, current: prev.values[field] });

          if (field && value !== undefined) {
            return {
              ...prev,
              values: {
                ...prev.values,
                [field]: { value, display_value: payload.display_value || prev.values[field]?.display_value }
              }
            };
          }
        }
      }
      return prev;
    });
  }, []); // Empty deps - callback never recreated, EventSource stays connected

  const handleOtherEvent = useCallback((payload) => {
    setLiveCapabilities(prev => {
      if (!prev || !prev.values) return prev;

      // Return mixer events - payload.return is a number (0-based index)
      if (payload.event === 'return_mixer_changed' && prev.entity_type === 'return') {
        const returnIndex = typeof payload.return === 'number' ? payload.return : null;
        if (returnIndex === prev.return_index) {
          const field = payload.field;
          const value = payload.value;

          console.log('[CapabilitiesDrawer] Received return_mixer_changed:', { returnIndex, field, value, current: prev.values[field] });

          if (field && value !== undefined) {
            return {
              ...prev,
              values: {
                ...prev.values,
                [field]: { value, display_value: payload.display_value || prev.values[field]?.display_value }
              }
            };
          }
        }
      }

      // Master mixer events
      else if (payload.event === 'master_mixer_changed' && prev.entity_type === 'master') {
        const field = payload.field;
        const value = payload.value;

        console.log('[CapabilitiesDrawer] Received master_mixer_changed:', { field, value, current: prev.values[field] });

        if (field && value !== undefined) {
          return {
            ...prev,
            values: {
              ...prev.values,
              [field]: { value, display_value: payload.display_value || prev.values[field]?.display_value }
            }
          };
        }
      }

      // Track device parameter events
      else if (payload.event === 'device_param_changed' && typeof prev.device_index === 'number' && typeof prev.track_index === 'number') {
        const trackIndex = typeof payload.track === 'number' ? payload.track : null;
        const deviceIndex = typeof payload.device_index === 'number' ? payload.device_index : null;
        const paramName = payload.param_name;
        const value = payload.value;

        if (trackIndex === prev.track_index && deviceIndex === prev.device_index && paramName && value !== undefined) {
          console.log('[CapabilitiesDrawer] Received device_param_changed:', { trackIndex, deviceIndex, paramName, value, current: prev.values[paramName] });

          return {
            ...prev,
            values: {
              ...prev.values,
              [paramName]: { value, display_value: payload.display_value || prev.values[paramName]?.display_value }
            }
          };
        }
      }

      // Return device parameter events
      else if (payload.event === 'return_device_param_changed' && typeof prev.device_index === 'number' && typeof prev.return_index === 'number') {
        const returnIndex = typeof payload.return === 'number' ? payload.return : null;
        const deviceIndex = typeof payload.device_index === 'number' ? payload.device_index : null;
        const paramName = payload.param_name;
        const value = payload.value;

        if (returnIndex === prev.return_index && deviceIndex === prev.device_index && paramName && value !== undefined) {
          console.log('[CapabilitiesDrawer] Received return_device_param_changed:', { returnIndex, deviceIndex, paramName, value, current: prev.values[paramName] });

          return {
            ...prev,
            values: {
              ...prev.values,
              [paramName]: { value, display_value: payload.display_value || prev.values[paramName]?.display_value }
            }
          };
        }
      }

      // Master device parameter events
      else if (payload.event === 'master_device_param_changed' && prev.entity_type === 'master' && typeof prev.device_index === 'number') {
        const deviceIndex = typeof payload.device_index === 'number' ? payload.device_index : null;
        const paramName = payload.param_name;
        const value = payload.value;

        if (deviceIndex === prev.device_index && paramName && value !== undefined) {
          console.log('[CapabilitiesDrawer] Received master_device_param_changed:', { deviceIndex, paramName, value, current: prev.values[paramName] });

          return {
            ...prev,
            values: {
              ...prev.values,
              [paramName]: { value, display_value: payload.display_value || prev.values[paramName]?.display_value }
            }
          };
        }
      }

      return prev;
    });
  }, []); // Empty deps - callback never recreated, EventSource stays connected

  // Subscribe to Live events for real-time sync
  console.log('[CapabilitiesDrawer] Subscribing to mixer events, open=', open);
  useMixerEvents(handleMixerChanged, null, handleOtherEvent, open);

  // Determine what type of entity this is based on available fields
  const hasEntityType = typeof liveCapabilities?.entity_type === 'string';
  const hasDeviceIndex = typeof liveCapabilities?.device_index === 'number';

  // Build context-sensitive title
  let title = 'Controls';

  if (hasEntityType) {
    // Mixer entity (track/return/master mixer controls)
    if (liveCapabilities.entity_type === 'return' && typeof liveCapabilities.return_index === 'number') {
      // Return mixer: simple format "Return A Mixer"
      const returnLetter = String.fromCharCode(65 + liveCapabilities.return_index);
      title = `Return ${returnLetter} Mixer`;
    } else if (liveCapabilities.entity_type === 'track') {
      // Track mixer: use device_name from backend (e.g., "Track 1 Mixer")
      title = liveCapabilities.device_name || 'Track Mixer';
    } else if (liveCapabilities.entity_type === 'master') {
      // Master mixer
      title = liveCapabilities.device_name || 'Master Mixer';
    } else {
      title = liveCapabilities.device_name || 'Mixer Controls';
    }
  } else if (hasDeviceIndex) {
    // Device entity (effect/instrument on track or return)
    const deviceName = liveCapabilities.device_name || 'Device';
    const deviceIndex = liveCapabilities.device_index;
    const trackIndex = liveCapabilities.track_index;
    const returnIndex = liveCapabilities.return_index;

    if (trackIndex !== undefined) {
      // Track device: track_index from backend is already 1-based (matches REST API /track/device/capabilities)
      title = `Track ${trackIndex} Device ${deviceIndex}, ${deviceName}`;
    } else if (returnIndex !== undefined) {
      // Return device: "Return A Device 0, Reverb"
      const returnLetter = String.fromCharCode(65 + returnIndex); // 0 -> A, 1 -> B, etc.
      title = `Return ${returnLetter} Device ${deviceIndex}, ${deviceName}`;
    } else {
      // Fallback
      title = `Device ${deviceIndex}, ${deviceName}`;
    }
  }

  const isInIgnoredArea = (event) => {
    try {
      const path = event.composedPath ? event.composedPath() : [];
      for (const sel of ignoreCloseSelectors) {
        const el = document.querySelector(sel);
        if (!el) continue;
        if (path.includes(el) || (event.target && (el === event.target || el.contains(event.target)))) return true;
      }
    } catch {}
    return false;
  };

  const handleClickAway = (event) => {
    if (!open) return;
    if (pinned) return; // do not close when pinned
    if (isInIgnoredArea(event)) return; // allow typing in chat input without closing
    onClose?.();
  };

  // Early return check AFTER all hooks (Rules of Hooks)
  if (!liveCapabilities) {
    return null;
  }

  return (
    <ClickAwayListener onClickAway={handleClickAway} mouseEvent="onMouseDown" touchEvent="onTouchStart">
      <Drawer
        anchor="right"
        open={open}
        // Use persistent with no backdrop so the rest of the UI stays interactive
        variant="persistent"
        hideBackdrop
        ModalProps={{
          keepMounted: true,
          disableEnforceFocus: true,
        }}
        sx={{
          '& .MuiDrawer-paper': {
            width: 380,
            maxWidth: '90vw'
          }
        }}
      >
        <Box sx={{ p: 2 }}>
          {/* Header with title, pin and close buttons */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', flex: 1, mr: 0.5, minWidth: 0 }}>
              <Tooltip title={title} placement="bottom-start">
                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  color="primary"
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontSize: '1rem'
                  }}
                >
                  {title}
                </Typography>
              </Tooltip>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, flexShrink: 0 }}>
              {/* History navigation */}
              {historyLength > 1 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, mr: 0.5, borderRight: '1px solid', borderColor: 'divider', pr: 0.5 }}>
                  <Tooltip title="Previous">
                    <span>
                      <IconButton
                        size="small"
                        onClick={onHistoryBack}
                        disabled={historyIndex >= historyLength - 1}
                        sx={{ p: 0.5 }}
                      >
                        <ArrowBackIcon sx={{ fontSize: 18 }} />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Typography variant="caption" color="text.secondary" sx={{ minWidth: '3ch', textAlign: 'center', fontSize: '0.7rem' }}>
                    {historyIndex + 1}/{historyLength}
                  </Typography>
                  <Tooltip title="Next">
                    <span>
                      <IconButton
                        size="small"
                        onClick={onHistoryForward}
                        disabled={historyIndex <= 0}
                        sx={{ p: 0.5 }}
                      >
                        <ArrowForwardIcon sx={{ fontSize: 18 }} />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Latest">
                    <span>
                      <IconButton
                        size="small"
                        onClick={onHistoryHome}
                        disabled={historyIndex === 0}
                        sx={{ p: 0.5 }}
                      >
                        <HomeIcon sx={{ fontSize: 18 }} />
                      </IconButton>
                    </span>
                  </Tooltip>
                </Box>
              )}
              <Tooltip title={pinned ? 'Unpin' : 'Pin'}>
                <IconButton size="small" onClick={() => onPinnedChange?.(!pinned)} sx={{ p: 0.5 }}>
                  {pinned ? <PushPinIcon sx={{ fontSize: 18 }} /> : <PushPinOutlinedIcon sx={{ fontSize: 18 }} />}
                </IconButton>
              </Tooltip>
              <IconButton onClick={onClose} size="small" sx={{ p: 0.5 }}>
                <CloseIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Box>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {/* Capabilities content - use liveCapabilities for real-time updates */}
          <ParamAccordion capabilities={liveCapabilities} initialGroup={initialGroup} initialParam={initialParam} />
        </Box>
      </Drawer>
    </ClickAwayListener>
  );
}
