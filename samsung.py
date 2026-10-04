"""Samsung Tizen TV remote control over the local network WebSocket API.

Usage:
    tv = SamsungTV("192.168.1.50", token="12345678")
    tv.send_key("KEY_HDMI")

On first use the TV shows an "Allow?" prompt. Run pair.py to do the
one-time pairing and get the token for config.json.
"""
import base64
import json

import websocket


class SamsungTV:
    def __init__(self, ip, token=None, app_name="TvRemote", timeout=8):
        self.ip = ip
        self.token = token
        self.timeout = timeout
        self.name_b64 = base64.b64encode(app_name.encode()).decode()

    def _url(self):
        url = (
            f"ws://{self.ip}:8001/api/v2/channels/samsung.remote.control"
            f"?name={self.name_b64}"
        )
        if self.token:
            url += f"&token={self.token}"
        return url

    def send_key(self, key):
        """Send a remote key press, e.g. KEY_POWER, KEY_HDMI, KEY_HOME,
        KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER, KEY_RETURN,
        KEY_VOLUP, KEY_VOLDOWN, KEY_MUTE, KEY_SOURCE."""
        payload = {
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey",
            },
        }
        ws = websocket.create_connection(self._url(), timeout=self.timeout)
        try:
            ws.send(json.dumps(payload))
        finally:
            ws.close()
        return True
