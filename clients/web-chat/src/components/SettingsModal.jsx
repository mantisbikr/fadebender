import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  TextField,
  FormGroup,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  InputLabel,
  FormControl
} from '@mui/material';
import { apiService } from '../services/api.js';

export default function SettingsModal({ open, onClose, confirmExecute, setConfirmExecute, systemStatus }) {
  const [ui, setUi] = useState({ refresh_ms: 5000, sends_open_refresh_ms: 800, master_refresh_ms: 800, track_refresh_ms: 1200, returns_refresh_ms: 3000, sse_throttle_ms: 150, sidebar_width_px: 360, default_sidebar_tab: 'tracks' });
  const [debug, setDebug] = useState({ firestore: false, sse: false, auto_capture: false });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const cfg = await apiService.getAppConfig();
        const uiIn = cfg?.ui || {};
        const dbgIn = cfg?.debug || {};
        setUi((prev) => ({ ...prev, ...uiIn }));
        setDebug((prev) => ({ ...prev, ...dbgIn }));
      } catch {}
    })();
  }, [open]);

  const save = async () => {
    setSaving(true);
    try {
      await apiService.updateAppConfig({ ui, debug });
    } catch {}
    setSaving(false);
    onClose?.();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Settings</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Session Controls */}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControlLabel
              control={<Switch checked={!!confirmExecute} onChange={(e) => setConfirmExecute?.(e.target.checked)} />}
              label={confirmExecute ? 'Execute' : 'Preview only'}
            />
          </Box>
          {systemStatus && (
            <Box sx={{ fontSize: 12, color: 'text.secondary' }}>
              <div>Controller: {systemStatus.status || 'unknown'}</div>
            </Box>
          )}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Button size="small" variant="outlined" onClick={() => window.dispatchEvent(new Event('fb:refresh-project'))}>
              Refresh Project
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              label="Auto-refresh (ms)"
              type="number"
              value={ui.refresh_ms}
              onChange={(e) => setUi({ ...ui, refresh_ms: Number(e.target.value) })}
              size="small"
            />
            <TextField
              label="Sends Open (ms)"
              type="number"
              value={ui.sends_open_refresh_ms}
              onChange={(e) => setUi({ ...ui, sends_open_refresh_ms: Number(e.target.value) })}
              size="small"
            />
            <TextField
              label="Master Poll (ms)"
              type="number"
              value={ui.master_refresh_ms}
              onChange={(e) => setUi({ ...ui, master_refresh_ms: Number(e.target.value) })}
              size="small"
            />
            <TextField
              label="Track Poll (ms)"
              type="number"
              value={ui.track_refresh_ms}
              onChange={(e) => setUi({ ...ui, track_refresh_ms: Number(e.target.value) })}
              size="small"
            />
            <TextField
              label="Returns Poll (ms)"
              type="number"
              value={ui.returns_refresh_ms}
              onChange={(e) => setUi({ ...ui, returns_refresh_ms: Number(e.target.value) })}
              size="small"
            />
            <TextField
              label="SSE Throttle (ms)"
              type="number"
              value={ui.sse_throttle_ms}
              onChange={(e) => setUi({ ...ui, sse_throttle_ms: Number(e.target.value) })}
              size="small"
            />
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Sidebar Width (px)"
              type="number"
              value={ui.sidebar_width_px}
              onChange={(e) => setUi({ ...ui, sidebar_width_px: Number(e.target.value) })}
              size="small"
            />
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Default Tab</InputLabel>
              <Select
                label="Default Tab"
                value={ui.default_sidebar_tab || 'tracks'}
                onChange={(e) => setUi({ ...ui, default_sidebar_tab: e.target.value })}
              >
                <MenuItem value="tracks">Tracks</MenuItem>
                <MenuItem value="returns">Returns</MenuItem>
                <MenuItem value="master">Master</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <FormGroup>
            <FormControlLabel control={<Switch checked={!!debug.firestore} onChange={(e) => setDebug({ ...debug, firestore: e.target.checked })} />} label="Debug: Firestore" />
            <FormControlLabel control={<Switch checked={!!debug.sse} onChange={(e) => setDebug({ ...debug, sse: e.target.checked })} />} label="Debug: SSE" />
            <FormControlLabel control={<Switch checked={!!debug.auto_capture} onChange={(e) => setDebug({ ...debug, auto_capture: e.target.checked })} />} label="Debug: Auto-capture" />
          </FormGroup>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>Close</Button>
        <Button onClick={save} variant="contained" disabled={saving}>Save</Button>
      </DialogActions>
    </Dialog>
  );
}
