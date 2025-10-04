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

export function Sidebar({ messages, onReplay, open, onClose, variant = 'permanent', onSetDraft, widthPx = 360 }) {
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
  const [returnSends, setReturnSends] = useState({}); // { [returnIndex]: sends[] }
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

  // Listen for global refresh requests (from Settings modal)
  useEffect(() => {
    const handler = () => fetchOutline(true);
    window.addEventListener('fb:refresh-project', handler);
    return () => window.removeEventListener('fb:refresh-project', handler);
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

  const fetchReturnSends = async (ri, opts = {}) => {
    const silent = !!opts.silent;
    try {
      const res = await apiService.getReturnSends(ri);
      const snds = (res && res.data && Array.isArray(res.data.sends)) ? res.data.sends : [];
      setReturnSends(prev => ({ ...prev, [ri]: snds }));
    } catch {
      if (!silent) setReturnSends(prev => ({ ...prev, [ri]: [] }));
    }
  };

  const fetchReturnDevices = async (ri) => {
    try {
      const res = await apiService.getReturnDevices(ri);
      const devs = (res && res.data && Array.isArray(res.data.devices)) ? res.data.devices : [];
      // For each device get minimal param state to derive on/off
      const withState = await Promise.all(devs.map(async (d) => {
        try {
          const pr = await apiService.getReturnDeviceParams(ri, d.index);
          const params = (pr && pr.data && Array.isArray(pr.data.params)) ? pr.data.params : [];
          const devOn = params.find(p => (p.name || '').toLowerCase() === 'device on');
          let isOn = true;
          if (devOn && typeof devOn.value === 'number') {
            isOn = devOn.value >= 0.5;
          } else {
            const dw = params.find(p => {
              const n = (p.name || '').toLowerCase();
              return n === 'dry/wet' || n === 'mix';
            });
            if (dw && typeof dw.value === 'number') isOn = dw.value > 0.0;
          }
          return { ...d, isOn };
        } catch {
          return { ...d, isOn: true };
        }
      }));
      setReturnDevices(prev => ({ ...prev, [ri]: withState }));
      // Check learned status once per device
      withState.forEach(async (d) => {
        try {
          const key = `${ri}:${d.index}`;
          if (learnedMap[key] === true) return;
          const mr = await apiService.getReturnDeviceMapSummary(ri, d.index);
          const exists = !!(mr && (mr.exists || (mr.data && mr.data.exists)));
          setLearnedMap(prev => ({ ...prev, [key]: exists }));
        } catch {}
      });
    } catch {}
  };

  // Light polling to keep return devices fresh while a return is open
  useEffect(() => {
    if (tab !== 0 || openReturn == null) return;
    const id = setInterval(() => {
      fetchReturnDevices(openReturn).catch(() => {});
    }, 3000);
    return () => clearInterval(id);
  }, [tab, openReturn]);

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

  // Load returns list when navigating to Returns tab
  useEffect(() => {
    if (tab === 1) {
      fetchReturns();
    }
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
    async (payload) => {
      if (tab !== 0) return;
      if (!payload?.event) return;
      // Optimistic handling for bypass; minimal refresh for others
      if (payload.event === 'device_bypass_changed') {
        const rIndex = (typeof payload.return === 'number') ? payload.return : (typeof payload.return_index === 'number' ? payload.return_index : null);
        if (rIndex == null) return;
        setReturnDevices(prev => {
          const list = prev[rIndex];
          if (!Array.isArray(list)) return prev;
          const nextList = list.map(d => (d.index === payload.device_index ? { ...d, isOn: !!payload.on } : d));
          return { ...prev, [rIndex]: nextList };
        });
        return;
      }
      if (payload.event.startsWith('preset_') || payload.event === 'return_device_param_changed' || payload.event === 'device_removed') {
        try {
          const rIndex = (typeof payload.return === 'number') ? payload.return : (typeof payload.return_index === 'number' ? payload.return_index : null);
          if (rIndex != null) {
            await fetchReturnDevices(rIndex);
          } else if (openReturn != null) {
            await fetchReturnDevices(openReturn);
          }
        } catch {}
      }
    },
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

  const content = (
    <>
      <Box sx={{ p: 1 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          variant="fullWidth"
          size="small"
        >
          <Tab icon={<ProjectIcon fontSize="small" />} iconPosition="start" label="Tracks" />
          <Tab icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="Returns" />
          <Tab icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="Master" />
        </Tabs>
      </Box>
      <Divider />

      {/* Project Tab */}
      {tab === 0 && (
        <Box sx={{ p: 2, overflow: 'auto' }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>Tracks</Typography>
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
              {/* Return Tracks removed from Tracks tab; see Returns tab */}
              {false && (
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
                                {openReturn === r.index ? 'Hide' : 'Show'}
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
                                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: 360 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                                      <Tooltip title={d.isOn ? 'On' : 'Off'} placement="top">
                                        <input
                                          type="checkbox"
                                          checked={!!d.isOn}
                                          onChange={async (e) => {
                                            const nextOn = e.target.checked;
                                            // Optimistic UI update
                                            setReturnDevices(prev => {
                                              const list = prev[r.index] || [];
                                              const nextList = list.map(x => (x.index === d.index ? { ...x, isOn: nextOn } : x));
                                              return { ...prev, [r.index]: nextList };
                                            });
                                            try {
                                              await apiService.bypassReturnDevice(r.index, d.index, nextOn);
                                            } catch {
                                              // revert on error
                                              setReturnDevices(prev => {
                                                const list = prev[r.index] || [];
                                                const nextList = list.map(x => (x.index === d.index ? { ...x, isOn: !nextOn } : x));
                                                return { ...prev, [r.index]: nextList };
                                              });
                                            }
                                          }}
                                          style={{ cursor: 'pointer' }}
                                        />
                                      </Tooltip>
                                      <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>{d.name || `Device ${d.index}`}</Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      {learnJobs[`${r.index}:${d.index}`]?.state === 'running' && (
                                        <Typography variant="caption" color="text.secondary">
                                          {Math.round((learnJobs[`${r.index}:${d.index}`].progress / Math.max(1, learnJobs[`${r.index}:${d.index}`].total)) * 100)}%
                                        </Typography>
                                      )}
                                      <Tooltip
                                        title={
                                          learnedMap[`${r.index}:${d.index}`]
                                            ? "Device learned - ready for control"
                                            : "Click to learn device parameters"
                                        }
                                        placement="left"
                                      >
                                        <Box
                                          onClick={async () => {
                                            if (learnedMap[`${r.index}:${d.index}`]) return; // Don't re-learn
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
                                          }}
                                          sx={{
                                            width: 12,
                                            height: 12,
                                            borderRadius: '50%',
                                            backgroundColor: learnedMap[`${r.index}:${d.index}`] ? '#4caf50' : '#f44336',
                                            cursor: learnedMap[`${r.index}:${d.index}`] ? 'default' : 'pointer',
                                            transition: 'all 0.2s',
                                            '&:hover': learnedMap[`${r.index}:${d.index}`] ? {} : {
                                              transform: 'scale(1.3)',
                                              boxShadow: '0 0 8px rgba(244, 67, 54, 0.6)',
                                            }
                                          }}
                                        />
                                      </Tooltip>
                                    </Box>
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
              )}

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
                            <ListItem key={s.index} disableGutters sx={{ py: 0.5 }}>
                              <Box sx={{ width: '100%' }}>
                                <Typography variant="body2" sx={{ mb: 0.5 }}>
                                  {s.name || `Send ${s.index}`}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
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
                                    sx={{ flex: 1 }}
                                  />
                                  <Tooltip title={`${liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB`}>
                                    <Typography variant="caption" color="text.secondary" sx={{ width: 56, textAlign: 'right' }}>
                                      {liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB
                                    </Typography>
                                  </Tooltip>
                                </Box>
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

      {/* Returns Tab */}
      {tab === 1 && (
        <Box sx={{ p: 2, overflow: 'auto' }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>Return Tracks</Typography>
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
                        {openReturn === r.index ? 'Hide' : 'Show'}
                      </Button>
                    </Box>
                  </Box>
                  {openReturn === r.index && (
                    <Box sx={{ mt: 1, pl: 1 }}>
                      {/* Return mixer: Volume & Pan sliders stacked */}
                      <Box sx={{ mb: 1, pr: 2 }}>
                        <Typography variant="caption" color="text.secondary">Volume</Typography>
                        <Slider
                          size="small"
                          value={0.5}
                          min={0}
                          max={1}
                          step={0.005}
                          valueLabelDisplay="auto"
                          valueLabelFormat={(v) => `${liveFloatToDbSend(Number(v)).toFixed(1)} dB`}
                          onChangeCommitted={async (_, val) => {
                            const v = Array.isArray(val) ? val[0] : val;
                            try { await apiService.setReturnMixer(r.index, 'volume', Number(v)); } catch {}
                          }}
                        />
                        <Box sx={{ height: 8 }} />
                        <Typography variant="caption" color="text.secondary">Pan</Typography>
                        <Slider
                          size="small"
                          value={0}
                          min={-1}
                          max={1}
                          step={0.02}
                          valueLabelDisplay="auto"
                          valueLabelFormat={(v) => `${Math.round(Math.abs(Number(v)) * 50)}${Number(v) < 0 ? 'L' : (Number(v) > 0 ? 'R' : '')}`}
                          onChangeCommitted={async (_, val) => {
                            const v = Array.isArray(val) ? val[0] : val;
                            try { await apiService.setReturnMixer(r.index, 'pan', Number(v)); } catch {}
                          }}
                        />
                      </Box>
                      {!returnDevices[r.index] && (
                        <Typography variant="caption" color="text.secondary">Loading devices…</Typography>
                      )}
                      {returnDevices[r.index] && returnDevices[r.index].length === 0 && (
                        <Typography variant="caption" color="text.secondary">No devices</Typography>
                      )}
                      {returnDevices[r.index] && returnDevices[r.index].map((d) => (
                        <Box key={d.index} sx={{ mb: 0.5, pl: 1, pr: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: 360 }}>
                            {/* Left cluster: bypass + name */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                              <Tooltip title={d.isOn ? 'On' : 'Off'} placement="top">
                                <input
                                  type="checkbox"
                                  checked={!!d.isOn}
                                  onChange={async (e) => {
                                    const nextOn = e.target.checked;
                                    setReturnDevices(prev => {
                                      const list = prev[r.index] || [];
                                      const nextList = list.map(x => (x.index === d.index ? { ...x, isOn: nextOn } : x));
                                      return { ...prev, [r.index]: nextList };
                                    });
                                    try { await apiService.bypassReturnDevice(r.index, d.index, nextOn); } catch {}
                                  }}
                                  style={{ cursor: 'pointer' }}
                                />
                              </Tooltip>
                              <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                                {d.name || `Device ${d.index}`}
                              </Typography>
                            </Box>
                            {/* Right cluster: learned LED */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Tooltip
                                title={
                                  learnedMap[`${r.index}:${d.index}`]
                                    ? "Device learned - ready for control"
                                    : "Click to learn device parameters"
                                }
                                placement="left"
                              >
                                <Box
                                  onClick={async () => {
                                    if (learnedMap[`${r.index}:${d.index}`]) return; // Don't re-learn
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
                                  }}
                                  sx={{
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    backgroundColor: learnedMap[`${r.index}:${d.index}`] ? '#4caf50' : '#f44336',
                                    cursor: learnedMap[`${r.index}:${d.index}`] ? 'default' : 'pointer'
                                  }}
                                />
                              </Tooltip>
                            </Box>
                          </Box>
                        </Box>
                      ))}

                      {/* Sends for this Return (name above slider) */}
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Sends</Typography>
                        {!returnSends[r.index] && (
                          <Button size="small" onClick={() => fetchReturnSends(r.index)}>Load Sends</Button>
                        )}
                        {returnSends[r.index] && returnSends[r.index].length === 0 && (
                          <Typography variant="caption" color="text.secondary">No sends</Typography>
                        )}
                        {returnSends[r.index] && returnSends[r.index].length > 0 && (
                          <List dense>
                            {returnSends[r.index].map((s, i) => (
                              <ListItem key={s.index} disableGutters sx={{ py: 0.5 }}>
                                <Box sx={{ width: '100%' }}>
                                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                                    {s.name || `Send ${s.index}`}
                                  </Typography>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
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
                                        setReturnSends(prev => {
                                          const arr = prev[r.index] ? [...prev[r.index]] : [];
                                          arr[i] = { ...arr[i], value: Number(v) };
                                          return { ...prev, [r.index]: arr };
                                        });
                                      }}
                                      onChangeCommitted={async (_, val) => {
                                        const v = Array.isArray(val) ? val[0] : val;
                                        try { await apiService.setReturnSend(r.index, s.index, Number(v)); } catch {}
                                      }}
                                      sx={{ flex: 1 }}
                                    />
                                    <Tooltip title={`${liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB`}>
                                      <Typography variant="caption" color="text.secondary" sx={{ width: 56, textAlign: 'right' }}>
                                        {liveFloatToDbSend(Number(s.value || 0)).toFixed(1)} dB
                                      </Typography>
                                    </Tooltip>
                                  </Box>
                                </Box>
                              </ListItem>
                            ))}
                          </List>
                        )}
                      </Box>
                    </Box>
                  )}
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      )}

      {/* Master Tab */}
      {tab === 2 && (
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>Master</Typography>
          <Typography variant="body2" color="text.secondary">Master controls coming soon.</Typography>
        </Box>
      )}
    </>
  );

  if (variant === 'permanent') {
    return (
      <Box sx={{ width: widthPx, height: '100%', display: 'flex', flexDirection: 'column', borderRight: 1, borderColor: 'divider', overflow: 'hidden' }}>
        {content}
      </Box>
    );
  }

  return (
    <Drawer
      variant="temporary"
      open={open}
      onClose={onClose}
      anchor="left"
      ModalProps={{ keepMounted: true }}
      PaperProps={{ sx: { width: widthPx, boxSizing: 'border-box' } }}
    >
      {content}
    </Drawer>
  );
}
