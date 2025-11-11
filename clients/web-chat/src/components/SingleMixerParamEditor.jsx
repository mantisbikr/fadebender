import React, { useState, useMemo, useEffect, useRef } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, CircularProgress } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleMixerParamEditor({ editor }) {
  const { entity_type, index_ref, title, param, send_ref } = editor;
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentValue, setCurrentValue] = useState(param?.current_value);
  const [currentDisplay, setCurrentDisplay] = useState(param?.current_display);
  const pollingRef = useRef(null);
  const mountedRef = useRef(true);

  console.log('[SingleMixerParamEditor] Component mounted/updated:', {
    param_name: param?.name,
    entity_type,
    index_ref,
    send_ref,
    initial_current_value: currentValue,
    initial_current_display: currentDisplay
  });

  // Determine control type
  const computedType = useMemo(() => {
    if (!param || !param.control_type) return null;
    const ct = String(param.control_type).toLowerCase();
    if (ct === 'binary' || ct === 'toggle') return 'toggle';
    if (ct === 'quantized') return 'quantized';
    return 'continuous';
  }, [param]);

  // Fetch fresh value when parameter changes and start polling
  useEffect(() => {
    mountedRef.current = true;
    console.log('[SingleMixerParamEditor] useEffect triggered for param:', param?.name);

    const fetchCurrentValue = async () => {
      let readBody = null;
      try {
        if (!mountedRef.current) return;
        if (busy) return; // avoid clobbering during commits
        if (loading) setLoading(true);
        readBody = { domain: entity_type, field: param.name };

        if (entity_type === 'track') {
          readBody.track_index = Number(index_ref) + 1; // 1-based for backend
        } else if (entity_type === 'return') {
          readBody.return_ref = String(index_ref);
        }

        if (send_ref) {
          readBody.field = 'send';
          readBody.send_ref = send_ref;
        }

        const response = await apiService.readIntent(readBody);

        if (response && response.ok) {
          const newValue = response.normalized_value ?? response.value;
          const newDisplay = response.display_value ?? response.value;
          setCurrentValue(newValue);
          setCurrentDisplay(newDisplay);
        }
      } catch (error) {
        // Fall back to param values
        setCurrentValue(param.current_value);
        setCurrentDisplay(param.current_display);
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    };

    // initial fetch
    fetchCurrentValue();

    // start polling for live changes
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
  }, [entity_type, index_ref, param.name, send_ref, busy]);

  // Parse pan display value
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

  // Calculate initial value for slider/input
  const initialValue = useMemo(() => {
    if (!param) return 0;
    if ((param.name || '').toLowerCase() === 'pan') {
      return parsePanDisplay(currentDisplay, currentValue, param.min_display, param.max_display);
    }
    const v = currentDisplay ?? currentValue;
    const n = Number(v);
    if (Number.isFinite(n)) return n;
    const m = String(v || '').match(/-?\d+(?:\.\d+)?/);
    return m ? Number(m[0]) : 0;
  }, [param, currentValue, currentDisplay, loading]);

  const [value, setValue] = useState(initialValue);
  useEffect(() => { setValue(initialValue); }, [initialValue]);

  // Initial toggle state
  const initialToggleOn = useMemo(() => {
    if (computedType !== 'toggle') return false;
    const disp = String(currentDisplay || '');
    if (/^on$/i.test(disp)) return true;
    if (/^off$/i.test(disp)) return false;
    const num = Number(currentValue);
    if (Number.isFinite(num)) return num >= 0.5;
    return false;
  }, [computedType, currentValue, currentDisplay, loading]);

  const [toggleOn, setToggleOn] = useState(initialToggleOn);
  useEffect(() => { setToggleOn(initialToggleOn); }, [initialToggleOn]);

  // Commit function
  const commit = async (val) => {
    setBusy(true);
    try {
      if (send_ref) {
        if (entity_type === 'track') {
          const ti1 = Number(index_ref) + 1;
          const payload = { domain: 'track', field: 'send', track_index: ti1, send_ref, value: Number(val), unit: 'db' };
          await apiService.executeCanonicalIntent(payload);
        } else if (entity_type === 'return') {
          const ri = index_ref.charCodeAt(0) - 'A'.charCodeAt(0);
          const payload = { domain: 'return', field: 'send', return_index: ri, send_ref, value: Number(val), unit: 'db' };
          await apiService.executeCanonicalIntent(payload);
        }
        return;
      }

      const field = param.name;
      if (entity_type === 'track') {
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

  // Early return after all hooks have been called
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
    const deriveLabel = () => {
      const asStr = String(currentDisplay || '');
      if (param.label_map && (asStr in param.label_map)) return asStr; // label->value
      if (param.labels.includes(asStr)) return asStr;
      const asNum = Number(currentValue);
      if (Number.isFinite(asNum) && param.label_map) {
        const k = String(Math.round(asNum));
        if (k in param.label_map) return String(param.label_map[k]);
      }
      // Fallback: numeric index into labels array
      if (Number.isFinite(Number(currentValue)) && Array.isArray(param.labels) && param.labels.length) {
        const idx = Math.max(0, Math.min(param.labels.length - 1, Math.round(Number(currentValue))));
        if (param.labels[idx] !== undefined) return String(param.labels[idx]);
      }
      return String(param.labels[0] || '');
    };
    const currentLabel = deriveLabel();

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
            // Optimistic display update
            setCurrentDisplay(selectedLabel);
            // Map label to numeric value if possible
            let commitVal = null;
            if (param.label_map) {
              // Case A: number->label
              const key = Object.keys(param.label_map).find(k => String(param.label_map[k]) === String(selectedLabel));
              if (key !== undefined) commitVal = Number(key);
              // Case B: label->value
              if (commitVal === null && (selectedLabel in param.label_map)) {
                const v = Number(param.label_map[selectedLabel]);
                if (Number.isFinite(v)) commitVal = v;
              }
            }
            if (commitVal === null) {
              const idx = param.labels.findIndex(l => String(l) === String(selectedLabel));
              if (idx >= 0) commitVal = idx;
            }
            if (commitVal !== null) await commit(commitVal);
          }}
        >
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
