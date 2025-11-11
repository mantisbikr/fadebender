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
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  VolumeOff as VolumeOffIcon,
  Headphones as HeadphonesIcon,
  Audiotrack as TrackIcon,
  CallMerge as ReturnIcon,
  GraphicEq as MasterIcon
} from '@mui/icons-material';
import { apiService } from '../services/api.js';
import { liveFloatToDb, liveFloatToDbSend, dbFromStatus, panLabelFromStatus } from '../utils/volumeUtils.js';
import { useMixerEvents } from '../hooks/useMixerEvents.js';
import TrackRow from './TrackRow.jsx';

function ReturnSendSlider({ send, sendIndex, returnIndex, returnSends, setReturnSends }) {
  const [localVol, setLocalVol] = useState(null);
  const baseVal = (typeof send?.volume === 'number') ? send.volume : ((typeof send?.value === 'number') ? send.value : 0);
  const lastVolRef = useRef(baseVal);
  const currentVol = localVol !== null ? localVol : ((typeof send?.volume === 'number') ? send.volume : ((typeof send?.value === 'number') ? send.value : undefined));
  useEffect(() => {
    if (typeof currentVol === 'number') lastVolRef.current = currentVol;
  }, [currentVol]);
  const displayVol = (typeof currentVol === 'number') ? currentVol : lastVolRef.current;

  return (
    <Box sx={{ mb: 0.5 }}>
      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', mb: 0.3, display: 'block' }}>
        {send?.name || `Send ${sendIndex + 1}`}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Slider
          size="small"
          value={displayVol}
          min={0}
          max={1}
          step={0.005}
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
          onChange={(_, val) => setLocalVol(Array.isArray(val) ? val[0] : val)}
          onChangeCommitted={async (_, val) => {
            const v = Array.isArray(val) ? val[0] : val;
            try {
              await apiService.setReturnSend(returnIndex, send.index, Number(v));
              // Update local cache
              setReturnSends(prev => {
                const list = prev[returnIndex] || [];
                return {
                  ...prev,
                  [returnIndex]: list.map((s, i) => i === sendIndex ? { ...s, volume: Number(v), value: Number(v) } : s)
                };
              });
            } catch {}
            setLocalVol(null);
          }}
          sx={{ flex: 1 }}
        />
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 44, textAlign: 'right' }}>
          {liveFloatToDbSend(Number(displayVol)).toFixed(1)} dB
        </Typography>
      </Box>
    </Box>
  );
}

function ReturnRow({
  returnTrack: r,
  openReturn,
  setOpenReturn,
  returnDevices,
  setReturnDevices,
  learnedMap,
  setLearnedMap,
  setLearnJobs,
  fetchReturnDevices,
  fetchReturnSends,
  fetchReturns,
  returnSends,
  setReturnSends,
  onReturnMixerSet,
}) {
  const [localVol, setLocalVol] = useState(null);
  const [localPan, setLocalPan] = useState(null);
  // Preserve last known values and suppress transient refresh right after commit
  const lastVolRef = useRef(typeof r?.mixer?.volume === 'number' ? r.mixer.volume : 0.5);
  const lastPanRef = useRef(typeof r?.mixer?.pan === 'number' ? r.mixer.pan : 0);
  const volBusyUntilRef = useRef(0);
  const panBusyUntilRef = useRef(0);
  const [sendsExpanded, setSendsExpanded] = useState(false);
  const [routing, setRouting] = useState(null);
  const currentVol = localVol !== null ? localVol : (typeof r.mixer?.volume === 'number' ? r.mixer.volume : undefined);
  const currentPan = localPan !== null ? localPan : (typeof r.mixer?.pan === 'number' ? r.mixer.pan : undefined);
  useEffect(() => {
    const now = Date.now();
    if (typeof currentVol === 'number' && now >= volBusyUntilRef.current) lastVolRef.current = currentVol;
  }, [currentVol]);
  useEffect(() => {
    const now = Date.now();
    if (typeof currentPan === 'number' && now >= panBusyUntilRef.current) lastPanRef.current = currentPan;
  }, [currentPan]);
  const nowTick = Date.now();
  const supVol = nowTick < volBusyUntilRef.current;
  const supPan = nowTick < panBusyUntilRef.current;
  const displayVol = (localVol !== null)
    ? localVol
    : (supVol ? lastVolRef.current : (typeof currentVol === 'number' ? currentVol : lastVolRef.current));
  const displayPan = (localPan !== null)
    ? localPan
    : (supPan ? lastPanRef.current : (typeof currentPan === 'number' ? currentPan : lastPanRef.current));

  return (
    <ListItem sx={{
      display: 'block',
      py: 0.5,
      borderBottom: '1px solid',
      borderColor: 'divider',
      boxShadow: '0 1px 3px rgba(0,0,0,0.12)'
    }}>
      {/* Compact header: name + mute/solo */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
          {r.name || `Return ${r.index}`}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title={r.mixer?.mute ? 'Unmute' : 'Mute'}>
            <IconButton size="small" onClick={async () => {
              try { await apiService.setReturnMixer(r.index, 'mute', r.mixer?.mute ? 0 : 1); fetchReturns({ silent: true }); } catch {}
            }}>
              <VolumeOffIcon fontSize="small" color={r.mixer?.mute ? 'warning' : 'inherit'} />
            </IconButton>
          </Tooltip>
          <Tooltip title={r.mixer?.solo ? 'Unsolo' : 'Solo'}>
            <IconButton size="small" onClick={async () => {
              try { await apiService.setReturnMixer(r.index, 'solo', r.mixer?.solo ? 0 : 1); fetchReturns({ silent: true }); } catch {}
            }}>
              <HeadphonesIcon fontSize="small" color={r.mixer?.solo ? 'success' : 'inherit'} />
            </IconButton>
          </Tooltip>
          <IconButton size="small" onClick={async () => { const next = (openReturn === r.index) ? null : r.index; setOpenReturn(next); if (next != null) { await fetchReturnDevices(next); fetchReturnSends(next); } }}>
            {openReturn === r.index ? <ExpandMoreIcon /> : <ChevronRightIcon />}
          </IconButton>
        </Box>
      </Box>

      {/* Mixer controls: Vol + Pan stacked vertically */}
      <Box sx={{ mb: 0.5 }}>
        {/* Volume */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>Vol</Typography>
          <Slider
            size="small"
            value={displayVol}
            min={0}
            max={1}
            step={0.005}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
            onChange={(_, val) => setLocalVol(Array.isArray(val) ? val[0] : val)}
            onChangeCommitted={async (_, val) => {
              const v = Array.isArray(val) ? val[0] : val;
              try { await apiService.setReturnMixer(r.index, 'volume', Number(v)); } catch {}
              volBusyUntilRef.current = Date.now() + 1000;
              onReturnMixerSet?.(r.index, 'volume', Number(v));
              setTimeout(() => setLocalVol(null), 500);
            }}
            sx={{ flex: 1 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 44, textAlign: 'right' }}>
            {liveFloatToDb(Number(displayVol)).toFixed(1)} dB
          </Typography>
        </Box>

        {/* Pan */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>Pan</Typography>
          <Slider
            size="small"
            value={displayPan}
            min={-1}
            max={1}
            step={0.02}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
            onChange={(_, val) => setLocalPan(Array.isArray(val) ? val[0] : val)}
            onChangeCommitted={async (_, val) => {
              const v = Array.isArray(val) ? val[0] : val;
              try { await apiService.setReturnMixer(r.index, 'pan', Number(v)); } catch {}
              panBusyUntilRef.current = Date.now() + 1000;
              onReturnMixerSet?.(r.index, 'pan', Number(v));
              setTimeout(() => setLocalPan(null), 500);
            }}
            sx={{ flex: 1 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 30, textAlign: 'right' }}>
            {Math.round(Math.abs(Number(displayPan)) * 50)}{Number(displayPan) < 0 ? 'L' : (Number(displayPan) > 0 ? 'R' : '')}
          </Typography>
        </Box>
      </Box>

      {/* Devices - compact list with preset names first */}
      {openReturn === r.index && (
        <Box sx={{ pl: 1, mt: 0.5 }}>
          {/* Routing controls hidden (Chat-only). Keeping state capture but no direct UI for now. */}
          {!returnDevices[r.index] && <Typography variant="caption" color="text.secondary">Loading devices…</Typography>}
          {returnDevices[r.index] && returnDevices[r.index].length === 0 && <Typography variant="caption" color="text.secondary">No devices</Typography>}
          {returnDevices[r.index] && returnDevices[r.index].map((d) => (
            <Box key={d.index} sx={{ mb: 0.3 }}>
              {/* Preset name first */}
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                  {d.name || `Device ${d.index}`}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Tooltip title={d.isOn ? 'On' : 'Off'}>
                    <input
                      type="checkbox"
                      checked={!!d.isOn}
                      onChange={async (e) => {
                        const nextOn = e.target.checked;
                        setReturnDevices(prev => {
                          const list = prev[r.index] || [];
                          return { ...prev, [r.index]: list.map(x => (x.index === d.index ? { ...x, isOn: nextOn } : x)) };
                        });
                        try { await apiService.bypassReturnDevice(r.index, d.index, nextOn); } catch {}
                      }}
                      style={{ cursor: 'pointer' }}
                    />
                  </Tooltip>
                  <Tooltip title={learnedMap[`${r.index}:${d.index}`] ? "Learned" : "Click to learn"} placement="left">
                    <Box
                      onClick={async () => {
                        if (learnedMap[`${r.index}:${d.index}`]) return;
                        try {
                          const st = await apiService.learnReturnDeviceStart(r.index, d.index, 41, 20);
                          const jobId = st?.job_id;
                          if (!jobId) return;
                          setLearnJobs(prev => ({ ...prev, [`${r.index}:${d.index}`]: { jobId, state: 'running', progress: 0, total: 1 } }));
                          const key = `${r.index}:${d.index}`;
                          const poll = async () => {
                            try {
                              const s = await apiService.learnReturnDeviceStatus(jobId);
                              setLearnJobs(prev => ({ ...prev, [key]: { ...(prev[key]||{}), ...s, jobId } }));
                              if (s?.state === 'done') { setLearnedMap(prev => ({ ...prev, [key]: true })); return; }
                              if (s?.state === 'error') return;
                              setTimeout(poll, 400);
                            } catch { setTimeout(poll, 600); }
                          };
                          poll();
                        } catch {}
                      }}
                      sx={{
                        width: 10,
                        height: 10,
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
        </Box>
      )}

      {/* Sends expandable section */}
      <Accordion
        disableGutters
        elevation={0}
        expanded={sendsExpanded}
        onChange={(ev, exp) => {
          try { ev.stopPropagation(); } catch {}
          setSendsExpanded(exp);
          if (exp) {
            // Briefly suppress adopting external mixer updates to avoid visual bounce
            const now = Date.now();
            try {
              volBusyUntilRef.current = Math.max(volBusyUntilRef.current, now + 350);
              panBusyUntilRef.current = Math.max(panBusyUntilRef.current, now + 350);
            } catch {}
            fetchReturnSends(r.index);
          }
        }}
        sx={{
          mt: 0.5,
          border: 'none',
          '&:before': { display: 'none' },
          '&.Mui-expanded': { margin: 0 }
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon fontSize="small" />}
          onClick={(e) => { e.stopPropagation(); }}
          onMouseDown={(e) => { e.stopPropagation(); }}
          sx={{ minHeight: 32, padding: '0 8px', '&.Mui-expanded': { minHeight: 32 } }}
        >
          <Typography variant="caption" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
            Sends {returnSends[r.index] ? `(${returnSends[r.index].length})` : ''}
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 1, pt: 0 }}>
          {!returnSends[r.index] && <Typography variant="caption" color="text.secondary">Loading…</Typography>}
          {returnSends[r.index] && returnSends[r.index].length === 0 && (
            <Typography variant="caption" color="text.secondary">No sends</Typography>
          )}
          {returnSends[r.index] && returnSends[r.index].map((s, i) => (
            <ReturnSendSlider
              key={s.index}
              send={s}
              sendIndex={i}
              returnIndex={r.index}
              returnSends={returnSends}
              setReturnSends={setReturnSends}
            />
          ))}
        </AccordionDetails>
      </Accordion>
    </ListItem>
  );
}

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
  const [masterRefreshMs, setMasterRefreshMs] = useState(800);
  const [trackRefreshMs, setTrackRefreshMs] = useState(1200);
  const [returnsRefreshMs, setReturnsRefreshMs] = useState(3000);
  const [followSelection, setFollowSelection] = useState(true);
  const [expandAllTracks, setExpandAllTracks] = useState(false);
  const [trackSends, setTrackSends] = useState({}); // { [trackIndex]: sends[] }
  const [returns, setReturns] = useState(null);
  const [loadingReturns, setLoadingReturns] = useState(false);
  const [openReturn, setOpenReturn] = useState(null);
  const [returnDevices, setReturnDevices] = useState({}); // { [returnIndex]: devices[] }
  const [returnSends, setReturnSends] = useState({}); // { [returnIndex]: sends[] }
  const [masterStatus, setMasterStatus] = useState(null); // Master track mixer state
  const [expandAllReturns, setExpandAllReturns] = useState(false);
  const [isAdjusting, setIsAdjusting] = useState(false);
  const adjustingUntilRef = useRef(0);
  const trackBusyUntilRef = useRef({}); // { [trackIndex]: ts }
  const returnBusyUntilRef = useRef({}); // { [returnIndex]: ts }
  const masterBusyUntilRef = useRef({}); // { field: ts }
  const trackPendingRef = useRef({}); // { [trackIndex]: { volume?:number, pan?:number } }
  const returnPendingRef = useRef({}); // { [returnIndex]: { volume?:number, pan?:number } }
  const masterPendingRef = useRef({}); // { volume?:number, pan?:number, cue?:number }
  const trackToggleUntilRef = useRef({}); // { [trackIndex]: timestamp }
  const [learnedMap, setLearnedMap] = useState({}); // { `${ri}:${di}`: bool }
  const [learnJobs, setLearnJobs] = useState({}); // { `${ri}:${di}`: { jobId, progress, total, state } }
  const prevOutlineRef = useRef('');
  const inflightReturnFetch = useRef({}); // { [returnIndex]: boolean }
  const lastReturnFetchAt = useRef({}); // { [returnIndex]: number }
  const lastReturnsListAt = useRef(0);
  const MIN_REFRESH_GAP_MS = 800; // debounce poll vs SSE

  const mergePending = (pendingMap, idx, data, fields) => {
    if (!data) return;
    const pending = pendingMap.current[idx];
    if (!pending) return;
    data.mixer = data.mixer || {};
    let cleared = true;
    fields.forEach((field) => {
      if (pending[field] === undefined) return;
      const incoming = data.mixer[field];
      if (incoming != null && Math.abs(Number(incoming) - Number(pending[field])) <= 0.004) {
        delete pending[field];
      } else {
        data.mixer[field] = Number(pending[field]);
      }
      if (pending[field] !== undefined) cleared = false;
    });
    if (cleared) {
      delete pendingMap.current[idx];
    } else {
      pendingMap.current[idx] = pending;
    }
  };

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
      const hasTracks = !!(data && Array.isArray(data.tracks) && data.tracks.length > 0);
      if (!hasTracks) {
        // Avoid clearing UI with empty outline; retry shortly on cold start
        setTimeout(() => { if (tab === 0) fetchOutline(false); }, 600);
        return;
      }
      const nextStr = JSON.stringify(data || {});
      if (nextStr === prevOutlineRef.current) return;
      prevOutlineRef.current = nextStr;
      setOutline(data);
      // Prime per-track statuses in background to avoid blocking initial render
      try {
        setTimeout(async () => {
          const tracks = (data && Array.isArray(data.tracks)) ? data.tracks : [];
          const results = await Promise.all(tracks.map(async (t) => {
            try {
              const r = await apiService.getTrackStatus(t.index);
              return [t.index, (r && r.data) || null];
            } catch { return [t.index, null]; }
          }));
          const map = Object.fromEntries(results.filter((kv) => kv[1] != null));
          Object.entries(map).forEach(([idx, payload]) => mergePending(trackPendingRef, Number(idx), payload, ['volume', 'pan']));
          if (Object.keys(map).length) setRowStatuses((prev) => ({ ...prev, ...map }));
        }, 0);
      } catch {}
      if (followSelection && data && data.selected_track) {
        setSelectedIndex(data.selected_track);
        // Also refresh track status when following selection
        try { const ts = await apiService.getTrackStatus(data.selected_track); setTrackStatus(ts.data || null); } catch {}
        // clear sends cache on selection change; fetch on demand when accordion expands
        setTrackSends({});
      }
    } catch (e) {
      // Keep existing outline on error to avoid flicker/disappear
      // Optionally, we could surface a toast here.
    } finally {
      if (manual) setLoadingOutline(false);
    }
  };

  // Smoothly scroll the selected track into view so expanded controls are visible
  useEffect(() => {
    try {
      if (typeof selectedIndex !== 'number') return;
      if (expandAllTracks) return; // no need when all are expanded
      const el = document.getElementById(`track-item-${selectedIndex}`);
      if (!el) return;
      // Wait for DOM to render expanded content
      requestAnimationFrame(() => {
        try {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
        } catch {}
      });
    } catch {}
  }, [selectedIndex, expandAllTracks]);

  // Smoothly scroll the selected return into view so expanded controls are visible
  useEffect(() => {
    try {
      if (expandAllReturns) return;
      if (openReturn == null) return;
      const el = document.getElementById(`return-item-${openReturn}`);
      if (!el) return;
      requestAnimationFrame(() => {
        try { el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' }); } catch {}
      });
    } catch {}
  }, [openReturn, expandAllReturns]);

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
          if (ui.master_refresh_ms) setMasterRefreshMs(Number(ui.master_refresh_ms));
          if (ui.track_refresh_ms) setTrackRefreshMs(Number(ui.track_refresh_ms));
          if (ui.returns_refresh_ms) setReturnsRefreshMs(Number(ui.returns_refresh_ms));
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

  const fetchTrackSends = async (trackIndex, opts = {}) => {
    const silent = !!opts.silent;
    try {
      const res = await apiService.getTrackSends(trackIndex);
      const sendsRaw = (res && res.data && Array.isArray(res.data.sends)) ? res.data.sends : [];
      const sends = sendsRaw.map(s => ({ ...s, volume: (typeof s.value === 'number') ? s.value : s.volume }));
      setTrackSends(prev => ({ ...prev, [trackIndex]: sends }));
    } catch {
      if (!silent) setTrackSends(prev => ({ ...prev, [trackIndex]: [] }));
    }
  };

  const fetchReturns = async (opts = {}) => {
    const silent = !!opts.silent;
    try {
      const now = Date.now();
      if (silent && now - lastReturnsListAt.current < MIN_REFRESH_GAP_MS) return; // debounce
      if (!silent) setLoadingReturns(true);
      const res = await apiService.getReturnTracks();
      const next = (res && res.data && Array.isArray(res.data.returns)) ? res.data.returns : [];
      lastReturnsListAt.current = now;
      setReturns(prev => {
        if (!Array.isArray(prev) || prev.length === 0) {
          return next.map(r => {
            const copy = { ...r };
            mergePending(returnPendingRef, r.index, copy, ['volume', 'pan']);
            return copy;
          });
        }
        // Reconcile by index; merge mixer fields so UI reflects latest
        const byIndex = Object.fromEntries(prev.map(r => [r.index, r]));
        return next.map(r => {
          const existing = byIndex[r.index];
          if (!existing) {
            const clone = { ...r };
            mergePending(returnPendingRef, r.index, clone, ['volume', 'pan']);
            return clone;
          }
          const merged = { ...existing, ...r, mixer: { ...(existing.mixer || {}), ...(r.mixer || {}) } };
          mergePending(returnPendingRef, r.index, merged, ['volume', 'pan']);
          return merged;
        });
      });
    } catch {
      setReturns([]);
    } finally {
      if (!silent) setLoadingReturns(false);
    }
  };

  const fetchReturnSends = async (ri, opts = {}) => {
    const silent = !!opts.silent;
    try {
      const res = await apiService.getReturnSends(ri);
      const sndsRaw = (res && res.data && Array.isArray(res.data.sends)) ? res.data.sends : [];
      const snds = sndsRaw.map(s => ({ ...s, volume: (typeof s.value === 'number') ? s.value : s.volume }));
      setReturnSends(prev => ({ ...prev, [ri]: snds }));
    } catch {
      if (!silent) setReturnSends(prev => ({ ...prev, [ri]: [] }));
    }
  };

  const fetchReturnDevices = async (ri, opts = {}) => {
    const force = !!opts.force;
    try {
      const now = Date.now();
      const lastAt = lastReturnFetchAt.current[ri] || 0;
      if (!force && now - lastAt < MIN_REFRESH_GAP_MS) return; // debounce
      if (inflightReturnFetch.current[ri]) return; // coalesce
      inflightReturnFetch.current[ri] = true;
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
      setReturnDevices(prev => {
        const prevList = Array.isArray(prev[ri]) ? prev[ri] : [];
        const prevByIdx = Object.fromEntries(prevList.map(x => [x.index, x]));
        const nextList = withState.map(d => {
          const e = prevByIdx[d.index];
          if (e && e.name === d.name && !!e.isOn === !!d.isOn) return e; // preserve reference
          return d;
        });
        return { ...prev, [ri]: nextList };
      });
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
    finally {
      lastReturnFetchAt.current[ri] = Date.now();
      inflightReturnFetch.current[ri] = false;
    }
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
      const now = Date.now();
      if (now < (trackBusyUntilRef.current[idx] || 0)) {
        return rowStatuses[idx] || null;
      }
      const res = await apiService.getTrackStatus(idx);
      const data = res.data || null;
      if (data) mergePending(trackPendingRef, idx, data, ['volume', 'pan']);
      setRowStatuses((prev) => ({ ...prev, [idx]: data }));
      if (selectedIndex === idx) setTrackStatus(data);
      return data;
    } catch {
      return null;
    }
  };

  const handleTrackMixerSet = useCallback((idx, field, value) => {
    const f = String(field || '').toLowerCase();
    const now = Date.now();
    if (f === 'volume' || f === 'pan') {
      // Continuous params: apply busy window and pending merge
      trackBusyUntilRef.current[idx] = now + 800;
      trackPendingRef.current[idx] = { ...(trackPendingRef.current[idx] || {}), [f]: Number(value) };
      setRowStatuses((prev) => {
        const cur = prev[idx] || {};
        const mix = cur.mixer || {};
        return { ...prev, [idx]: { ...cur, mixer: { ...mix, [f]: Number(value) } } };
      });
      if (selectedIndex === idx) {
        setTrackStatus((prev) => prev ? { ...prev, mixer: { ...(prev.mixer || {}), [f]: Number(value) } } : prev);
      }
      return;
    }
    if (f === 'mute' || f === 'solo') {
      // Toggles: update top-level flags immediately; no pending needed
      const boolVal = !!value;
      setRowStatuses((prev) => {
        const cur = prev[idx] || {};
        return { ...prev, [idx]: { ...cur, [f]: boolVal } };
      });
      if (selectedIndex === idx) {
        setTrackStatus((prev) => (prev ? { ...prev, [f]: boolVal } : prev));
      }
      return;
    }
  }, [selectedIndex]);

  const handleReturnMixerSet = useCallback((ri, field, value) => {
    const now = Date.now();
    returnBusyUntilRef.current[ri] = now + 800;
    returnPendingRef.current[ri] = { ...(returnPendingRef.current[ri] || {}), [field]: Number(value) };
    setReturns(prev => {
      const list = Array.isArray(prev) ? prev : [];
      return list.map(x => (x.index === ri ? { ...x, mixer: { ...(x.mixer || {}), [field]: Number(value) } } : x));
    });
  }, []);

  const handleMasterMixerSet = useCallback((field, value) => {
    const now = Date.now();
    masterBusyUntilRef.current[field] = now + 800;
    masterPendingRef.current[field] = Number(value);
    setMasterStatus(prev => ({
      ...(prev || {}),
      mixer: { ...(prev?.mixer || {}), [field]: Number(value) }
    }));
  }, []);

  const fetchMasterStatus = async (opts = {}) => {
    const silent = !!opts.silent;
    const force = !!opts.force;
    try {
      const res = await apiService.getMasterStatus();
      const data = (res && res.data) || null;
      if (data) {
        // Merge pending values unless forcing a fresh read
        if (!force && data.mixer && masterPendingRef.current) {
          ['volume', 'pan', 'cue'].forEach(field => {
            const pending = masterPendingRef.current[field];
            if (pending === undefined) return;
            const incoming = data.mixer[field];
            const now = Date.now();
            const busyUntil = masterBusyUntilRef.current[field] || 0;
            if (now < busyUntil) {
              // Still busy, keep pending value
              data.mixer[field] = Number(pending);
            } else if (incoming != null && Math.abs(Number(incoming) - Number(pending)) <= 0.004) {
              // Converged, clear pending
              delete masterPendingRef.current[field];
            } else {
              // Use pending value
              data.mixer[field] = Number(pending);
            }
          });
        }
        setMasterStatus(data);
      }
    } catch (err) {
      console.error('[fetchMasterStatus] Error:', err);
    }
  };

  useEffect(() => {
    if (tab !== 0) return;
    let mounted = true;
    (async () => { if (mounted) await fetchOutline(true); })();
    return () => { mounted = false; };
  }, [tab]);

  // Load returns list when navigating to Returns tab
  useEffect(() => {
    if (tab === 1) {
      fetchReturns();
    }
  }, [tab]);

  // Load master status when navigating to Master tab
  useEffect(() => {
    if (tab === 2) {
      // Clear any stale pending/busy state so initial values are not shadowed
      try { masterPendingRef.current = {}; } catch {}
      try { masterBusyUntilRef.current = {}; } catch {}
      fetchMasterStatus({ force: true });
    }
  }, [tab]);

  // Poll returns/devices while Returns tab is open to keep names/states fresh
  useEffect(() => {
    if (tab !== 1) return;
    const id = setInterval(() => {
      fetchReturns({ silent: true }).catch(() => {});
      if (openReturn != null) {
        fetchReturnDevices(openReturn).catch(() => {});
      }
    }, Math.max(500, Number(returnsRefreshMs || 3000)));
    return () => clearInterval(id);
  }, [tab, openReturn, returnsRefreshMs]);

  // Poll master status while Master tab is open (disabled when masterRefreshMs === 0)
  useEffect(() => {
    if (tab !== 2) return;
    const intervalMs = Number(masterRefreshMs);
    if (intervalMs === 0) return; // Polling disabled - rely on SSE listeners only
    const id = setInterval(() => {
      fetchMasterStatus({ silent: true }).catch(() => {});
    }, Math.max(200, intervalMs || 800));
    return () => clearInterval(id);
  }, [tab, masterRefreshMs]);

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
      // Accept track SSE regardless of active tab so caches stay fresh.
      if (!payload?.track) return;
      const idx = Number(payload.track);
      // If this is a toggle event, set a short suppression window to avoid mixer jitter
      if (payload.field === 'mute' || payload.field === 'solo') {
        trackToggleUntilRef.current[idx] = Date.now() + 800;
      }
      if (payload.field && payload.value != null) {
        const fld = String(payload.field).toLowerCase();
        // During toggle suppression window, ignore continuous SSE updates to prevent slider wiggle
        if ((fld === 'volume' || fld === 'pan')) {
          const until = trackToggleUntilRef.current[idx] || 0;
          if (Date.now() < until) return;
        }
        handleTrackMixerSet(idx, payload.field, payload.value);
      }
      // Only refresh for continuous fields to avoid jitter after mute/solo
      if (tab === 0 && (payload.field === 'volume' || payload.field === 'pan')) {
        const until = trackToggleUntilRef.current[idx] || 0;
        if (Date.now() < until) return;
        refreshTrackThrottled(idx);
      }
    },
    async (payload) => {
      // Handle track send changes
      if (payload?.event === 'send_changed') {
        const trackIdx = (typeof payload.track === 'number') ? payload.track : (typeof payload.track_index === 'number' ? payload.track_index : null);
        if (trackIdx != null && trackSends[trackIdx]) {
          // Refresh sends if this track's sends accordion is expanded
          await fetchTrackSends(trackIdx, { silent: true });
        }
        return;
      }
      if (tab === 0) { fetchOutline(false); }
    },
    async (payload) => {
      // Handle return events on Returns tab as well, and master events on Master tab
      if (tab !== 0 && tab !== 1 && tab !== 2) return;
      if (!payload?.event) return;
      // Ignore master SSE to avoid snap-back; rely on polling-only for Master
      if (payload.event === 'master_mixer_changed') {
        return;
      }
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
      // Handle return-level changes via SSE
      if (payload.event === 'return_mixer_changed') {
        const rIndex = (typeof payload.return === 'number') ? payload.return : (typeof payload.return_index === 'number' ? payload.return_index : null);
        if (rIndex != null && payload.field && payload.value != null) {
          handleReturnMixerSet(Number(rIndex), payload.field, payload.value);
        }
        return;
      }
      if (payload.event === 'return_send_changed' || payload.event === 'return_routing_changed') {
        try {
          await fetchReturns({ silent: true });
          const rIndex = (typeof payload.return === 'number') ? payload.return : (typeof payload.return_index === 'number' ? payload.return_index : null);
          if (rIndex != null && openReturn === rIndex) {
            await fetchReturnDevices(rIndex, { force: true });
            await fetchReturnSends(rIndex, { silent: true });
          }
        } catch {}
        return;
      }
      if (payload.event.startsWith('preset_') || payload.event === 'return_device_param_changed' || payload.event === 'device_removed') {
        try {
          const rIndex = (typeof payload.return === 'number') ? payload.return : (typeof payload.return_index === 'number' ? payload.return_index : null);
          if (rIndex != null) {
            await fetchReturnDevices(rIndex, { force: true });
          } else if (openReturn != null) {
            await fetchReturnDevices(openReturn, { force: true });
          }
        } catch {}
      }
    },
    // Enable SSE on Tracks, Returns, and Master tabs
    tab === 0 || tab === 1 || tab === 2
  );

  // Auto-refresh outline and selected track status every 5s when Project tab is active
  useEffect(() => {
    if (tab !== 0 || !autoRefresh) return;
    const id = setInterval(() => {
      const now = Date.now();
      if (now < adjustingUntilRef.current || isAdjusting) return; // pause during active adjustments
      fetchOutline(false);
      if (selectedIndex) {
        apiService.getTrackStatus(selectedIndex).then((ts) => setTrackStatus(ts.data || null)).catch(() => {});
      }
    }, refreshInterval);
    return () => clearInterval(id);
  }, [tab, autoRefresh, selectedIndex, followSelection, refreshInterval]);

  // Poll selected track status while Tracks tab is open (fallback when SSE not flowing)
  useEffect(() => {
    if (tab !== 0) return;
    const id = setInterval(() => {
      const now = Date.now();
      if (now < adjustingUntilRef.current || isAdjusting) return; // avoid during user drag
      if (selectedIndex) {
        // Suppress polling immediately after toggles to avoid jitter
        const until = trackToggleUntilRef.current[selectedIndex] || 0;
        if (now < until) return;
        refreshTrack(selectedIndex).catch(() => {});
      }
    }, Math.max(300, Number(trackRefreshMs || 1200)));
    return () => clearInterval(id);
  }, [tab, selectedIndex, isAdjusting, trackRefreshMs]);

  // Poll track sends when accordions are expanded
  useEffect(() => {
    if (tab !== 0) return;
    const expandedTracks = Object.keys(trackSends).map(Number);
    if (expandedTracks.length === 0) return;

    const id = setInterval(() => {
      const now = Date.now();
      if (now < adjustingUntilRef.current || isAdjusting) return;
      expandedTracks.forEach(trackIdx => {
        fetchTrackSends(trackIdx, { silent: true });
      });
    }, sendsFastRefreshMs);
    return () => clearInterval(id);
  }, [tab, trackSends, isAdjusting, sendsFastRefreshMs]);

  // Poll return sends when accordions are expanded
  useEffect(() => {
    if (tab !== 1) return;
    const expandedReturns = Object.keys(returnSends).map(Number);
    if (expandedReturns.length === 0) return;

    const id = setInterval(() => {
      expandedReturns.forEach(returnIdx => {
        fetchReturnSends(returnIdx, { silent: true });
      });
    }, sendsFastRefreshMs);
    return () => clearInterval(id);
  }, [tab, returnSends, sendsFastRefreshMs]);

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
          <Tab icon={<TrackIcon fontSize="small" />} iconPosition="start" label="Tracks" />
          <Tab icon={<ReturnIcon fontSize="small" />} iconPosition="start" label="Returns" />
          <Tab icon={<MasterIcon fontSize="small" />} iconPosition="start" label="Master" />
        </Tabs>
      </Box>
      <Divider />

      {/* Project Tab */}
      {tab === 0 && (
        <Box sx={{ p: 2, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle1">Tracks</Typography>
            <Button size="small" onClick={() => setExpandAllTracks(v => !v)}>
              {expandAllTracks ? 'Collapse all' : 'Expand all'}
            </Button>
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

              {/* Compact list of tracks with inline expansion for selected */}
              <List dense>
                {outline.tracks.map((t) => {
                  const st = getStatus(t.index) || {};
                  return (
                    <Box key={t.index} id={`track-item-${t.index}`} component="li" sx={{ listStyle: 'none', m: 0, p: 0 }}>
                      <ListItem
                        selected={selectedIndex === t.index}
                        onClick={() => {
                          setSelectedIndex(t.index);
                          refreshTrack(t.index);
                        }}
                        sx={{
                          cursor: 'pointer',
                          py: 0.5,
                          borderBottom: '1px solid',
                          borderColor: 'divider',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: selectedIndex === t.index ? 600 : 400, fontSize: '0.875rem' }}>
                          {t.index}. {t.name}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            {String(t.type || '').toLowerCase()}
                          </Typography>
                          <Tooltip title={st?.mute ? 'Unmute' : 'Mute'}>
                            <IconButton size="small" onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                const cur = getStatus(t.index) || st || {};
                                const next = cur?.mute ? 0 : 1;
                                const now = Date.now();
                                trackToggleUntilRef.current[t.index] = now + 800;
                                await apiService.setMixer(t.index, 'mute', next);
                              } catch {}
                            }}>
                              <VolumeOffIcon fontSize="small" color={st?.mute ? 'warning' : 'inherit'} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={st?.solo ? 'Unsolo' : 'Solo'}>
                            <IconButton size="small" onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                const cur = getStatus(t.index) || st || {};
                                const next = cur?.solo ? 0 : 1;
                                const now = Date.now();
                                trackToggleUntilRef.current[t.index] = now + 800;
                                await apiService.setMixer(t.index, 'solo', next);
                              } catch {}
                            }}>
                              <HeadphonesIcon fontSize="small" color={st?.solo ? 'success' : 'inherit'} />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </ListItem>
                      {(expandAllTracks || selectedIndex === t.index) && (
                        <Box sx={{ mt: 0.5, pl: 1, pr: 0.5 }}>
                          <TrackRow
                            track={t}
                            isSelected={true}
                            getStatus={getStatus}
                            refreshTrack={refreshTrack}
                            setSelectedIndex={setSelectedIndex}
                            onSetDraft={onSetDraft}
                            onHoverPrime={ensureRowStatus}
                            sends={trackSends}
                            setSends={setTrackSends}
                            fetchSends={fetchTrackSends}
                            onAdjustStart={(idx) => {
                              setIsAdjusting(true);
                              const now = Date.now();
                              adjustingUntilRef.current = now + 600;
                              trackBusyUntilRef.current[idx] = now + 1000;
                            }}
                            onAdjustEnd={(idx) => { adjustingUntilRef.current = Date.now() + 400; setTimeout(() => setIsAdjusting(false), 420); }}
                            onAdjustSet={(idx, field, value) => {
                              trackBusyUntilRef.current[idx] = Date.now() + 1000;
                              trackPendingRef.current[idx] = { ...(trackPendingRef.current[idx] || {}), [field]: Number(value) };
                              setRowStatuses((prev) => {
                                const cur = prev[idx] || {};
                                const mix = cur.mixer || {};
                                return { ...prev, [idx]: { ...cur, mixer: { ...mix, [field]: Number(value) } } };
                              });
                            }}
                            onToggleStart={(idx, field) => {
                              const now = Date.now();
                              trackToggleUntilRef.current[idx] = now + 800;
                            }}
                          />
                        </Box>
                      )}
                    </Box>
                  );
                })}
              </List>
            </>
          )}
        </Box>
      )}

      {/* Returns Tab */}
      {tab === 1 && (
        <Box sx={{ p: 2, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle1">Return Tracks</Typography>
            <Button size="small" onClick={() => setExpandAllReturns(v => !v)}>
              {expandAllReturns ? 'Collapse all' : 'Expand all'}
            </Button>
          </Box>
          {loadingReturns && (
            <Typography variant="body2" color="text.secondary">Loading…</Typography>
          )}
          {!loadingReturns && (!returns || returns.length === 0) && (
            <Typography variant="body2" color="text.secondary">No returns</Typography>
          )}
          {!loadingReturns && returns && returns.length > 0 && (
            <List dense>
              {returns.map((r) => (
                <Box key={r.index} id={`return-item-${r.index}`} component="li" sx={{ listStyle: 'none', m: 0, p: 0 }}>
                  <ListItem
                    onClick={async () => {
                      const next = (openReturn === r.index) ? null : r.index;
                      setOpenReturn(next);
                      if (next != null) { await fetchReturnDevices(next); fetchReturnSends(next); }
                    }}
                    sx={{
                      cursor: 'pointer',
                      py: 0.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <Typography variant="body2" sx={{ fontSize: '0.875rem', fontWeight: openReturn === r.index ? 600 : 400 }}>
                      {r.name || `Return ${r.index}`}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Tooltip title={r.mixer?.mute ? 'Unmute' : 'Mute'}>
                        <IconButton size="small" onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const nextVal = r.mixer?.mute ? 0 : 1;
                            await apiService.setReturnMixer(r.index, 'mute', nextVal);
                            setReturns(prev => {
                              const list = Array.isArray(prev) ? prev : [];
                              return list.map(x => (x.index === r.index ? { ...x, mixer: { ...(x.mixer || {}), mute: !!nextVal } } : x));
                            });
                          } catch {}
                        }}>
                          <VolumeOffIcon fontSize="small" color={r.mixer?.mute ? 'warning' : 'inherit'} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={r.mixer?.solo ? 'Unsolo' : 'Solo'}>
                        <IconButton size="small" onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const nextVal = r.mixer?.solo ? 0 : 1;
                            await apiService.setReturnMixer(r.index, 'solo', nextVal);
                            setReturns(prev => {
                              const list = Array.isArray(prev) ? prev : [];
                              return list.map(x => (x.index === r.index ? { ...x, mixer: { ...(x.mixer || {}), solo: !!nextVal } } : x));
                            });
                          } catch {}
                        }}>
                          <HeadphonesIcon fontSize="small" color={r.mixer?.solo ? 'success' : 'inherit'} />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  {(expandAllReturns || openReturn === r.index) && (
                    <Box sx={{ mt: 0.5, pl: 1, pr: 0.5 }}>
                      <ReturnRow
                        returnTrack={r}
                        openReturn={openReturn}
                        setOpenReturn={setOpenReturn}
                        returnDevices={returnDevices}
                        setReturnDevices={setReturnDevices}
                        learnedMap={learnedMap}
                        setLearnedMap={setLearnedMap}
                        setLearnJobs={setLearnJobs}
                        fetchReturnDevices={fetchReturnDevices}
                        fetchReturnSends={fetchReturnSends}
                        fetchReturns={fetchReturns}
                        returnSends={returnSends}
                        setReturnSends={setReturnSends}
                        onReturnMixerSet={(idx, field, value) => {
                          const now = Date.now();
                          returnBusyUntilRef.current[idx] = now + 1000;
                          returnPendingRef.current[idx] = { ...(returnPendingRef.current[idx] || {}), [field]: Number(value) };
                          setReturns(prev => {
                            const list = Array.isArray(prev) ? prev : [];
                            return list.map(x => (x.index === idx ? { ...x, mixer: { ...(x.mixer || {}), [field]: Number(value) } } : x));
                          });
                        }}
                      />
                    </Box>
                  )}
                </Box>
              ))}
            </List>
          )}
        </Box>
      )}

      {/* Master Tab */}
      {tab === 2 && (
        <MasterPanel
          masterStatus={masterStatus}
          onMasterMixerSet={handleMasterMixerSet}
          masterBusyUntilRef={masterBusyUntilRef}
        />
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

function MasterPanel({ masterStatus: m, onMasterMixerSet, masterBusyUntilRef }) {
  // ALL HOOKS MUST BE CALLED BEFORE ANY CONDITIONAL RENDERING
  const [localVol, setLocalVol] = useState(null);
  const [localPan, setLocalPan] = useState(null);
  const [localCue, setLocalCue] = useState(null);

  // Preserve last known values and suppress transient refresh right after commit
  // CRITICAL: Initialize with simple fallbacks, NOT with prop expressions (useRef only evaluates once!)
  const lastVolRef = useRef(0.85);
  const lastPanRef = useRef(0);
  const lastCueRef = useRef(0);
  const seededRef = useRef(false);

  // Require volume to be numeric before showing sliders (avoid default 0.85)
  const ready = (typeof m?.mixer?.volume === 'number');

  const currentVol = localVol !== null ? localVol : (typeof m?.mixer?.volume === 'number' ? m.mixer.volume : undefined);
  const currentPan = localPan !== null ? localPan : (typeof m?.mixer?.pan === 'number' ? m.mixer.pan : undefined);
  const currentCue = localCue !== null ? localCue : (typeof m?.mixer?.cue === 'number' ? m.mixer.cue : undefined);

  // Seed once from initial status (only when volume is present)
  useEffect(() => {
    if (seededRef.current) return;
    const vOK = typeof m?.mixer?.volume === 'number';
    if (vOK) {
      lastVolRef.current = Number(m.mixer.volume);
      if (typeof m?.mixer?.pan === 'number') lastPanRef.current = Number(m.mixer.pan);
      if (typeof m?.mixer?.cue === 'number') lastCueRef.current = Number(m.mixer.cue);
      seededRef.current = true;
    }
  }, [m]);

  // Update refs when data arrives or changes (only if not busy)
  useEffect(() => {
    const now = Date.now();
    if (typeof currentVol === 'number' && now >= (masterBusyUntilRef.current?.volume || 0)) {
      lastVolRef.current = currentVol;
    }
  }, [currentVol, masterBusyUntilRef]);

  useEffect(() => {
    const now = Date.now();
    if (typeof currentPan === 'number' && now >= (masterBusyUntilRef.current?.pan || 0)) {
      lastPanRef.current = currentPan;
    }
  }, [currentPan, masterBusyUntilRef]);

  useEffect(() => {
    const now = Date.now();
    if (typeof currentCue === 'number' && now >= (masterBusyUntilRef.current?.cue || 0)) {
      lastCueRef.current = currentCue;
    }
  }, [currentCue, masterBusyUntilRef]);

  const nowTick = Date.now();
  const supVol = nowTick < (masterBusyUntilRef.current?.volume || 0);
  const supPan = nowTick < (masterBusyUntilRef.current?.pan || 0);
  const supCue = nowTick < (masterBusyUntilRef.current?.cue || 0);

  // On first paint after status arrives, bypass suppression to show Live values exactly
  const initialMode = !seededRef.current;
  const displayVol = (localVol !== null)
    ? localVol
    : (initialMode
      ? (typeof currentVol === 'number' ? currentVol : lastVolRef.current)
      : (supVol ? lastVolRef.current : (typeof currentVol === 'number' ? currentVol : lastVolRef.current)));
  const displayPan = (localPan !== null)
    ? localPan
    : (initialMode
      ? (typeof currentPan === 'number' ? currentPan : lastPanRef.current)
      : (supPan ? lastPanRef.current : (typeof currentPan === 'number' ? currentPan : lastPanRef.current)));
  const displayCue = (localCue !== null)
    ? localCue
    : (initialMode
      ? (typeof currentCue === 'number' ? currentCue : lastCueRef.current)
      : (supCue ? lastCueRef.current : (typeof currentCue === 'number' ? currentCue : lastCueRef.current)));

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>Master</Typography>
      {!ready ? (
        <Typography variant="body2" color="text.secondary">Loading…</Typography>
      ) : (
        <>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 22 }}>Cue</Typography>
            <Slider size="small" value={displayCue} min={0} max={1} step={0.005}
              onChange={(_, v) => setLocalCue(Array.isArray(v) ? v[0] : v)}
              onChangeCommitted={async (_, v) => {
                const x = Array.isArray(v) ? v[0] : v;
                try {
                  await apiService.setMasterMixer('cue', Number(x));
                } catch {}
                onMasterMixerSet?.('cue', Number(x));
                setTimeout(() => setLocalCue(null), 500);
              }}
              sx={{ flex: 1 }} />
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 44, textAlign: 'right' }}>{liveFloatToDb(Number(displayCue)).toFixed(1)} dB</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 22 }}>Vol</Typography>
            <Slider size="small" value={displayVol} min={0} max={1} step={0.005}
              onChange={(_, v) => setLocalVol(Array.isArray(v) ? v[0] : v)}
              onChangeCommitted={async (_, v) => {
                const x = Array.isArray(v) ? v[0] : v;
                try {
                  await apiService.setMasterMixer('volume', Number(x));
                } catch {}
                onMasterMixerSet?.('volume', Number(x));
                setTimeout(() => setLocalVol(null), 500);
              }}
              sx={{ flex: 1 }} />
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 44, textAlign: 'right' }}>{liveFloatToDb(Number(displayVol)).toFixed(1)} dB</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 22 }}>Pan</Typography>
            <Slider size="small" value={displayPan} min={-1} max={1} step={0.02}
              onChange={(_, v) => setLocalPan(Array.isArray(v) ? v[0] : v)}
              onChangeCommitted={async (_, v) => {
                const x = Array.isArray(v) ? v[0] : v;
                try {
                  await apiService.setMasterMixer('pan', Number(x));
                } catch {}
                onMasterMixerSet?.('pan', Number(x));
                setTimeout(() => setLocalPan(null), 500);
              }}
              sx={{ flex: 1 }} />
        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 30, textAlign: 'right' }}>{Math.round(Math.abs(Number(displayPan)) * 50)}{Number(displayPan) < 0 ? 'L' : (Number(displayPan) > 0 ? 'R' : '')}</Typography>
          </Box>

          {/* Devices (minimal list) */}
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>Devices</Typography>
            <MasterDevicesList />
          </Box>
        </>
      )}
    </Box>
  );
}

function MasterDevicesList() {
  const [devices, setDevices] = useState(null);
  return (
    <Box>
      {!devices && (
        <Typography variant="caption" color="text.secondary">(tap to load)</Typography>
      )}
      <Box sx={{ mt: 0.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, cursor: 'pointer' }} onClick={async () => {
          try { const r = await apiService.getMasterDevices(); setDevices((r && r.data && r.data.devices) || []); } catch {}
        }}>Load devices</Typography>
        {Array.isArray(devices) && devices.length > 0 && devices.map(d => (
          <Typography key={d.index} variant="body2" sx={{ display: 'block', fontWeight: 500 }}>{d.name}</Typography>
        ))}
      </Box>
    </Box>
  );
}
