import json
import os
import socket
from typing import Any, Dict, Optional, Tuple


def _udp_target() -> Tuple[str, int]:
    host = os.getenv("ABLETON_UDP_HOST", "127.0.0.1")
    port = int(os.getenv("ABLETON_UDP_PORT", "19845"))
    return host, port


def send(message: Dict[str, Any]) -> None:
    data = json.dumps(message).encode("utf-8")
    host, port = _udp_target()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data, (host, port))


def request(message: Dict[str, Any], timeout: float = 0.75) -> Optional[Dict[str, Any]]:
    data = json.dumps(message).encode("utf-8")
    host, port = _udp_target()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(data, (host, port))
        try:
            resp, _ = sock.recvfrom(64 * 1024)
            return json.loads(resp.decode("utf-8"))
        except socket.timeout:
            return None

