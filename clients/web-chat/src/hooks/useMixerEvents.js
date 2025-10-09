import { useEffect } from 'react';
import { apiService } from '../services/api.js';

export function useMixerEvents(onMixerChanged, onSelectionChanged, onOtherEvent, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined;
    const url = apiService.getEventsURL();
    const es = new EventSource(url);
    es.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        if (!payload || typeof payload !== 'object') return;
        if ((payload.event === 'mixer_changed' || payload.event === 'send_changed') && payload.track) {
          onMixerChanged && onMixerChanged(payload);
        } else if (payload.event === 'selection_changed') {
          onSelectionChanged && onSelectionChanged(payload);
        } else if (
          payload.event === 'preset_captured' ||
          payload.event === 'preset_updated' ||
          payload.event === 'preset_backfill_item' ||
          payload.event === 'preset_backfill_progress' ||
          payload.event === 'preset_backfill_done' ||
          payload.event === 'return_device_param_changed' ||
          payload.event === 'device_bypass_changed' ||
          payload.event === 'return_mixer_changed' ||
          payload.event === 'return_send_changed' ||
          payload.event === 'return_routing_changed' ||
          payload.event === 'preset_saved' ||
          payload.event === 'device_param_restored' ||
          payload.event === 'device_removed' ||
          payload.event === 'master_mixer_changed'
        ) {
          onOtherEvent && onOtherEvent(payload);
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
