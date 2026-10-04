#!/usr/bin/env python3
"""One-time Samsung TV pairing.

Run:  python3 pair.py [TV_IP]

Accept the "Allow?" prompt on your TV with the TV remote.
Prints the token to paste into config.json as "tv_token".
"""
import base64
import json
import sys

import websocket


def main():
    ip = sys.argv[1] if len(sys.argv) > 1 else input("TV IP address: ").strip()
    name_b64 = base64.b64encode(b"TvRemote").decode()
    url = (
        f"ws://{ip}:8001/api/v2/channels/samsung.remote.control"
        f"?name={name_b64}"
    )
    print("Connecting... if your TV shows an Allow prompt, accept it now.")
    ws = websocket.create_connection(url, timeout=60)
    try:
        msg = ws.recv()
    finally:
        ws.close()
    token = (json.loads(msg).get("data") or {}).get("token")
    if token:
        print("\nPaired! Add this to config.json:")
        print(f'  "tv_token": "{token}"')
    else:
        print("\nNo token received. Raw message:")
        print(msg[:300])


if __name__ == "__main__":
    main()
