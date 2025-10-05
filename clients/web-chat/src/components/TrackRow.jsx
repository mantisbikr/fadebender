import { useState } from 'react';
import {
  ListItem,
  Box,
  Tooltip,
  IconButton,
  Slider,
  Typography,
} from '@mui/material';
import {
  VolumeOff as VolumeOffIcon,
  Headphones as HeadphonesIcon,
} from '@mui/icons-material';
import { liveFloatToDb } from '../utils/volumeUtils.js';
import { apiService } from '../services/api.js';

export default function TrackRow({
  track,
  isSelected,
  getStatus,
  refreshTrack,
  setSelectedIndex,
  onSetDraft,
  onHoverPrime,
}) {
  const t = track;
  const status = getStatus(t.index);

  // Local state for live slider feedback
  const [localVolume, setLocalVolume] = useState(null);
  const [localPan, setLocalPan] = useState(null);

  const currentVolume = localVolume !== null ? localVolume : status?.mixer?.volume;
  const currentPan = localPan !== null ? localPan : status?.mixer?.pan;

  return (
    <ListItem
      key={t.index}
      selected={isSelected}
      onClick={() => { setSelectedIndex(t.index); refreshTrack(t.index); }}
      onMouseEnter={() => { onHoverPrime?.(t.index); }}
      secondaryAction={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title={status?.mute ? 'Unmute' : 'Mute'}>
            <IconButton size="small" onClick={async (e) => {
              e.stopPropagation();
              try {
                if (!isSelected) setSelectedIndex(t.index);
                const ts = getStatus(t.index) || await refreshTrack(t.index);
                await apiService.setMixer(t.index, 'mute', ts?.mute ? 0 : 1);
                await refreshTrack(t.index);
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
                const ts = getStatus(t.index) || await refreshTrack(t.index);
                await apiService.setMixer(t.index, 'solo', ts?.solo ? 0 : 1);
                await refreshTrack(t.index);
              } catch {}
            }}>
              <HeadphonesIcon fontSize="small" color={status?.solo ? 'success' : 'inherit'} />
            </IconButton>
          </Tooltip>
        </Box>
      }
      sx={{
        cursor: 'pointer',
        py: 0.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        boxShadow: '0 1px 3px rgba(0,0,0,0.12)'
      }}
    >
      <Box sx={{ width: '100%', pr: 10 }}>
        <Typography variant="body2" sx={{ fontWeight: isSelected ? 600 : 400, fontSize: '0.875rem' }}>
          {t.index}. {t.name}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
          {t.type}
        </Typography>

        {/* Sliders stacked vertically below track name */}
        <Box sx={{ mt: 0.5 }}>
          {/* Volume */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>
              Vol
            </Typography>
            <Slider
              size="small"
              value={typeof currentVolume === 'number' ? currentVolume : 0.5}
              min={0}
              max={1}
              step={0.005}
              onChange={(_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                setLocalVolume(v);
              }}
              onChangeCommitted={async (_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                try {
                  await apiService.setMixer(t.index, 'volume', Number(v));
                  await refreshTrack(t.index);
                } catch {}
                setLocalVolume(null);
              }}
              sx={{ flex: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 44, textAlign: 'right' }}>
              {liveFloatToDb(Number(currentVolume || 0.5)).toFixed(1)} dB
            </Typography>
          </Box>

          {/* Pan */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 22 }}>
              Pan
            </Typography>
            <Slider
              size="small"
              value={typeof currentPan === 'number' ? currentPan : 0}
              min={-1}
              max={1}
              step={0.02}
              onChange={(_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                setLocalPan(v);
              }}
              onChangeCommitted={async (_, val) => {
                const v = Array.isArray(val) ? val[0] : val;
                try {
                  await apiService.setMixer(t.index, 'pan', Number(v));
                  await refreshTrack(t.index);
                } catch {}
                setLocalPan(null);
              }}
              sx={{ flex: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', minWidth: 30, textAlign: 'right' }}>
              {Math.round(Math.abs(Number(currentPan || 0)) * 50)}{Number(currentPan || 0) < 0 ? 'L' : (Number(currentPan || 0) > 0 ? 'R' : '')}
            </Typography>
          </Box>
        </Box>
      </Box>
    </ListItem>
  );
}
