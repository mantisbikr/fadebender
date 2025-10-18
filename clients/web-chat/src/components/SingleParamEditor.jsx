import React, { useState, useMemo, useEffect } from 'react';
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
  // Derive initial toggle state from current value/display and keep it in sync
  const initialToggleOn = useMemo(() => {
    const dv = String(current?.display_value || '');
    if (/^on$/i.test(dv)) return true;
    if (/^off$/i.test(dv)) return false;
    if (typeof current?.is_on === 'boolean') return current.is_on;
    const num = Number(current?.value);
    if (Number.isFinite(num)) return num >= 0.99;
    const m = dv.match(/-?\d+(?:\.\d+)?/);
    if (m) return Number(m[0]) >= 0.99;
    return false;
  }, [current]);
  const [toggleOn, setToggleOn] = useState(initialToggleOn);
  useEffect(() => {
    setToggleOn(initialToggleOn);
  }, [initialToggleOn]);

  const handleToggle = async (on) => {
    setToggleOn(on);
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
    // Robust control type detection
    const ctIn = (param.control_type || '').toLowerCase();
    const hasLabels = Array.isArray(param.labels) && param.labels.length > 0;
    const hasLabelMap = param.label_map && typeof param.label_map === 'object' && Object.keys(param.label_map).length > 0;
    const labelsLower = hasLabels ? param.labels.map((l) => String(l).toLowerCase()) : [];
    const isOnOffLabels = labelsLower.includes('on') || labelsLower.includes('off');
    const nameLc = String(param.name || '').toLowerCase();
    const vmin = Number.isFinite(param.min) ? Number(param.min) : 0;
    const vmax = Number.isFinite(param.max) ? Number(param.max) : 1;
    const rangeLooksBool = Math.abs(vmin) <= 1e-6 && Math.abs(vmax - 1.0) <= 1e-6;

    const computedType = (() => {
      if (ctIn === 'toggle' || ctIn === 'binary') return 'toggle';
      if (isOnOffLabels) return 'toggle';
      if (nameLc.endsWith(' on') || rangeLooksBool) return 'toggle';
      if (ctIn === 'quantized' || hasLabels || hasLabelMap) return 'quantized';
      return 'continuous';
    })();

    if (computedType === 'toggle') {
      return (
        <>
          <FormControlLabel control={<Switch checked={toggleOn} onChange={(e) => handleToggle(e.target.checked)} disabled={busy} />} label={param.name} />
          {param.has_master && (
            <FormControlLabel sx={{ ml: 2 }} control={<Switch checked={autoEnable} onChange={(e) => setAutoEnable(e.target.checked)} />} label="Auto‑enable master" />
          )}
        </>
      );
    }

    if (computedType === 'quantized' && hasLabels) {
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
    // Build evenly spaced marks across range
    const marks = (() => {
      if (!isFinite(minD) || !isFinite(maxD) || maxD <= minD) return [];
      const ticks = 5; // 6 marks
      const step = (maxD - minD) / ticks;
      const arr = [];
      for (let i = 0; i <= ticks; i++) {
        const v = minD + i * step;
        arr.push({ value: v, label: `${formatNum(v)}${param.unit ? ' ' + param.unit : ''}` });
      }
      return arr;
    })();

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
          marks={marks}
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
