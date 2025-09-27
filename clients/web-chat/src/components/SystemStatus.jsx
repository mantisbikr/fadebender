/**
 * System Status Component
 * Displays health checks in a collapsible accordion
 */

import { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  Box,
  Typography,
  Chip,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  FiberManualRecord as StatusDotIcon
} from '@mui/icons-material';

function SystemStatus({ systemStatus, conversationContext }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const getAiStatusColor = (available) => {
    return available ? 'info' : 'warning';
  };

  const getStatusDotColor = (status) => {
    switch (status) {
      case 'healthy': return 'success.main';
      case 'unhealthy': return 'error.main';
      default: return 'grey.500';
    }
  };

  return (
    <Box>
      <Button
        onClick={handleClick}
        variant="outlined"
        size="small"
        startIcon={<StatusDotIcon sx={{ color: getStatusDotColor(systemStatus?.status) }} />}
        endIcon={<ExpandMoreIcon />}
        sx={{ textTransform: 'none' }}
      >
        System
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        slotProps={{
          paper: {
            sx: { minWidth: 200 }
          }
        }}
      >
        <MenuItem disableRipple>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
            <Typography variant="body2" color="text.secondary">
              Status:
            </Typography>
            <Chip
              label={systemStatus?.status || 'connecting...'}
              size="small"
              color={getStatusColor(systemStatus?.status)}
            />
          </Box>
        </MenuItem>

        <MenuItem disableRipple>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
            <Typography variant="body2" color="text.secondary">
              AI Parser:
            </Typography>
            <Chip
              label={systemStatus?.ai_parser_available ? 'Active' : 'Fallback'}
              size="small"
              color={getAiStatusColor(systemStatus?.ai_parser_available)}
            />
          </Box>
        </MenuItem>

        {conversationContext && (
          <>
            <Divider />
            <MenuItem disableRipple>
              <Chip
                label="🤔 Awaiting clarification"
                size="small"
                color="secondary"
                sx={{ width: '100%' }}
              />
            </MenuItem>
          </>
        )}
      </Menu>
    </Box>
  );
}

export default SystemStatus;