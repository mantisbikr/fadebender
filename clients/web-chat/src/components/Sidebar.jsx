/**
 * Sidebar Component
 * Left panel with Project and History tabs
 */

import { useMemo, useState, useEffect, useRef } from 'react';
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
  Tooltip,
  Button,
  Select as MUISelect,
  MenuItem
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  History as HistoryIcon,
  AccountTree as ProjectIcon
} from '@mui/icons-material';
import { apiService } from '../services/api.js';

const DRAWER_WIDTH = 320;

export function Sidebar({ messages, onReplay, open, onClose, variant = 'permanent', onSetDraft }) {
  const [tab, setTab] = useState(0); // 0: Project, 1: History
  const [outline, setOutline] = useState(null);
  const [loadingOutline, setLoadingOutline] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [trackStatus, setTrackStatus] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [followSelection, setFollowSelection] = useState(true);
  const prevOutlineRef = useRef('');

  const userCommands = useMemo(() => {
    // Most recent first
    return (messages || [])
      .filter(m => m.type === 'user' && m.content)
      .slice()
      .reverse();
  }, [messages]);

  const fetchOutline = async (manual = false) => {
    try {
      if (manual) setLoadingOutline(true);
      const res = await apiService.getProjectOutline();
      const data = res.data || null;
      const nextStr = JSON.stringify(data || {});
      if (nextStr !== prevOutlineRef.current) {
        prevOutlineRef.current = nextStr;
        setOutline(data);
        if (followSelection && data && data.selected_track) {
          setSelectedIndex(data.selected_track);
          // Also refresh track status when following selection
          try { const ts = await apiService.getTrackStatus(data.selected_track); setTrackStatus(ts.data || null); } catch {}
        }
      }
    } catch (e) {
      // don't clobber existing outline unless manual
      if (manual) setOutline(null);
    } finally {
      if (manual) setLoadingOutline(false);
    }
  };

  useEffect(() => {
    if (tab !== 0) return;
    let mounted = true;
    (async () => { if (mounted) await fetchOutline(); })();
    return () => { mounted = false; };
  }, [tab]);

  // Auto-refresh outline and selected track status every 5s when Project tab is active
  useEffect(() => {
    if (tab !== 0 || !autoRefresh) return;
    const id = setInterval(() => {
      fetchOutline(false);
      if (selectedIndex) {
        apiService.getTrackStatus(selectedIndex).then((ts) => setTrackStatus(ts.data || null)).catch(() => {});
      }
    }, refreshInterval);
    return () => clearInterval(id);
  }, [tab, autoRefresh, selectedIndex, followSelection, refreshInterval]);

  // When outline is fetched the first time, set selected to outline.selected_track if present
  useEffect(() => {
    if (!outline) return;
    if (!selectedIndex && outline.selected_track) {
      setSelectedIndex(outline.selected_track);
    }
  }, [outline, selectedIndex]);

  // Fetch per-track status when selected changes
  const fetchTrackStatus = async (idx) => {
    try {
      const res = await fetch(`${window.location.origin.replace('3000','8722')}/track/status?index=${idx}`);
      const json = await res.json();
      setTrackStatus(json.data || null);
    } catch (e) {
      setTrackStatus(null);
    }
  };

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
        <Box sx={{ p: 2, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle1">Project</Typography>
            <Button size="small" variant="outlined" onClick={() => fetchOutline(true)} disabled={loadingOutline}
              sx={{ minHeight: 28, px: 1.25, py: 0.25 }}>
              {loadingOutline ? 'Refreshing…' : 'Refresh'}
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">Refresh every</Typography>
            <MUISelect
              size="small"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              sx={{ minHeight: 28, '& .MuiSelect-select': { py: 0.5, pr: 3, pl: 1.25 } }}
              title="Auto-refresh interval"
            >
              <MenuItem value={3000}>3s</MenuItem>
              <MenuItem value={5000}>5s</MenuItem>
              <MenuItem value={10000}>10s</MenuItem>
              <MenuItem value={30000}>30s</MenuItem>
            </MUISelect>
          </Box>
          {loadingOutline && (
            <Typography variant="body2" color="text.secondary">Loading…</Typography>
          )}
          {!loadingOutline && (!outline || !outline.tracks || outline.tracks.length === 0) && (
            <Typography variant="body2" color="text.secondary">
              Connect Ableton Live to view tracks, sends, and devices here.
            </Typography>
          )}
          {!loadingOutline && outline && outline.tracks && outline.tracks.length > 0 && (
            <>
              <List dense>
                {outline.tracks.map((t) => (
                  <ListItem
                    key={t.index}
                    selected={selectedIndex === t.index}
                    onClick={() => { setSelectedIndex(t.index); fetchTrackStatus(t.index); }}
                    sx={{ cursor: 'pointer' }}
                  >
                    <ListItemText
                      primary={`${t.index}. ${t.name}`}
                      secondary={t.type}
                    />
                  </ListItem>
                ))}
              </List>

              {selectedIndex && trackStatus && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Track {trackStatus.index}: {trackStatus.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Volume: {
                      typeof trackStatus.volume_db === 'number'
                        ? `${trackStatus.volume_db.toFixed(1)} dB`
                        : (trackStatus.mixer?.volume != null
                            ? `${(Math.max(-60, Math.min(6, ((Number(trackStatus.mixer.volume) - 0.85) / 0.025))).toFixed(1))} dB`
                            : '—')
                    }
                    {' '}• Pan: {trackStatus.mixer?.pan != null ? `${Math.round(Math.abs(trackStatus.mixer.pan) * 50)}${trackStatus.mixer.pan < 0 ? 'L' : (trackStatus.mixer.pan > 0 ? 'R' : '')}` : '—'}
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    <Tooltip title="Volume accepts dB (e.g., -6)">
                      <Button size="small" variant="text" onClick={() => onSetDraft?.(`set track ${selectedIndex} volume to -6`)}>
                        Set volume…
                      </Button>
                    </Tooltip>
                    <Tooltip title="Pan accepts −50..50 or Live style 25L/25R">
                      <Button size="small" variant="text" onClick={() => onSetDraft?.(`set track ${selectedIndex} pan to 20L`)}>
                        Set pan…
                      </Button>
                    </Tooltip>
                    <Button
                      size="small"
                      variant={trackStatus?.mute ? 'contained' : 'outlined'}
                      color={trackStatus?.mute ? 'warning' : 'inherit'}
                      onClick={async () => {
                        try {
                          await apiService.setMixer(selectedIndex, 'mute', trackStatus?.mute ? 0 : 1);
                          const ts = await apiService.getTrackStatus(selectedIndex);
                          setTrackStatus(ts.data || null);
                        } catch {}
                      }}
                    >
                      {trackStatus?.mute ? 'Unmute' : 'Mute'}
                    </Button>
                    <Button
                      size="small"
                      variant={trackStatus?.solo ? 'contained' : 'outlined'}
                      color={trackStatus?.solo ? 'success' : 'inherit'}
                      onClick={async () => {
                        try {
                          await apiService.setMixer(selectedIndex, 'solo', trackStatus?.solo ? 0 : 1);
                          const ts = await apiService.getTrackStatus(selectedIndex);
                          setTrackStatus(ts.data || null);
                        } catch {}
                      }}
                    >
                      {trackStatus?.solo ? 'Unsolo' : 'Solo'}
                    </Button>
                  </Box>
                </Box>
              )}
            </>
          )}
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
