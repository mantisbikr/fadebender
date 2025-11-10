import React, { useState, useMemo, useEffect, useRef } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, CircularProgress } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleDeviceParamEditor({ editor }) {
  const { return_index, device_index, title, param, current_values } = editor;
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentValue, setCurrentValue] = useState(current_values?.[param.name]?.display_value ?? param.current_value);
  const pollingRef = useRef(null);
  const mountedRef = useRef(true);

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

  // Fetch fresh value when parameter changes and start polling while editor is open
  useEffect(() => {
    mountedRef.current = true;
    console.log('[SingleDeviceParamEditor] useEffect triggered for param:', param?.name, {
      return_index,
      device_index,
      param_name: param.name,
      busy
    });

    const fetchCurrentValue = async () => {
      try {
        if (!mountedRef.current) return;
        if (busy) return; // avoid clobbering local value during commits
        setLoading((prev) => prev && true); // keep spinner only on first fetch
        const requestBody = {
          domain: 'device',
          return_index: return_index,
          device_index: device_index,
          param_ref: param.name
        };

        const response = await apiService.readIntent(requestBody);

        if (response && response.ok) {
          const newValue = response.display_value ?? response.normalized_value ?? response.value;
          setCurrentValue(newValue);
        }
      } catch (error) {
        // Fall back to current_values from capabilities
        const currentVal = current_values?.[param.name];
        if (currentVal && currentVal.display_value !== null && currentVal.display_value !== undefined) {
          setCurrentValue(currentVal.display_value);
        } else {
          setCurrentValue(param.current_value);
        }
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    };

    // initial fetch
    fetchCurrentValue();

    // start polling for live updates while open
    // TEMPORARILY DISABLED FOR DEBUGGING
    // if (pollingRef.current) clearInterval(pollingRef.current);
    // pollingRef.current = setInterval(() => {
    //   fetchCurrentValue();
    // }, 600);

    // cleanup
    return () => {
      mountedRef.current = false;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [return_index, device_index, param.name]);

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
      // Hint the server when value is a display percentage to avoid clamping to 1.0
      // But NOT for binary/toggle parameters!
      if (computedType !== 'toggle') {
        try {
          const unitStr = String(param.unit || '').toLowerCase();
          const hasPercentUnit = unitStr.includes('%') || unitStr.includes('percent');
          const md = Number(param.min_display);
          const Mx = Number(param.max_display);
          const looksLikePercentRange = Number.isFinite(md) && Number.isFinite(Mx) && md >= 0 && Mx <= 100;
          if (hasPercentUnit || looksLikePercentRange) {
            payload.unit = '%';
          }
        } catch {}
      }
      console.log('[SingleDeviceParamEditor] Committing:', {
        param_name: param.name,
        input_val: val,
        payload
      });
      await apiService.executeCanonicalIntent(payload);
    } finally { setBusy(false); }
  };

  // Commit with display string (for quantized params) - matches what chat does
  const commitDisplay = async (displayValue) => {
    setBusy(true);
    try {
      const payload = {
        domain: 'device',
        action: 'set',
        return_index: return_index,
        device_index: device_index,
        param_ref: param.name,
        display: String(displayValue)  // Send display string, let backend do label_map lookup
      };
      console.log('[SingleDeviceParamEditor] Committing display value:', {
        param_name: param.name,
        display: displayValue,
        payload
      });
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
    // Derive a reliable label from numeric or string value
    const deriveLabel = (val) => {
      const asNum = Number(val);
      if (Number.isFinite(asNum) && param.label_map) {
        const k = String(Math.round(asNum));
        if (k in param.label_map) return String(param.label_map[k]);
      }
      // Fallback: numeric index into labels array
      if (Number.isFinite(asNum) && Array.isArray(param.labels) && param.labels.length) {
        const idx = Math.max(0, Math.min(param.labels.length - 1, Math.round(asNum)));
        if (param.labels[idx] !== undefined) return String(param.labels[idx]);
      }
      const asStr = String(val || '');
      // If label_map is label->value and current value is label string key
      if (param.label_map && (asStr in param.label_map)) return asStr;
      if (param.labels.includes(asStr)) return asStr;
      // try reverse lookup: if currentValue equals any label_map value
      if (param.label_map) {
        const hit = Object.values(param.label_map).find(v => String(v) === asStr);
        if (hit) return String(hit);
      }
      return String(param.labels[0] || '');
    };

    const currentLabel = deriveLabel(currentValue);
    console.log('[SingleDeviceParamEditor] Quantized param state:', {
      param_name: param.name,
      currentValue,
      currentLabel,
      labels: param.labels,
      label_map: param.label_map,
      labels_includes_currentLabel: param.labels.includes(currentLabel)
    });

    return (
      <Box>
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          {title || param.name} — <span style={{ color: 'var(--mui-palette-text-secondary)' }}>{currentLabel}</span>
        </Typography>
        <Select
          size="small"
          value={currentLabel}
          disabled={busy}
          renderValue={(val) => String(val || currentLabel)}
          onChange={async (e) => {
            const selectedLabel = e.target.value;
            console.log('[SingleDeviceParamEditor] Dropdown changed:', {
              param_name: param.name,
              selectedLabel
            });
            // Optimistically update local value for snappy UI
            setCurrentValue(selectedLabel);
            // Send display string to backend - let it do label_map lookup (same as chat does)
            await commitDisplay(selectedLabel);
          }}
        >
          {param.labels.map((lab) => (<MenuItem key={String(lab)} value={String(lab)}>{String(lab)}</MenuItem>))}
        </Select>
      </Box>
    );
  }

  // Determine effective slider domain
  const unitStr = String(param.unit || '').toLowerCase();
  const isPercentDisplay = unitStr.includes('%') || unitStr.includes('percent') || /%/.test(String(currentValue || ''));
  let minD = Number(param.min_display ?? param.min ?? 0);
  let maxD = Number(param.max_display ?? param.max ?? 1);
  if (isPercentDisplay) {
    // Use 0..100 domain for percent-like parameters regardless of normalized min/max
    minD = 0;
    maxD = 100;
  }
  const formatNum = (n) => {
    const x = Number(n);
    if (!isFinite(x)) return String(n);
    const r = Math.round(x * 100) / 100;
    return (r % 1 === 0) ? String(r) : String(r).replace(/\.?0+$/, '');
  };

  const displayUnit = (param.unit && param.unit !== 'display_value') ? param.unit : (isPercentDisplay ? '%' : '');

  return (
    <Box>
      <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name} {displayUnit ? `(${displayUnit})` : ''}</Typography>
      <Slider
        size="small"
        value={Number(value)}
        min={isFinite(minD) ? minD : 0}
        max={isFinite(maxD) ? maxD : 1}
        step={(isFinite(maxD - minD) && (maxD - minD) > 0) ? (isPercentDisplay ? 1 : (maxD - minD) / 100) : 0.01}
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
