/**
 * Sidebar Component
 * Left panel with Project and History tabs
 */

import { useMemo, useState, useEffect, useRef, useCallback } from 'react';
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
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider
} from '@mui/material';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import {
  PlayArrow as PlayIcon,
  History as HistoryIcon,
  AccountTree as ProjectIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { apiService } from '../services/api.js';
import { liveFloatToDb, liveFloatToDbSend, dbFromStatus, panLabelFromStatus } from '../utils/volumeUtils.js';
import { useMixerEvents } from '../hooks/useMixerEvents.js';
import TrackRow from './TrackRow.jsx';
import ClickAwayAccordion from './ClickAwayAccordion.jsx';

const DRAWER_WIDTH = 320;

export function Sidebar({ messages, onReplay, open, onClose, variant = 'permanent', onSetDraft }) {
  const [tab, setTab] = useState(0); // 0: Project, 1: History
  const [outline, setOutline] = useState(null);
  const [loadingOutline, setLoadingOutline] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [trackStatus, setTrackStatus] = useState(null);
  const [rowStatuses, setRowStatuses] = useState({}); // per-track cached status
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [sendsFastRefreshMs, setSendsFastRefreshMs] = useState(800);
  const [sseThrottleMs, setSseThrottleMs] = useState(150);
  const [followSelection, setFollowSelection] = useState(true);
  const [sends, setSends] = useState(null);
  const [loadingSends, setLoadingSends] = useState(false);
  const [sendsOpen, setSendsOpen] = useState(false);
  const [returns, setReturns] = useState(null);
  const [loadingReturns, setLoadingReturns] = useState(false);
  const [openReturn, setOpenReturn] = useState(null);
  const [returnDevices, setReturnDevices] = useState({}); // { [returnIndex]: devices[] }
  const [learnedMap, setLearnedMap] = useState({}); // { `${ri}:${di}`: bool }
  const [learnJobs, setLearnJobs] = useState({}); // { `${ri}:${di}`: { jobId, progress, total, state } }
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
          // clear sends cache on selection change; fetch on demand when accordion expands
          setSends(null);
        }
      }
    } catch (e) {
      // don't clobber existing outline unless manual
      if (manual) setOutline(null);
    } finally {
      if (manual) setLoadingOutline(false);
    }
  };

  // Load app config once to initialize UI timings
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const cfg = await apiService.getAppConfig();
        const ui = cfg?.ui || {};
        if (mounted) {
          if (ui.refresh_ms) setRefreshInterval(Number(ui.refresh_ms));
          if (ui.sends_open_refresh_ms) setSendsFastRefreshMs(Number(ui.sends_open_refresh_ms));
          if (ui.sse_throttle_ms) setSseThrottleMs(Number(ui.sse_throttle_ms));
        }
      } catch {}
    })();
    return () => { mounted = false; };
  }, []);

  const fetchSends = async (idx, opts = {}) => {
    const silent = !!opts.silent;
    try {
      if (!silent) setLoadingSends(true);
      const res = await apiService.getTrackSends(idx);
      const next = (res && res.data && Array.isArray(res.data.sends)) ? res.data.sends : [];
      setSends((prev) => {
        if (!Array.isArray(prev) || prev.length === 0) return next;
        const byIdx = new Map(next.map((x) => [x.index, x]));
        const merged = prev.map((p) => {
          const n = byIdx.get(p.index);
          if (!n) return p;
          const same = p.value === n.value && (p.name || '') === (n.name || '');
          return same ? p : { ...p, value: n.value, name: n.name };
        });
        next.forEach((n) => { if (!merged.find((m) => m.index === n.index)) merged.push(n); });
        return merged;
      });
    } catch {
      if (!silent) setSends([]);
    } finally {
      if (!silent) setLoadingSends(false);
    }
  };

  const fetchReturns = async () => {
    try {
      setLoadingReturns(true);
      const res = await apiService.getReturnTracks();
      setReturns((res && res.data && Array.isArray(res.data.returns)) ? res.data.returns : []);
    } catch {
      setReturns([]);
    } finally {
      setLoadingReturns(false);
    }
  };

  const fetchReturnDevices = async (ri) => {
    try {
      const res = await apiService.getReturnDevices(ri);
      const devs = (res && res.data && Array.isArray(res.data.devices)) ? res.data.devices : [];
      setReturnDevices(prev => ({ ...prev, [ri]: devs }));
      // Check learned status for each device
      devs.forEach(async (d) => {
        try {
          const mr = await apiService.getReturnDeviceMap(ri, d.index);
          setLearnedMap(prev => ({ ...prev, [`${ri}:${d.index}`]: !!(mr && mr.exists) }));
        } catch {}
      });
    } catch {}
  };

  const ensureRowStatus = async (idx) => {
    try {
      if (!idx) return;
      const existing = rowStatuses[idx];
      if (existing) return existing;
      const res = await apiService.getTrackStatus(idx);
      const data = res.data || null;
      setRowStatuses((prev) => ({ ...prev, [idx]: data }));
      return data;
    } catch {
      return null;
    }
  };

  // Helper: get freshest known status for a track index
  // Used by tooltips, row UI, and detail panel to read current values
  const getStatus = (idx) => {
    return (selectedIndex === idx ? trackStatus : null) || rowStatuses[idx] || null;
  };

  // Helper: refresh a specific track and update caches
  // Called by: SSE mixer_changed handler, tooltip onOpen, and after mute/solo ops
  const refreshTrack = async (idx) => {
    try {
      if (!idx) return null;
      const res = await apiService.getTrackStatus(idx);
      const data = res.data || null;
      setRowStatuses((prev) => ({ ...prev, [idx]: data }));
      if (selectedIndex === idx) setTrackStatus(data);
      return data;
    } catch {
      return null;
    }
  };

  useEffect(() => {
    if (tab !== 0) return;
    let mounted = true;
    (async () => { if (mounted) await fetchOutline(); })();
    return () => { mounted = false; };
  }, [tab]);

  // Throttled refresh for SSE bursts
  const lastRefreshRef = useRef({});
  const refreshTrackThrottled = useCallback(async (idx) => {
    const now = Date.now();
    const last = lastRefreshRef.current[idx] || 0;
    if (now - last < sseThrottleMs) return null;
    lastRefreshRef.current[idx] = now;
    return refreshTrack(idx);
  }, [refreshTrack, sseThrottleMs]);

  // Subscribe to mixer events via hook
  useMixerEvents(
    (payload) => {
      if (tab !== 0 || !payload?.track) return;
      // Always refresh basic track status
      refreshTrackThrottled(payload.track);
      // If sends accordion is open for the selected track and a send changed, refresh sends too
      if (payload.event === 'send_changed' && sendsOpen && selectedIndex === payload.track) {
        fetchSends(selectedIndex, { silent: true });
      }
    },
    () => { if (tab === 0) { fetchOutline(false); } },
    tab === 0
  );

  // Auto-refresh outline and selected track status every 5s when Project tab is active
  useEffect(() => {
    if (tab !== 0 || !autoRefresh) return;
    const id = setInterval(() => {
      fetchOutline(false);
      if (selectedIndex) {
        apiService.getTrackStatus(selectedIndex).then((ts) => setTrackStatus(ts.data || null)).catch(() => {});
        if (sendsOpen) {
          fetchSends(selectedIndex, { silent: true });
        }
      }
    }, refreshInterval);
    return () => clearInterval(id);
  }, [tab, autoRefresh, selectedIndex, followSelection, refreshInterval, sendsOpen]);

  // Faster, low-jitter refresh loop for sends while accordion is open
  useEffect(() => {
    if (tab !== 0 || !sendsOpen || !selectedIndex) return;
    const id = setInterval(() => {
      fetchSends(selectedIndex, { silent: true });
    }, sendsFastRefreshMs);
    return () => clearInterval(id);
  }, [tab, sendsOpen, selectedIndex, sendsFastRefreshMs]);

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
          {/* Settings (from server config) */}
          <Accordion disableGutters elevation={0} sx={{ mb: 1, border: '1px dashed', borderColor: 'divider', '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  label="Refresh (ms)"
                  type="number"
                  size="small"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  sx={{ width: 140 }}
                />
                <TextField
                  label="Sends Open (ms)"
                  type="number"
                  size="small"
                  value={sendsFastRefreshMs}
                  onChange={(e) => setSendsFastRefreshMs(Number(e.target.value))}
                  sx={{ width: 160 }}
                />
                <TextField
                  label="SSE Throttle (ms)"
                  type="number"
                  size="small"
                  value={sseThrottleMs}
                  onChange={(e) => setSseThrottleMs(Number(e.target.value))}
                  sx={{ width: 160 }}
                />
                <Button size="small" variant="outlined" onClick={async () => {
                  try {
                    await apiService.updateAppConfig({ ui: { refresh_ms: refreshInterval, sends_open_refresh_ms: sendsFastRefreshMs, sse_throttle_ms: sseThrottleMs } });
                  } catch {}
                }}>Save</Button>
                <Button size="small" onClick={async () => {
                  try {
                    const cfg = await apiService.getAppConfig();
                    const ui = cfg?.ui || {};
                    if (ui.refresh_ms) setRefreshInterval(Number(ui.refresh_ms));
                    if (ui.sends_open_refresh_ms) setSendsFastRefreshMs(Number(ui.sends_open_refresh_ms));
                    if (ui.sse_throttle_ms) setSseThrottleMs(Number(ui.sse_throttle_ms));
                  } catch {}
                }}>Reload</Button>
              </Box>
            </AccordionDetails>
          </Accordion>
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
              {/* Return Tracks come first, like Live's layout */}
              <Accordion
                disableGutters
                elevation={0}
                onChange={(_, expanded) => { if (expanded) fetchReturns(); }}
                sx={{ mb: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1, '&:before': { display: 'none' } }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle2">Return Tracks</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {loadingReturns && (
                    <Typography variant="body2" color="text.secondary">Loading…</Typography>
                  )}
                  {!loadingReturns && (!returns || returns.length === 0) && (
                    <Typography variant="body2" color="text.secondary">No returns</Typography>
                  )}
                  {!loadingReturns && returns && returns.length > 0 && (
                    <List dense>
                      {returns.map((r) => (
                        <ListItem key={r.index} sx={{ display: 'block' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                            <Typography variant="body2" noWrap>{r.name || `Return ${r.index}`}</Typography>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button size="small" onClick={async () => { const next = (openReturn === r.index) ? null : r.index; setOpenReturn(next); if (next != null) await fetchReturnDevices(next); }}>
                                {openReturn === r.index ? 'Hide' : 'Show'} Devices
                              </Button>
                            </Box>
                          </Box>
                          {openReturn === r.index && (
                            <Box sx={{ mt: 1, pl: 1 }}>
                              {!returnDevices[r.index] && (
                                <Typography variant="caption" color="text.secondary">Loading devices…</Typography>
                              )}
                              {returnDevices[r.index] && returnDevices[r.index].length === 0 && (
                                <Typography variant="caption" color="text.secondary">No devices</Typography>
                              )}
                              {returnDevices[r.index] && returnDevices[r.index].map((d) => (
                                <Box key={d.index} sx={{ mb: 0.5, pl: 1, pr: 1 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: 320 }}>
                                    <Typography variant="body2" noWrap>{d.name || `Device ${d.index}`}</Typography>
                                    {learnedMap[`${r.index}:${d.index}`]
                                      ? <Chip size="small" label="Learned" color="success" variant="outlined" />
                                      : (
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                          {learnJobs[`${r.index}:${d.index}`]?.state === 'running' && (
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                              <Typography variant="caption" color="text.secondary">
                                                {Math.round((learnJobs[`${r.index}:${d.index}`].progress / Math.max(1, learnJobs[`${r.index}:${d.index}`].total)) * 100)}%
                                              </Typography>
                                            </Box>
                                          )}
                                          <Button size="small" variant="outlined" onClick={async () => {
                                            try {
                                              const st = await apiService.learnReturnDeviceStart(r.index, d.index, 41, 20);
                                              const jobId = st?.job_id;
                                              if (!jobId) return;
                                              setLearnJobs(prev => ({ ...prev, [`${r.index}:${d.index}`]: { jobId, state: 'running', progress: 0, total: 1 } }));
                                              // Poll status
                                              const key = `${r.index}:${d.index}`;
                                              const poll = async () => {
                                                try {
                                                  const s = await apiService.learnReturnDeviceStatus(jobId);
                                                  setLearnJobs(prev => ({ ...prev, [key]: { ...(prev[key]||{}), ...s, jobId } }));
                                                  if (s && s.state === 'done') {
                                                    setLearnedMap(prev => ({ ...prev, [key]: true }));
                                                    return;
                                                  }
                                                  if (s && s.state === 'error') return;
                                                  setTimeout(poll, 400);
                                                } catch {
                                                  setTimeout(poll, 600);
                                                }
                                              };
                                              poll();
                                            } catch {}
                                          }}>Learn</Button>
                                        </Box>
                                      )}
                                  </Box>
                                </Box>
                              ))}
                            </Box>
                          )}
                        </ListItem>
                      ))}
                    </List>
                  )}
                </AccordionDetails>
              </Accordion>

              <List dense>
                {outline.tracks.map((t) => (
                  <TrackRow
                    key={t.index}
                    track={t}
                    isSelected={selectedIndex === t.index}
                    getStatus={getStatus}
                    refreshTrack={refreshTrack}
                    setSelectedIndex={setSelectedIndex}
                    onSetDraft={onSetDraft}
                    onHoverPrime={ensureRowStatus}
                  />
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
                            ? `${liveFloatToDb(Number(trackStatus.mixer.volume)).toFixed(1)} dB`
                            : '—')
                    }
                    {' '}• Pan: {trackStatus.mixer?.pan != null ? `${Math.round(Math.abs(trackStatus.mixer.pan) * 50)}${trackStatus.mixer.pan < 0 ? 'L' : (trackStatus.mixer.pan > 0 ? 'R' : '')}` : '—'}
                  </Typography>

                  {/* Sends Accordion */}
                  <Accordion
                    disableGutters
                    elevation={0}
                    onChange={(_, expanded) => {
                      setSendsOpen(!!expanded);
                      if (expanded && selectedIndex) fetchSends(selectedIndex);
                    }}
                    sx={{ mt: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1, '&:before': { display: 'none' } }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">Sends</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      {loadingSends && sends === null && (
                        <Typography variant="body2" color="text.secondary">Loading…</Typography>
                      )}
                      {!loadingSends && (!sends || sends.length === 0) && (
                        <Typography variant="body2" color="text.secondary">No sends</Typography>
                      )}
                      {!loadingSends && sends && sends.length > 0 && (
                        <List dense>
                          {sends.map((s, i) => (
                            <ListItem key={s.index} disableGutters>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                                <Typography variant="body2" sx={{ minWidth: 80 }}>
                                  {s.name || `Send ${s.index}`}
                                </Typography>
                                <Slider
                                  size="small"
                                  value={typeof s.value === 'number' ? s.value : 0}
                                  min={0}
                                  max={1}
                                  step={0.005}
                                  valueLabelDisplay="auto"
                                  valueLabelFormat={(v) => `${liveFloatToDbSend(Number(v)).toFixed(1)} dB`}
                                  onChange={(_, val) => {
                                    const v = Array.isArray(val) ? val[0] : val;
                                    setSends(prev => {
                                      const next = [...(prev || [])];
                                      next[i] = { ...next[i], value: Number(v) };
                                      return next;
                                    });
                                  }}
                                  onChangeCommitted={async (_, val) => {
                                    const v = Array.isArray(val) ? val[0] : val;
                                    try {
                                      await apiService.setSend(selectedIndex, s.index, Number(v));
                                    } catch {}
                                  }}
                                  sx={{ flex: 1, maxWidth: '60%' }}
                                />
                                <Tooltip title={`${liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB`}>
                                  <Typography variant="caption" color="text.secondary" sx={{ width: 56, textAlign: 'right' }}>
                                    {liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB
                                  </Typography>
                                </Tooltip>
                              </Box>
                            </ListItem>
                          ))}
                        </List>
                      )}
                  </AccordionDetails>
                  </Accordion>

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
