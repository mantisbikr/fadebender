import React from 'react';
import {
  ListItem,
  ListItemText,
  Box,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  VolumeOff as VolumeOffIcon,
  Headphones as HeadphonesIcon,
  VolumeUp as VolumeUpIcon,
  SurroundSound as PanIcon,
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
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
          {/* Volume indicator */}
          <Tooltip
            key={volKey}
            onOpen={async () => { await refreshTrack(t.index); }}
            title={(() => {
              const ts = getStatus(t.index);
              const dbVal = dbFromStatus(ts);
              return dbVal != null ? `${dbVal.toFixed(1)}` : '';
            })()}
          >
            <Box
              sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', cursor: 'pointer' }}
              onClick={(e) => {
                e.stopPropagation();
                const ts = getStatus(t.index);
                if (ts) {
                  // Use displayed dB if available; otherwise compute from float
                  const vdb = (() => {
                    const v = (ts?.mixer && typeof ts.mixer.volume === 'number') ? Number(ts.mixer.volume) : null;
                    if (v != null) return liveFloatToDb(v);
                    return (typeof ts?.volume_db === 'number') ? Number(ts.volume_db) : -6;
                  })();
                  onSetDraft?.(`set track ${t.index} volume to ${vdb.toFixed(1)}`);
                }
              }}
            >
              <VolumeUpIcon sx={{ fontSize: 16 }} />
            </Box>
          </Tooltip>
          {/* Pan indicator */}
          <Tooltip
            key={panKey}
            onOpen={async () => { await refreshTrack(t.index); }}
            title={(() => panLabelFromStatus(getStatus(t.index)) || 'Current pan')()}
          >
            <Box
              sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', cursor: 'pointer' }}
              onClick={(e) => {
                e.stopPropagation();
                const ts = getStatus(t.index);
                if (ts && ts.mixer && ts.mixer.pan != null) {
                  const lbl = panLabelFromStatus(ts);
                  onSetDraft?.(`set track ${t.index} pan to ${lbl}`);
                }
              }}
            >
              <PanIcon sx={{ fontSize: 16, mr: 0.25 }} />
            </Box>
          </Tooltip>
        </Box>
      }
      sx={{ cursor: 'pointer' }}
    >
      <ListItemText
        primary={`${t.index}. ${t.name}`}
        secondary={t.type}
      />
    </ListItem>
  );
}

