/**
 * Sidebar Component
 * Left panel with Project and History tabs
 */

import { useMemo, useState } from 'react';
import {
  Drawer,
  Tabs,
  Tab,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  History as HistoryIcon,
  AccountTree as ProjectIcon
} from '@mui/icons-material';

const DRAWER_WIDTH = 320;

export function Sidebar({ messages, onReplay, open, onClose, variant = 'permanent' }) {
  const [tab, setTab] = useState(0); // 0: Project, 1: History

  const userCommands = useMemo(() => {
    // Most recent first
    return (messages || [])
      .filter(m => m.type === 'user' && m.content)
      .slice()
      .reverse();
  }, [messages]);

  return (
    <Drawer
      variant={variant}
      open={variant === 'temporary' ? open : undefined}
      onClose={variant === 'temporary' ? onClose : undefined}
      anchor="left"
      ModalProps={{ keepMounted: true }}
      PaperProps={{ sx: { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
    >
      <Box sx={{ p: 1 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          variant="fullWidth"
          size="small"
        >
          <Tab icon={<ProjectIcon fontSize="small" />} iconPosition="start" label="Project" />
          <Tab icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="History" />
        </Tabs>
      </Box>
      <Divider />

      {/* Project Tab */}
      {tab === 0 && (
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Project
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Connect Ableton Live to view tracks, sends, and devices here. While Live installs, this panel will remain empty.
          </Typography>
        </Box>
      )}

      {/* History Tab */}
      {tab === 1 && (
        <Box sx={{ p: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Typography variant="subtitle1" sx={{ px: 1, pb: 1 }}>
            Recent Commands
          </Typography>
          <List dense sx={{ overflow: 'auto' }}>
            {userCommands.length === 0 && (
              <ListItem>
                <ListItemText primary="No commands yet" secondary="Type a control or ask for help" />
              </ListItem>
            )}
            {userCommands.map((m) => (
              <ListItem key={m.id}
                secondaryAction={
                  <Tooltip title="Replay">
                    <span>
                      <IconButton edge="end" aria-label="replay" size="small" onClick={() => onReplay?.(m.content)}>
                        <PlayIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                }
              >
                <ListItemText
                  primary={m.content}
                  secondary={new Date(m.timestamp).toLocaleTimeString()}
                  primaryTypographyProps={{ noWrap: true }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Drawer>
  );
}

export const SIDEBAR_WIDTH = DRAWER_WIDTH;
