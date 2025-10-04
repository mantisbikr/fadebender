import React from 'react';
import {
  ListItem,
  ListItemText,
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
import { dbFromStatus, panLabelFromStatus, liveFloatToDb } from '../utils/volumeUtils.js';
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
  const volKey = (() => {
    const dbVal = dbFromStatus(status);
    return `vol-${t.index}-${dbVal != null ? dbVal.toFixed(1) : 'na'}`;
  })();
  const panKey = (() => {
    const lbl = panLabelFromStatus(status) || 'na';
    return `pan-${t.index}-${lbl}`;
  })();

  return (
    <ListItem
      key={t.index}
      selected={isSelected}
      onClick={() => { setSelectedIndex(t.index); refreshTrack(t.index); }}
      onMouseEnter={() => { onHoverPrime?.(t.index); }}
      secondaryAction={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Mute toggle */}
          <Tooltip title={(() => {
            const ts = getStatus(t.index);
            return ts && ts.mute ? 'Unmute' : 'Mute';
          })()}>
            <span>
              <IconButton size="small" onClick={async (e) => {
                e.stopPropagation();
                try {
                  if (!isSelected) setSelectedIndex(t.index);
                  const ts = getStatus(t.index) || await refreshTrack(t.index);
                  await apiService.setMixer(t.index, 'mute', ts?.mute ? 0 : 1);
                  await refreshTrack(t.index);
                } catch {}
              }}>
                <VolumeOffIcon fontSize="small" color={(getStatus(t.index)?.mute) ? 'warning' : 'inherit'} />
              </IconButton>
            </span>
          </Tooltip>
          {/* Solo toggle */}
          <Tooltip title={(() => {
            const ts = getStatus(t.index);
            return ts && ts.solo ? 'Unsolo' : 'Solo';
          })()}>
            <span>
              <IconButton size="small" onClick={async (e) => {
                e.stopPropagation();
                try {
                  if (!isSelected) setSelectedIndex(t.index);
                  const ts = getStatus(t.index) || await refreshTrack(t.index);
                  await apiService.setMixer(t.index, 'solo', ts?.solo ? 0 : 1);
                  await refreshTrack(t.index);
                } catch {}
              }}>
                <HeadphonesIcon fontSize="small" color={(getStatus(t.index)?.solo) ? 'success' : 'inherit'} />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      }
      sx={{ cursor: 'pointer' }}
    >
      <Box sx={{ width: '100%' }}>
        <ListItemText primary={`${t.index}. ${t.name}`} secondary={t.type} />
        {/* Sliders stacked vertically for clarity */}
        <Box sx={{ mt: 1, pr: 12 }}>
          <Typography variant="caption" color="text.secondary">Volume</Typography>
          <Slider
            size="small"
            value={(() => {
              const v = status?.mixer?.volume;
              return typeof v === 'number' ? v : 0.5;
            })()}
            min={0}
            max={1}
            step={0.005}
            valueLabelDisplay="auto"
            valueLabelFormat={(v) => `${liveFloatToDb(Number(v)).toFixed(1)} dB`}
            onChangeCommitted={async (_, val) => {
              const v = Array.isArray(val) ? val[0] : val;
              try {
                await apiService.setMixer(t.index, 'volume', Number(v));
                await refreshTrack(t.index);
              } catch {}
            }}
          />
          <Box sx={{ height: 8 }} />
          <Typography variant="caption" color="text.secondary">Pan</Typography>
          <Slider
            size="small"
            value={(() => {
              const p = status?.mixer?.pan;
              return typeof p === 'number' ? p : 0;
            })()}
            min={-1}
            max={1}
            step={0.02}
            valueLabelDisplay="auto"
            valueLabelFormat={(v) => `${Math.round(Math.abs(Number(v)) * 50)}${Number(v) < 0 ? 'L' : (Number(v) > 0 ? 'R' : '')}`}
            onChangeCommitted={async (_, val) => {
              const v = Array.isArray(val) ? val[0] : val;
              try {
                await apiService.setMixer(t.index, 'pan', Number(v));
                await refreshTrack(t.index);
              } catch {}
            }}
          />
        </Box>
      </Box>
    </ListItem>
  );
}
