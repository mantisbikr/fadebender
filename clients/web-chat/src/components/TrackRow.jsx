import { useRef, useState, useEffect } from 'react';
import {
  ListItem,
  Box,
  Tooltip,
  IconButton,
  Slider,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  VolumeOff as VolumeOffIcon,
  Headphones as HeadphonesIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { liveFloatToDb, liveFloatToDbSend } from '../utils/volumeUtils.js';
import { apiService } from '../services/api.js';

function TrackSendSlider({ send, sendIndex, trackIndex, sends, setSends }) {
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
              await apiService.setSend(trackIndex, send.index, Number(v));
              // Update local cache
              setSends(prev => {
                const list = prev[trackIndex] || [];
                return {
                  ...prev,
                  [trackIndex]: list.map((s, i) => i === sendIndex ? { ...s, volume: Number(v), value: Number(v) } : s)
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

export default function TrackRow({
  track,
  isSelected,
  getStatus,
  refreshTrack,
  setSelectedIndex,
  onSetDraft,
  onHoverPrime,
  sends,
  setSends,
  fetchSends,
  onAdjustStart,
  onAdjustEnd,
  onAdjustSet,
  onToggleStart,
}) {
  const t = track;
  const status = getStatus(t.index);

  // Local state for live slider feedback
  const [localVolume, setLocalVolume] = useState(null);
  const [localPan, setLocalPan] = useState(null);
  const [sendsExpanded, setSendsExpanded] = useState(false);
  const [devices, setDevices] = useState(null);
  const [devicesOpen, setDevicesOpen] = useState(false);

  // Preserve last known values to avoid slider jumps during refresh re-renders
  const lastVolRef = useRef(typeof status?.mixer?.volume === 'number' ? status.mixer.volume : 0.5);
  const lastPanRef = useRef(typeof status?.mixer?.pan === 'number' ? status.mixer.pan : 0);
  const currentVolume = localVolume !== null ? localVolume : (typeof status?.mixer?.volume === 'number' ? status.mixer.volume : undefined);
  const currentPan = localPan !== null ? localPan : (typeof status?.mixer?.pan === 'number' ? status.mixer.pan : undefined);
  // Suppress adopting transient refreshes for a short window after user commit
  const volBusyUntilRef = useRef(0);
  const panBusyUntilRef = useRef(0);
  useEffect(() => {
    const now = Date.now();
    if (typeof currentVolume === 'number' && now >= volBusyUntilRef.current) {
      lastVolRef.current = currentVolume;
    }
  }, [currentVolume]);
  useEffect(() => {
    const now = Date.now();
    if (typeof currentPan === 'number' && now >= panBusyUntilRef.current) {
      lastPanRef.current = currentPan;
    }
  }, [currentPan]);
  const nowTick = Date.now();
  const supVol = nowTick < volBusyUntilRef.current;
  const supPan = nowTick < panBusyUntilRef.current;
  const displayVol = (localVolume !== null)
    ? localVolume
    : (supVol
      ? lastVolRef.current
      : (typeof currentVolume === 'number' ? currentVolume : lastVolRef.current));
  const displayPan = (localPan !== null)
    ? localPan
    : (supPan
      ? lastPanRef.current
      : (typeof currentPan === 'number' ? currentPan : lastPanRef.current));

  return (
    <ListItem
      key={t.index}
      selected={isSelected}
      onClick={() => { setSelectedIndex(t.index); refreshTrack(t.index); }}
      onMouseEnter={() => { onHoverPrime?.(t.index); }}
      sx={{
        cursor: 'pointer',
        py: 0.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
        display: 'block'
      }}
    >
      {/* Header with track name and mute/solo icons */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 0.5 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" sx={{ fontWeight: isSelected ? 600 : 400, fontSize: '0.875rem' }}>
            {t.index}. {t.name}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
            {t.type}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
          <Tooltip title={status?.mute ? 'Unmute' : 'Mute'}>
            <IconButton size="small" onClick={async (e) => {
              e.stopPropagation();
              try {
                if (!isSelected) setSelectedIndex(t.index);
                const cur = getStatus(t.index) || status || {};
                try { onToggleStart?.(t.index, 'mute'); } catch {}
                await apiService.setMixer(t.index, 'mute', cur?.mute ? 0 : 1);
                // Avoid immediate refresh; SSE will update promptly
              } catch {}
            }}>
              <VolumeOffIcon fontSize="small" color={status?.mute ? 'warning' : 'inherit'} />
            </IconButton>
          </Tooltip>
          <Tooltip title={status?.solo ? 'Unsolo' : 'Solo'}>
            <IconButton size="small" onClick={async (e) => {
              e.stopPropagation();
              try {
                if (!isSelected) setSelectedIndex(t.index);
                const cur = getStatus(t.index) || status || {};
                try { onToggleStart?.(t.index, 'solo'); } catch {}
                await apiService.setMixer(t.index, 'solo', cur?.solo ? 0 : 1);
                // Avoid immediate refresh; SSE will update promptly
              } catch {}
            }}>
              <HeadphonesIcon fontSize="small" color={status?.solo ? 'success' : 'inherit'} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box sx={{ width: '100%' }}>

        {/* Sliders stacked vertically below track name */}
        <Box sx={{ mt: 0.5 }}>
          {/* Volume */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>
              Vol
            </Typography>
            <Slider
              size="small"
              value={displayVol}
              min={0}
              max={1}
              step={0.005}
              onMouseDown={(e) => { e.stopPropagation(); try { onAdjustStart?.(t.index); } catch {} }}
              onClick={(e) => e.stopPropagation()}
              onChange={(_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                setLocalVolume(v);
              }}
              onChangeCommitted={async (_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                try {
                  await apiService.setMixer(t.index, 'volume', Number(v));
                } catch {}
                volBusyUntilRef.current = Date.now() + 350; // small suppression window
                setTimeout(() => setLocalVolume(null), 500);
                try { onAdjustEnd?.(t.index); } catch {}
                try { onAdjustSet?.(t.index, 'volume', Number(v)); } catch {}
              }}
              sx={{ flex: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 44, textAlign: 'right' }}>
              {liveFloatToDb(Number(displayVol)).toFixed(1)} dB
            </Typography>
          </Box>

          {/* Pan */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>
              Pan
            </Typography>
            <Slider
              size="small"
              value={displayPan}
              min={-1}
              max={1}
              step={0.02}
              onMouseDown={(e) => { e.stopPropagation(); try { onAdjustStart?.(t.index); } catch {} }}
              onClick={(e) => e.stopPropagation()}
              onChange={(_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                setLocalPan(v);
              }}
              onChangeCommitted={async (_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                try {
                  await apiService.setMixer(t.index, 'pan', Number(v));
                } catch {}
                panBusyUntilRef.current = Date.now() + 350;
                setTimeout(() => setLocalPan(null), 500);
                try { onAdjustEnd?.(t.index); } catch {}
                try { onAdjustSet?.(t.index, 'pan', Number(v)); } catch {}
              }}
              sx={{ flex: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 30, textAlign: 'right' }}>
              {Math.round(Math.abs(Number(displayPan)) * 50)}{Number(displayPan) < 0 ? 'L' : (Number(displayPan) > 0 ? 'R' : '')}
            </Typography>
          </Box>
        </Box>

        {/* Devices (expand on demand, filter to effects kinds) */}
        <Box sx={{ mt: 0.5 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, cursor: 'pointer' }}
            onClick={async (e) => {
              e.stopPropagation();
              const next = !devicesOpen;
              setDevicesOpen(next);
              if (next && devices == null) {
                try { const r = await apiService.getTrackDevices(t.index); setDevices((r && r.data && r.data.devices) || []); } catch {}
              }
            }}>
            {devicesOpen ? '▾ Devices' : '▸ Devices'}
          </Typography>
          {devicesOpen && Array.isArray(devices) && devices
            .filter(d => (
              d.kind === 'audio_effect' || d.kind === 'midi_effect' ||
              (d.kind === 'plugin' && (t.type === 'audio')) ||
              (d.kind === 'unknown' && (t.type === 'audio'))
            ))
            .map(d => (
              <Typography key={d.index} variant="body2" sx={{ display: 'block', fontWeight: 500 }}>{d.name}</Typography>
            ))}
          {devicesOpen && Array.isArray(devices) && devices.filter(d => (
            d.kind === 'audio_effect' || d.kind === 'midi_effect' ||
            (d.kind === 'plugin' && (t.type === 'audio')) ||
            (d.kind === 'unknown' && (t.type === 'audio'))
          )).length === 0 && (
            <Typography variant="caption" color="text.secondary">No effects</Typography>
          )}
        </Box>
      </Box>

      {/* Sends expandable section - full width */}
      <Accordion
        disableGutters
        elevation={0}
        expanded={sendsExpanded}
        onChange={(ev, exp) => {
          try { ev.stopPropagation(); } catch {}
          setSendsExpanded(exp);
          if (exp) {
            // Briefly suppress adopting external mixer updates to avoid visual bounce when section opens
            const now = Date.now();
            volBusyUntilRef.current = Math.max(volBusyUntilRef.current, now + 350);
            panBusyUntilRef.current = Math.max(panBusyUntilRef.current, now + 350);
            fetchSends?.(t.index);
          }
        }}
        sx={{
          width: '100%',
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
            Sends {sends?.[t.index] ? `(${sends[t.index].length})` : ''}
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 1, pt: 0 }}>
          {!sends?.[t.index] && <Typography variant="caption" color="text.secondary">Loading…</Typography>}
          {sends?.[t.index] && sends[t.index].length === 0 && (
            <Typography variant="caption" color="text.secondary">No sends</Typography>
          )}
          {sends?.[t.index] && sends[t.index].map((s, i) => (
            <TrackSendSlider
              key={s.index}
              send={s}
              sendIndex={i}
              trackIndex={t.index}
              sends={sends}
              setSends={setSends}
            />
          ))}
        </AccordionDetails>
      </Accordion>
    </ListItem>
  );
}
