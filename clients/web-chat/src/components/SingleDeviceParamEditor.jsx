import React, { useState, useMemo, useEffect } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, CircularProgress } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleDeviceParamEditor({ editor }) {
  const { return_index, device_index, title, param, current_values } = editor;
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentValue, setCurrentValue] = useState(current_values?.[param.name]?.display_value ?? param.current_value);

  console.log('[SingleDeviceParamEditor] Component mounted/updated:', {
    param_name: param?.name,
    return_index,
    device_index,
    initial_current_value: currentValue
  });

  // Determine control type
  const computedType = useMemo(() => {
    if (!param || !param.control_type) return null;
    const ct = String(param.control_type).toLowerCase();
    if (ct === 'binary' || ct === 'toggle') return 'toggle';
    if (ct === 'quantized') return 'quantized';
    return 'continuous';
  }, [param]);

  // Fetch fresh value when parameter changes
  useEffect(() => {
    console.log('[SingleDeviceParamEditor] useEffect triggered for param:', param?.name);

    const fetchCurrentValue = async () => {
      try {
        setLoading(true);
        const requestBody = {
          domain: 'device',
          return_index: return_index,
          device_index: device_index,
          param_ref: param.name
        };

        console.log('[SingleDeviceParamEditor] Fetching current value with:', requestBody);

        const response = await apiService.readIntent(requestBody);

        console.log('[SingleDeviceParamEditor] Fetch response:', {
          ok: response?.ok,
          normalized_value: response?.normalized_value,
          value: response?.value
        });

        if (response && response.ok) {
          const newValue = response.display_value ?? response.normalized_value ?? response.value;
          console.log('[SingleDeviceParamEditor] Setting new value:', newValue);
          setCurrentValue(newValue);
        }
      } catch (error) {
        console.warn('[SingleDeviceParamEditor] Failed to fetch device current value:', error);
        // Fall back to current_values from capabilities
        const currentVal = current_values?.[param.name];
        if (currentVal && currentVal.display_value !== null && currentVal.display_value !== undefined) {
          setCurrentValue(currentVal.display_value);
        } else {
          setCurrentValue(param.current_value);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentValue();
  }, [return_index, device_index, param.name, current_values]);

  const initialValue = useMemo(() => {
    if (!param) return 0;
    const n = Number(currentValue);
    if (Number.isFinite(n)) return n;
    const m = String(currentValue || '').match(/-?\d+(?:\.\d+)?/);
    return m ? Number(m[0]) : 0;
  }, [param, currentValue, loading]);

  const [value, setValue] = useState(initialValue);
  useEffect(() => { setValue(initialValue); }, [initialValue]);

  // Initial toggle state
  const initialToggleOn = useMemo(() => {
    if (computedType !== 'toggle') return false;

    // For binary params with labels, check if currentValue matches the "on" label (index 1)
    if (param.labels && param.labels.length === 2) {
      const currentStr = String(currentValue || '').toLowerCase();
      const onLabel = String(param.labels[1] || '').toLowerCase();
      const offLabel = String(param.labels[0] || '').toLowerCase();

      if (currentStr === onLabel) return true;
      if (currentStr === offLabel) return false;
    }

    // Fallback: try numeric conversion
    const num = Number(currentValue);
    if (Number.isFinite(num)) return num >= 0.5;
    return false;
  }, [computedType, currentValue, loading, param]);

  const [toggleOn, setToggleOn] = useState(initialToggleOn);
  useEffect(() => { setToggleOn(initialToggleOn); }, [initialToggleOn]);

  const commit = async (val) => {
    setBusy(true);
    try {
      const payload = {
        domain: 'device',
        action: 'set',
        return_index: return_index,
        device_index: device_index,
        param_ref: param.name,
        value: Number(val)
      };
      await apiService.executeCanonicalIntent(payload);
    } finally { setBusy(false); }
  };

  // Early return after all hooks
  if (!param || !param.control_type) {
    return <Typography variant="caption" color="text.secondary">No parameter data</Typography>;
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
        <CircularProgress size={16} />
        <Typography variant="caption" color="text.secondary">Loading current value...</Typography>
      </Box>
    );
  }

  if (computedType === 'toggle') {
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
    // For quantized params, currentValue now contains the label string directly from backend (e.g., "Fade")
    // Backend's read_intent now looks up the label from Firestore label_map
    let currentLabel = String(currentValue || '');

    // Fallback to first label if nothing matches
    if (!currentLabel || !param.labels.includes(currentLabel)) {
      currentLabel = String(param.labels[0] || '');
    }

    return (
      <Box>
        <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name}</Typography>
        <Select size="small" value={currentLabel} disabled={busy} onChange={async (e) => {
          const selectedLabel = e.target.value;
          // Find the normalized value (key) for this label in label_map
          if (param.label_map) {
            const normalizedValueKey = Object.keys(param.label_map).find(key => param.label_map[key] === selectedLabel);
            if (normalizedValueKey !== undefined) {
              await commit(Number(normalizedValueKey));
            }
          }
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

  const displayUnit = param.unit && param.unit !== 'display_value' ? param.unit : '';

  return (
    <Box>
      <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name} {displayUnit ? `(${displayUnit})` : ''}</Typography>
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
        valueLabelFormat={(x) => `${formatNum(x)}${displayUnit ? ' ' + displayUnit : ''}`}
      />
      <Typography variant="caption" color="text.secondary">{formatNum(isFinite(minD) ? minD : 0)} — {formatNum(isFinite(maxD) ? maxD : 1)} {displayUnit}</Typography>
    </Box>
  );
}
