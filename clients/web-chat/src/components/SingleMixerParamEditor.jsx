import React, { useState, useMemo, useEffect } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleMixerParamEditor({ editor }) {
  const { entity_type, index_ref, title, param } = editor;
  const [busy, setBusy] = useState(false);

  const parsePanDisplay = (s, fallbackNorm, minD, maxD) => {
    const str = String(s || '').trim();
    if (!str) {
      const norm = Number(fallbackNorm);
      if (Number.isFinite(norm)) {
        const scale = Math.max(Math.abs(Number(minD ?? -50)), Math.abs(Number(maxD ?? 50)));
        return (norm * 2.0 - 1.0) * scale;
      }
      return 0;
    }
    if (/^c$/i.test(str)) return 0;
    const m = str.match(/(-?\d+(?:\.\d+)?)(\s*[LR])?/i);
    if (!m) return 0;
    const num = Number(m[1]);
    const side = (m[2] || '').toUpperCase();
    if (side.includes('L')) return -Math.abs(num);
    if (side.includes('R')) return Math.abs(num);
    return num;
  };

  const initialValue = useMemo(() => {
    if (!param) return 0;
    if ((param.name || '').toLowerCase() === 'pan') {
      return parsePanDisplay(param.current_display, param.current_value, param.min_display, param.max_display);
    }
    const v = param.current_display ?? param.current_value;
    const n = Number(v);
    if (Number.isFinite(n)) return n;
    const m = String(v || '').match(/-?\d+(?:\.\d+)?/);
    return m ? Number(m[0]) : 0;
  }, [param]);

  const [value, setValue] = useState(initialValue);
  useEffect(() => { setValue(initialValue); }, [initialValue]);

  const commit = async (val) => {
    setBusy(true);
    try {
      // Use canonical intents path for unit/display-aware conversion
      const field = param.name;
      if (entity_type === 'track') {
        // execute_intent expects 1-based track_index
        const ti1 = Number(index_ref) + 1;
        const payload = { domain: 'track', field, track_index: ti1 };
        if (field === 'volume') { payload.value = Number(val); payload.unit = 'db'; }
        else { payload.value = Number(val); }
        await apiService.executeCanonicalIntent(payload);
      } else if (entity_type === 'return') {
        const ri = index_ref.charCodeAt(0) - 'A'.charCodeAt(0);
        const payload = { domain: 'return', field, return_index: ri };
        if (field === 'volume') { payload.value = Number(val); payload.unit = 'db'; }
        else { payload.value = Number(val); }
        await apiService.executeCanonicalIntent(payload);
      } else if (entity_type === 'master') {
        const payload = { domain: 'master', field };
        if (field === 'volume' || field === 'cue') { payload.value = Number(val); payload.unit = 'db'; }
        else { payload.value = Number(val); }
        await apiService.executeCanonicalIntent(payload);
      }
    } finally { setBusy(false); }
  };

  const computedType = useMemo(() => {
    const ct = String(param.control_type || '').toLowerCase();
    if (ct === 'binary' || ct === 'toggle') return 'toggle';
    if (ct === 'quantized') return 'quantized';
    return 'continuous';
  }, [param]);

  if (!param || !param.control_type) return null;

  if (computedType === 'toggle') {
    const initialToggleOn = useMemo(() => {
      const disp = String(param.current_display || '');
      if (/^on$/i.test(disp)) return true;
      if (/^off$/i.test(disp)) return false;
      const num = Number(param.current_value);
      if (Number.isFinite(num)) return num >= 0.5;
      return false;
    }, [param]);
    const [toggleOn, setToggleOn] = useState(initialToggleOn);
    useEffect(() => { setToggleOn(initialToggleOn); }, [initialToggleOn]);
    return (
      <Box>
        <FormControlLabel
          control={<Switch checked={toggleOn} onChange={async (e) => { setToggleOn(e.target.checked); await commit(e.target.checked ? 1 : 0); }} disabled={busy} />}
          label={title || param.name}
        />
      </Box>
    );
  }

  if (computedType === 'quantized' && Array.isArray(param.labels) && param.labels.length) {
    const current = String(param.current_label || '');
    return (
      <Box>
        <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name}</Typography>
        <Select size="small" value={current} disabled={busy} onChange={async (e) => {
          // For mixer we don't have label_map use-cases today; keep for parity
          // Clients should convert label selections to numeric via server if needed
        }}>
          {param.labels.map((lab) => (<MenuItem key={String(lab)} value={String(lab)}>{String(lab)}</MenuItem>))}
        </Select>
      </Box>
    );
  }

  const minD = Number(param.min_display ?? param.min ?? 0);
  const maxD = Number(param.max_display ?? param.max ?? 1);
  const formatNum = (n) => {
    const x = Number(n);
    if (!isFinite(x)) return String(n);
    const r = Math.round(x * 100) / 100;
    return (r % 1 === 0) ? String(r) : String(r).replace(/\.?0+$/, '');
  };

  return (
    <Box>
      <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name} {param.unit ? `(${param.unit})` : ''}</Typography>
      <Slider
        size="small"
        value={Number(value)}
        min={isFinite(minD) ? minD : 0}
        max={isFinite(maxD) ? maxD : 1}
        step={(isFinite(maxD - minD) && (maxD - minD) > 0) ? (maxD - minD) / 100 : 0.01}
        disabled={busy}
        onChange={(_, v) => setValue(Number(v))}
        onChangeCommitted={(_, v) => commit(Number(v))}
        valueLabelDisplay="auto"
        valueLabelFormat={(x) => `${formatNum(x)}${param.unit ? ' ' + param.unit : ''}`}
      />
      <Typography variant="caption" color="text.secondary">{formatNum(isFinite(minD) ? minD : 0)} — {formatNum(isFinite(maxD) ? maxD : 1)} {param.unit || ''}</Typography>
    </Box>
  );
}
