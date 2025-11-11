import { useEffect, useRef, useState } from 'react';
import { Box, IconButton, TextField, Tooltip, InputAdornment, MenuItem, Select } from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  FiberManualRecord as RecordIcon,
  AvTimer as MetronomeIcon,
  Loop as LoopIcon,
  ArrowBack as BackIcon,
  ArrowForward as FwdIcon
} from '@mui/icons-material';
import { apiService } from '../services/api.js';

export default function TransportBar() {
  const [state, setState] = useState({
    is_playing: false,
    is_recording: false,
    metronome: false,
    tempo: 120,
    time_signature_numerator: 4,
    time_signature_denominator: 4,
    loop_on: false,
    loop_start: 0,
    loop_length: 8,
    current_song_time: 0,
  });
  const [editingTempo, setEditingTempo] = useState(false);
  const [editingTS, setEditingTS] = useState({ num: false, den: false });
  const editingTempoRef = useRef(false);
  const pollIdRef = useRef(null);
  const esRef = useRef(null);
  const refresh = async () => {
    try {
      const r = await apiService.getTransport();
      const d = (r && r.data) || state;
      const round2 = (v) => {
        const n = Number(v);
        return Number.isFinite(n) ? Math.round((n + Number.EPSILON) * 100) / 100 : 0;
      };
      setState({
        ...d,
        // Clamp overly precise numbers to 2 decimals for readability
        current_song_time: round2(d.current_song_time),
        loop_start: round2(d.loop_start),
        loop_length: round2(d.loop_length),
      });
    } catch {}
  };
  useEffect(() => {
    // Initial read
    refresh();
    // Lightweight polling to reflect Live-side changes (bidirectional)
    // Reduced from 1000ms to 3000ms to match Returns tab and reduce server load
    pollIdRef.current = setInterval(() => { if (!editingTempoRef.current) refresh(); }, 3000);
    // Also listen to SSE and refresh on transport_changed events
    try {
      const es = new EventSource(apiService.getEventsURL());
      esRef.current = es;
      es.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          if (payload && payload.event === 'transport_changed') {
            refresh();
          }
        } catch {}
      };
      es.onerror = () => { try { es.close(); } catch {} };
    } catch {}
    return () => {
      if (pollIdRef.current) clearInterval(pollIdRef.current);
      try { if (esRef.current) esRef.current.close(); } catch {}
    };
  }, []);

  const setAction = async (action, value) => {
    try { await apiService.setTransport(action, value); await refresh(); } catch {}
  };

  return (
    <Box sx={{
      display: 'flex', alignItems: 'center', gap: 0.25, px: 0.75, py: 0.25,
      borderBottom: '1px solid', borderColor: 'divider', backgroundColor: 'background.paper',
      position: 'sticky', top: 0, zIndex: 2
    }}>
      <Tooltip title={state.is_playing ? 'Stop' : 'Play'}>
        <IconButton size="small" onClick={() => setAction(state.is_playing ? 'stop' : 'play')} sx={{ p: 0.5 }}>
          {state.is_playing ? <StopIcon fontSize="small" /> : <PlayIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
      <Tooltip title={state.is_recording ? 'Stop Recording' : 'Record'}>
        <IconButton size="small" color={state.is_recording ? 'error' : 'default'} onClick={() => setAction('record')} sx={{ p: 0.5 }}>
          <RecordIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Tooltip title={state.metronome ? 'Metronome Off' : 'Metronome On'}>
        <IconButton size="small" color={state.metronome ? 'primary' : 'default'} onClick={() => setAction('metronome')} sx={{ p: 0.5 }}>
          <MetronomeIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, ml: 0.25 }}>
        <TextField
          size="small"
          type="number"
          value={state.tempo}
          onFocus={() => { setEditingTempo(true); editingTempoRef.current = true; }}
          onChange={(e) => setState((prev) => ({ ...prev, tempo: Number(e.target.value || 0) }))}
          onBlur={() => { setEditingTempo(false); editingTempoRef.current = false; setAction('tempo', Number(state.tempo)); }}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.currentTarget.blur(); } }}
          placeholder="Tempo"
          InputProps={{
            step: 0.5,
            inputProps: { min: 20, max: 999, style: { fontSize: '0.8rem', width: '6ch' } },
            endAdornment: <InputAdornment position="end" sx={{ fontSize: '0.75rem' }}>BPM</InputAdornment>
          }}
          sx={{
            '& .MuiInputBase-root': { fontSize: '0.8rem', height: '26px' },
            '& .MuiInputBase-input': { py: 0.5 }
          }}
        />
      </Box>
      {/* Time Signature (editable) */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, ml: 0.5 }}>
        <Tooltip title="Time Signature Numerator">
          <TextField
            size="small"
            type="number"
            value={state.time_signature_numerator}
            onFocus={() => setEditingTS((p) => ({ ...p, num: true }))}
            onChange={(e) => setState((prev) => ({ ...prev, time_signature_numerator: Number(e.target.value || 4) }))}
            onBlur={() => { setEditingTS((p) => ({ ...p, num: false })); setAction('time_sig_num', Number(state.time_signature_numerator)); }}
            inputProps={{ min: 1, max: 32, style: { fontSize: '0.8rem', width: '3ch' } }}
            sx={{ '& .MuiInputBase-root': { height: '26px' }, '& .MuiInputBase-input': { py: 0.5, textAlign: 'center' } }}
          />
        </Tooltip>
        <Box sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>/</Box>
        <Tooltip title="Time Signature Denominator">
          <Select
            size="small"
            value={state.time_signature_denominator}
            onOpen={() => setEditingTS((p) => ({ ...p, den: true }))}
            onClose={() => setEditingTS((p) => ({ ...p, den: false }))}
            onChange={(e) => { const v = Number(e.target.value); setState((prev) => ({ ...prev, time_signature_denominator: v })); setAction('time_sig_den', v); }}
            sx={{
              '& .MuiSelect-select': { py: 0.2, fontSize: '0.8rem', minWidth: '4ch', textAlign: 'center' },
              height: '26px'
            }}
          >
            {[1, 2, 4, 8, 16, 32].map((d) => (
              <MenuItem key={d} value={d}>{d}</MenuItem>
            ))}
          </Select>
        </Tooltip>
      </Box>

      {/* Playhead controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, ml: 0.5 }}>
        <Tooltip title="Nudge -1 beat">
          <IconButton size="small" onClick={() => setAction('nudge', -1)} sx={{ p: 0.25 }}>
            <BackIcon fontSize="inherit" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Playhead (beats)">
          <TextField
            size="small"
            type="number"
            value={state.current_song_time}
            onChange={(e) => setState((prev) => ({ ...prev, current_song_time: Number(e.target.value || 0) }))}
            onBlur={() => setAction('position', Math.round(Number(state.current_song_time) * 100) / 100)}
            inputProps={{ step: 1, style: { fontSize: '0.8rem', width: '6ch' } }}
            sx={{ '& .MuiInputBase-root': { height: '26px' }, '& .MuiInputBase-input': { py: 0.5, textAlign: 'center' } }}
          />
        </Tooltip>
        <Tooltip title="Nudge +1 beat">
          <IconButton size="small" onClick={() => setAction('nudge', 1)} sx={{ p: 0.25 }}>
            <FwdIcon fontSize="inherit" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Loop controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, ml: 0.5 }}>
        <Tooltip title={state.loop_on ? 'Loop Off' : 'Loop On'}>
          <IconButton size="small" color={state.loop_on ? 'primary' : 'default'} onClick={() => setAction('loop_on', state.loop_on ? 0 : 1)} sx={{ p: 0.25 }}>
            <LoopIcon fontSize="inherit" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Loop Start (beats)">
          <TextField
            size="small"
            type="number"
            value={state.loop_start}
            onChange={(e) => setState((prev) => ({ ...prev, loop_start: Number(e.target.value || 0) }))}
            onBlur={() => setAction('loop_start', Math.round(Number(state.loop_start) * 100) / 100)}
            inputProps={{ step: 1, style: { fontSize: '0.8rem', width: '6ch' } }}
            sx={{ '& .MuiInputBase-root': { height: '26px' }, '& .MuiInputBase-input': { py: 0.5, textAlign: 'center' } }}
          />
        </Tooltip>
        <Tooltip title="Loop Length (beats)">
          <TextField
            size="small"
            type="number"
            value={state.loop_length}
            onChange={(e) => setState((prev) => ({ ...prev, loop_length: Number(e.target.value || 0) }))}
            onBlur={() => setAction('loop_length', Math.round(Number(state.loop_length) * 100) / 100)}
            inputProps={{ step: 1, min: 0, style: { fontSize: '0.8rem', width: '5.5ch' } }}
            sx={{ '& .MuiInputBase-root': { height: '26px' }, '& .MuiInputBase-input': { py: 0.5, textAlign: 'center' } }}
          />
        </Tooltip>
      </Box>
    </Box>
  );
}
