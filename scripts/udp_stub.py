#!/usr/bin/env python3
import os
import socket
import json

HOST = os.environ.get('ABLETON_UDP_HOST', '127.0.0.1')
PORT = int(os.environ.get('ABLETON_UDP_PORT', '19845'))

STATE = {
    'tracks': [
        {'index': 1, 'name': 'Track 1', 'type': 'audio', 'mixer': {'volume': 0.5, 'pan': 0.0}},
        {'index': 2, 'name': 'Track 2', 'type': 'audio', 'mixer': {'volume': 0.5, 'pan': 0.0}},
    ],
    'selected_track': 1,
    'scenes': 1,
}


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    print(f'UDP stub listening on {HOST}:{PORT} (Ctrl+C to stop)')
    while True:
        data, addr = s.recvfrom(65535)
        try:
            msg = json.loads(data.decode('utf-8'))
        except Exception:
            msg = {}

        op = (msg.get('op') or '').strip()
        if op == 'ping':
            reply_obj = {'ok': True, 'op': 'ping'}
        elif op == 'get_overview':
            reply_obj = {
                'ok': True,
                'op': 'get_overview',
                'data': {
                    'tracks': [{'index': t['index'], 'name': t['name'], 'type': t['type']} for t in STATE['tracks']],
                    'selected_track': STATE['selected_track'],
                    'scenes': STATE['scenes'],
                }
            }
        elif op == 'get_track_status':
            ti = int(msg.get('track_index', 0))
            found = next((t for t in STATE['tracks'] if t['index'] == ti), None)
            if found:
                reply_obj = {'ok': True, 'op': op, 'data': {'index': found['index'], 'name': found['name'], 'mixer': found['mixer']}}
            else:
                reply_obj = {'ok': False, 'error': 'track_not_found'}
        elif op == 'set_mixer':
            ti = int(msg.get('track_index', 0))
            field = str(msg.get('field'))
            value = float(msg.get('value', 0.0))
            found = next((t for t in STATE['tracks'] if t['index'] == ti), None)
            if found and field in ('volume', 'pan', 'mute', 'solo'):
                if field == 'volume':
                    value = max(0.0, min(1.0, value))
                if field == 'pan':
                    value = max(-1.0, min(1.0, value))
                if field in ('volume', 'pan'):
                    found['mixer'][field] = value
                else:
                    found[field] = bool(value)
                reply_obj = {'ok': True, 'op': op}
            else:
                reply_obj = {'ok': False, 'error': 'bad_args'}
        else:
            reply_obj = {'ok': True, 'echo': msg}

        s.sendto(json.dumps(reply_obj).encode('utf-8'), addr)

if __name__ == '__main__':
    main()
