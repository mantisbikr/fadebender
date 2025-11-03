import React, { useState, useMemo, useEffect } from 'react';
import { Box, Typography, Switch, FormControlLabel, Select, MenuItem, Slider, CircularProgress } from '@mui/material';
import { apiService } from '../services/api.js';

export default function SingleMixerParamEditor({ editor }) {
  const { entity_type, index_ref, title, param, send_ref } = editor;
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentValue, setCurrentValue] = useState(param?.current_value);
  const [currentDisplay, setCurrentDisplay] = useState(param?.current_display);

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

  // Fetch fresh value when parameter changes
  useEffect(() => {
    console.log('[SingleMixerParamEditor] useEffect triggered for param:', param?.name);

    const fetchCurrentValue = async () => {
      let readBody = null;
      try {
        setLoading(true);
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

        console.log('[SingleMixerParamEditor] Fetching current value with:', readBody);

        const response = await apiService.readIntent(readBody);

        console.log('[SingleMixerParamEditor] Fetch response:', {
          ok: response?.ok,
          normalized_value: response?.normalized_value,
          value: response?.value,
          display_value: response?.display_value
        });

        if (response && response.ok) {
          const newValue = response.normalized_value ?? response.value;
          const newDisplay = response.display_value ?? response.value;
          console.log('[SingleMixerParamEditor] Setting new values:', { newValue, newDisplay });
          setCurrentValue(newValue);
          setCurrentDisplay(newDisplay);
        }
      } catch (error) {
        console.error('[SingleMixerParamEditor] Failed to fetch current value:', {
          error: error,
          errorMessage: error?.message,
          errorString: String(error),
          requestBody: readBody
        });
        // Fall back to param values
        setCurrentValue(param.current_value);
        setCurrentDisplay(param.current_display);
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentValue();
  }, [entity_type, index_ref, param.name, send_ref]);

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
    const current = String(param.current_label || '');
    return (
      <Box>
        <Typography variant="body2" sx={{ mb: 0.5 }}>{title || param.name}</Typography>
        <Select size="small" value={current} disabled={busy}>
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
