import React, { useMemo, useState } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, Divider } from '@mui/material';
import { apiService } from '../services/api.js';

function approxEqual(a, b, eps = 1e-3) {
  try { return Math.abs(Number(a) - Number(b)) <= eps; } catch { return false; }
}

export default function ParamEditor({ capabilities, compact = false }) {
  if (!capabilities) return null;
  const values = capabilities.values || {};

  const allParams = useMemo(() => {
    const arr = [];
    (capabilities.groups || []).forEach(g => {
      (g.params || []).forEach(p => arr.push({ ...p, group: g.name }));
    });
    (capabilities.ungrouped || []).forEach(p => arr.push({ ...p, group: null }));
    return arr;
  }, [capabilities]);

  const [busy, setBusy] = useState(false);

  const currentLabelFor = (p) => {
    const v = values[p.name];
    if (!v) return null;
    const lm = p.label_map || null;
    if (!lm) return null;
    for (const [label, val] of Object.entries(lm)) {
      if (approxEqual(val, v.value)) return label;
    }
    return null;
  };

  const handleToggle = async (p, on) => {
    setBusy(true);
    try {
      await apiService.executeCanonicalIntent({
        domain: 'device', action: 'set',
        return_index: capabilities.return_index,
        device_index: capabilities.device_index,
        param_ref: p.name,
        display: on ? 'On' : 'Off'
      });
    } catch (e) {
      // noop; Chat area will display errors
      console.error(e);
    } finally { setBusy(false); }
  };

  const handleSelect = async (p, label) => {
    setBusy(true);
    try {
      await apiService.executeCanonicalIntent({
        domain: 'device', action: 'set',
        return_index: capabilities.return_index,
        device_index: capabilities.device_index,
        param_ref: p.name,
        display: String(label)
      });
    } catch (e) { console.error(e); } finally { setBusy(false); }
  };

  const handleSlider = async (p, val) => {
    setBusy(true);
    try {
      const unit = p.unit || null;
      const intent = {
        domain: 'device', action: 'set',
        return_index: capabilities.return_index,
        device_index: capabilities.device_index,
        param_ref: p.name,
      };
      if (unit) {
        intent.value = Number(val);
        intent.unit = unit;
      } else {
        // No unit — treat as display if mapping declares, otherwise percent of range
        intent.value = Number(val);
      }
      await apiService.executeCanonicalIntent(intent);
    } catch (e) { console.error(e); } finally { setBusy(false); }
  };

  const renderControl = (p) => {
    const ct = String(p.control_type || '').toLowerCase();
    if (!ct) return null; // No UI when type is missing
    const cur = values[p.name] || {};
    if (ct === 'toggle' || ct === 'binary') {
      const vmax = (p.max != null) ? Number(p.max) : 1.0;
      const on = approxEqual(cur.value, vmax) || String(cur.display_value || '').toLowerCase().includes('on');
      return (
        <FormControlLabel
          control={<Switch checked={!!on} onChange={(e) => handleToggle(p, e.target.checked)} disabled={busy} />}
          label={p.name}
        />
      );
    }
    if (ct === 'quantized' && (p.labels && p.labels.length)) {
      const current = currentLabelFor(p) || '';
      return (
        <Box sx={{ minWidth: 200 }}>
          <Typography variant="body2" sx={{ mb: 0.5 }}>{p.name}</Typography>
          <Select size="small" value={current} onChange={(e) => handleSelect(p, e.target.value)} disabled={busy} fullWidth>
            {p.labels.map((lab) => (
              <MenuItem key={String(lab)} value={String(lab)}>{String(lab)}</MenuItem>
            ))}
          </Select>
        </Box>
      );
    }
    if (ct !== 'continuous') return null; // Only render continuous slider when explicitly marked
    // Continuous
    const minD = Number(p.min_display ?? p.min ?? 0);
    const maxD = Number(p.max_display ?? p.max ?? 1);
    let curDisp = cur.display_value;
    const valNum = (typeof curDisp === 'string') ? Number((curDisp.match(/-?\d+(?:\.\d+)?/)||[])[0]) : (Number(curDisp) || Number(cur.value));
    return (
      <Box sx={{ minWidth: 260 }}>
        <Typography variant="body2" sx={{ mb: 0.5 }}>{p.name} {p.unit ? `(${p.unit})` : ''}</Typography>
        <Slider
          size="small"
          value={isFinite(valNum) ? valNum : minD}
          min={isFinite(minD) ? minD : 0}
          max={isFinite(maxD) ? maxD : 1}
          step={(maxD - minD) / 100}
          onChangeCommitted={(_, v) => handleSlider(p, v)}
          disabled={busy}
        />
        <Typography variant="caption" color="text.secondary">{isFinite(minD) ? minD : 0} — {isFinite(maxD) ? maxD : 1} {p.unit || ''}</Typography>
      </Box>
    );
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Edit Parameters</Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {allParams.map((p) => {
          const ui = renderControl(p);
          if (!ui) return null;
          return (<Box key={`${p.index}-${p.name}`}>{ui}</Box>);
        })}
      </Box>
      {!compact && <Divider sx={{ my: 2 }} />}
    </Box>
  );
}
