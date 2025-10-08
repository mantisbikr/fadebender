import { useEffect, useRef, useState } from 'react';
import { Box, IconButton, TextField, Tooltip, InputAdornment } from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  FiberManualRecord as RecordIcon,
  AvTimer as MetronomeIcon
} from '@mui/icons-material';
import { apiService } from '../services/api.js';

export default function TransportBar() {
  const [state, setState] = useState({ is_playing: false, is_recording: false, metronome: false, tempo: 120 });
  const [editingTempo, setEditingTempo] = useState(false);
  const editingTempoRef = useRef(false);
  const pollIdRef = useRef(null);
  const esRef = useRef(null);
  const refresh = async () => {
    try { const r = await apiService.getTransport(); setState((r && r.data) || state); } catch {}
  };
  useEffect(() => {
    // Initial read
    refresh();
    // Lightweight polling to reflect Live-side changes (bidirectional)
    pollIdRef.current = setInterval(() => { if (!editingTempoRef.current) refresh(); }, 1000);
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
      display: 'flex', alignItems: 'center', gap: 1, px: 1.5, py: 1,
      borderBottom: '1px solid', borderColor: 'divider', backgroundColor: 'background.paper',
      position: 'sticky', top: 0, zIndex: 2
    }}>
      <Tooltip title={state.is_playing ? 'Stop' : 'Play'}>
        <IconButton size="small" onClick={() => setAction(state.is_playing ? 'stop' : 'play')}>
          {state.is_playing ? <StopIcon /> : <PlayIcon />}
        </IconButton>
      </Tooltip>
      <Tooltip title={state.is_recording ? 'Stop Recording' : 'Record'}>
        <IconButton size="small" color={state.is_recording ? 'error' : 'default'} onClick={() => setAction('record')}>
          <RecordIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title={state.metronome ? 'Metronome Off' : 'Metronome On'}>
        <IconButton size="small" color={state.metronome ? 'primary' : 'default'} onClick={() => setAction('metronome')}>
          <MetronomeIcon />
        </IconButton>
      </Tooltip>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
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
            inputProps: { min: 20, max: 999 },
            endAdornment: <InputAdornment position="end">BPM</InputAdornment>
          }}
        />
      </Box>
    </Box>
  );
}
