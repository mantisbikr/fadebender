/**
 * CapabilitiesDrawer Component
 * Right-anchored drawer showing capabilities for current track/return/device
 */

import { Box, Drawer, Typography, IconButton, Divider, ClickAwayListener, Tooltip, Chip } from '@mui/material';
import { Close as CloseIcon, PushPin as PushPinIcon, PushPinOutlined as PushPinOutlinedIcon } from '@mui/icons-material';
import ParamAccordion from './ParamAccordion.jsx';
import { useEffect, useState, useCallback } from 'react';
import { apiService } from '../services/api.js';
import { useMixerEvents } from '../hooks/useMixerEvents.js';

export default function CapabilitiesDrawer({ open, onClose, capabilities, pinned = false, onPinnedChange, ignoreCloseSelectors = [], initialGroup = null, initialParam = null }) {
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

  // Type badge: simplified to avoid expensive API calls
  // Prefer using track_type from liveCapabilities if available, otherwise show entity type
  const typeBadge = (() => {
    // Return contexts
    if (liveCapabilities?.entity_type === 'return' || typeof liveCapabilities?.return_index === 'number') {
      return 'RETURN';
    }
    // Track contexts - use track_type from liveCapabilities if available (added by server)
    if (liveCapabilities?.entity_type === 'track' && liveCapabilities?.track_type) {
      return String(liveCapabilities.track_type).toUpperCase();
    }
    // Device on track - use track_type if available
    if (typeof liveCapabilities?.device_index === 'number' && typeof liveCapabilities?.track_index === 'number' && liveCapabilities?.track_type) {
      return String(liveCapabilities.track_type).toUpperCase();
    }
    // Master contexts
    if (liveCapabilities?.entity_type === 'master') {
      return 'MASTER';
    }
    return null;
  })();

  // Build context-sensitive title
  let title = 'Controls';

  if (hasEntityType) {
    // Mixer entity (track/return/master mixer controls)
    // Backend provides device_name like "Track 1 Mixer", "Return A Mixer", etc.
    title = liveCapabilities.device_name || 'Mixer Controls';
  } else if (hasDeviceIndex) {
    // Device entity (effect/instrument on track or return)
    const deviceName = liveCapabilities.device_name || 'Device';
    const deviceIndex = liveCapabilities.device_index;
    const trackIndex = liveCapabilities.track_index;
    const returnIndex = liveCapabilities.return_index;

    if (trackIndex !== undefined) {
      // Track device: "Track 1 Device 0, Reverb"
      title = `Track ${trackIndex + 1} Device ${deviceIndex}, ${deviceName}`;
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h6" fontWeight="bold" color="primary">
                {title}
              </Typography>
              {typeBadge && (
                <Chip size="small" label={typeBadge} sx={{ height: 20 }} />
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Tooltip title={pinned ? 'Unpin' : 'Pin'}>
                <IconButton size="small" onClick={() => onPinnedChange?.(!pinned)}>
                  {pinned ? <PushPinIcon /> : <PushPinOutlinedIcon />}
                </IconButton>
              </Tooltip>
              <IconButton onClick={onClose} size="small">
                <CloseIcon />
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
