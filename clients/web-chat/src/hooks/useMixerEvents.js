import { useEffect } from 'react';
import { apiService } from '../services/api.js';

export function useMixerEvents(onMixerChanged, onSelectionChanged, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined;
    const url = apiService.getEventsURL();
    const es = new EventSource(url);
    es.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        if (!payload || typeof payload !== 'object') return;
        if (payload.event === 'mixer_changed' && payload.track) {
          onMixerChanged && onMixerChanged(payload);
        } else if (payload.event === 'selection_changed') {
          onSelectionChanged && onSelectionChanged(payload);
        }
      } catch {
        // ignore parse errors
      }
    };
    es.onerror = () => {
      try { es.close(); } catch {}
    };
    return () => { try { es.close(); } catch {} };
  }, [onMixerChanged, onSelectionChanged, enabled]);
}

