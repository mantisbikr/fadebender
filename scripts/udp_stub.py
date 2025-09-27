#!/usr/bin/env python3
import os
import socket
import json

HOST = os.environ.get('ABLETON_UDP_HOST', '127.0.0.1')
PORT = int(os.environ.get('ABLETON_UDP_PORT', '19845'))

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
        reply = json.dumps({'ok': True, 'echo': msg}).encode('utf-8')
        s.sendto(reply, addr)

if __name__ == '__main__':
    main()

