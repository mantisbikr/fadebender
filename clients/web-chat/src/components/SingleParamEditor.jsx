import React, { useState, useMemo } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, Chip } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleParamEditor({ editor, onSuggestedIntent }) {
  const { return_index, return_letter, device_index, device_name, param, current, suggested } = editor;
  const [busy, setBusy] = useState(false);
  const [value, setValue] = useState(() => {
    const v = current?.display_value ?? current?.value;
    const m = String(v || '').match(/-?\d+(?:\.\d+)?/);
    return m ? Number(m[0]) : (typeof v === 'number' ? v : 0);
  });

  const exec = async (payload) => {
    setBusy(true);
    try {
      await apiService.executeCanonicalIntent(payload);
    } finally { setBusy(false); }
  };

  // Auto-enable master toggle (default on if dependency exists)
  const [autoEnable, setAutoEnable] = useState(param.has_master ? true : false);

  const handleToggle = async (on) => {
    await exec({ domain: 'device', action: 'set', return_index, device_index, param_ref: param.name, display: on ? 'On' : 'Off', auto_enable_master: autoEnable });
  };

  const handleSelect = async (label) => {
    await exec({ domain: 'device', action: 'set', return_index, device_index, param_ref: param.name, display: String(label), auto_enable_master: autoEnable });
  };

  const handleSliderCommit = async (_, v) => {
    setValue(Number(v));
    const payload = { domain: 'device', action: 'set', return_index, device_index, param_ref: param.name, auto_enable_master: autoEnable };
    if (param.unit) {
      payload.value = Number(v); payload.unit = param.unit;
    } else {
      payload.value = Number(v);
    }
    await exec(payload);
  };

  const formatNum = (n) => {
    const x = Number(n);
    if (!isFinite(x)) return String(n);
    const r = Math.round(x * 100) / 100;
    return (r % 1 === 0) ? String(r) : String(r).replace(/\.?0+$/, '');
  };

  const renderControl = () => {
    const ct = param.control_type || 'continuous';
    if (ct === 'toggle') {
      const isOn = /on/i.test(String(current?.display_value || '')) || (Number(current?.value) >= 0.99);
      return (
        <>
          <FormControlLabel control={<Switch checked={isOn} onChange={(e) => handleToggle(e.target.checked)} disabled={busy} />} label={param.name} />
          {param.has_master && (
            <FormControlLabel sx={{ ml: 2 }} control={<Switch checked={autoEnable} onChange={(e) => setAutoEnable(e.target.checked)} />} label="Auto‑enable master" />
          )}
        </>
      );
    }
    if (ct === 'quantized' && (param.labels && param.labels.length)) {
      const currentLabel = useMemo(() => {
        const lm = param.label_map || {};
        if (!lm || !current) return '';
        const entries = Object.entries(lm);
        const match = entries.find(([lab, val]) => Math.abs(Number(val) - Number(current.value)) <= 1e-6);
        return match ? match[0] : '';
      }, [param, current]);
      return (
        <Box>
          <Typography variant="body2" sx={{ mb: 0.5 }}>{param.name}</Typography>
          <Select size="small" value={currentLabel} disabled={busy} onChange={(e) => handleSelect(e.target.value)}>
            {param.labels.map((lab) => (<MenuItem key={String(lab)} value={String(lab)}>{String(lab)}</MenuItem>))}
          </Select>
          {param.has_master && (
            <FormControlLabel sx={{ ml: 1, mt: 1 }} control={<Switch checked={autoEnable} onChange={(e) => setAutoEnable(e.target.checked)} />} label="Auto‑enable master" />
          )}
        </Box>
      );
    }
    const minD = Number(param.min_display ?? param.min ?? 0);
    const maxD = Number(param.max_display ?? param.max ?? 1);
    return (
      <Box>
        <Typography variant="body2" sx={{ mb: 0.5 }}>{param.name} {param.unit ? `(${param.unit})` : ''}</Typography>
        <Slider
          size="small"
          value={Number(value)}
          min={isFinite(minD) ? minD : 0}
          max={isFinite(maxD) ? maxD : 1}
          step={(isFinite(maxD - minD) && (maxD - minD) > 0) ? (maxD - minD) / 100 : 0.01}
          onChangeCommitted={handleSliderCommit}
          onChange={(_, v) => setValue(Number(v))}
          disabled={busy}
          valueLabelDisplay="auto"
          valueLabelFormat={(x) => `${formatNum(x)}${param.unit ? ' ' + param.unit : ''}`}
          marks={[{ value: isFinite(minD) ? minD : 0, label: `${formatNum(isFinite(minD) ? minD : 0)}${param.unit ? ' ' + param.unit : ''}` }, { value: isFinite(maxD) ? maxD : 1, label: `${formatNum(isFinite(maxD) ? maxD : 1)}${param.unit ? ' ' + param.unit : ''}` }]}
        />
        <Typography variant="caption" color="text.secondary">{formatNum(isFinite(minD) ? minD : 0)} — {formatNum(isFinite(maxD) ? maxD : 1)} {param.unit || ''}</Typography>
        {param.has_master && (
          <FormControlLabel sx={{ ml: 1, mt: 1 }} control={<Switch checked={autoEnable} onChange={(e) => setAutoEnable(e.target.checked)} />} label="Auto‑enable master" />
        )}
      </Box>
    );
  };

  return (
    <Box>
      {renderControl()}
      {Array.isArray(suggested) && suggested.length > 0 && (
        <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {suggested.map((s, i) => (<Chip key={i} size="small" label={s} onClick={() => onSuggestedIntent?.(s)} />))}
        </Box>
      )}
    </Box>
  );
}
