/**
 * CapabilitiesDrawer Component
 * Right-anchored drawer showing capabilities for current track/return/device
 */

import { Box, Drawer, Typography, IconButton, Divider } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import ParamAccordion from './ParamAccordion.jsx';

export default function CapabilitiesDrawer({ open, onClose, capabilities }) {
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

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: 380,
          maxWidth: '90vw'
        }
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Header with title and close button */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight="bold" color="primary">
            {title}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Capabilities content */}
        <ParamAccordion capabilities={capabilities} />
      </Box>
    </Drawer>
  );
}
