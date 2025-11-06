/**
 * CapabilitiesDrawer Component
 * Right-anchored drawer showing capabilities for current track/return/device
 */

import { Box, Drawer, Typography, IconButton, Divider, ClickAwayListener, Tooltip } from '@mui/material';
import { Close as CloseIcon, PushPin as PushPinIcon, PushPinOutlined as PushPinOutlinedIcon } from '@mui/icons-material';
import ParamAccordion from './ParamAccordion.jsx';

export default function CapabilitiesDrawer({ open, onClose, capabilities, pinned = false, onPinnedChange, ignoreCloseSelectors = [] }) {
  if (!capabilities) {
    return null;
  }

  // Determine what type of entity this is based on available fields
  const hasEntityType = typeof capabilities?.entity_type === 'string';
  const hasDeviceIndex = typeof capabilities?.device_index === 'number';

  // Build context-sensitive title
  let title = 'Controls';

  if (hasEntityType) {
    // Mixer entity (track/return/master mixer controls)
    // Backend provides device_name like "Track 1 Mixer", "Return A Mixer", etc.
    title = capabilities.device_name || 'Mixer Controls';
  } else if (hasDeviceIndex) {
    // Device entity (effect/instrument on track or return)
    const deviceName = capabilities.device_name || 'Device';
    const deviceIndex = capabilities.device_index;
    const trackIndex = capabilities.track_index;
    const returnIndex = capabilities.return_index;

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
            <Typography variant="h6" fontWeight="bold" color="primary">
              {title}
            </Typography>
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

          {/* Capabilities content */}
          <ParamAccordion capabilities={capabilities} />
        </Box>
      </Drawer>
    </ClickAwayListener>
  );
}
