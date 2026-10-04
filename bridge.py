#!/usr/bin/env python3
"""TV remote bridge.

Phone UI -> this server -> Samsung TV (WebSocket) + Fire Stick (ADB).

Run:  python3 bridge.py
Then open http://<this-machine-ip>:5000 on your phone.
"""
import json
import subprocess
import time

from flask import Flask, jsonify, request, send_from_directory

with open("config.json") as f:
    CFG = json.load(f)

from samsung import SamsungTV  # noqa: E402

tv = SamsungTV(CFG["tv_ip"], CFG.get("tv_token"))

app = Flask(__name__, static_folder="ui", static_url_path="")


# ---------- Fire Stick via ADB ----------

def adb(*args):
    """Run an adb command against the Fire Stick. Returns stdout."""
    target = f"{CFG['stick_ip']}:5555"
    subprocess.run(["adb", "connect", target],
                   capture_output=True, timeout=15)
    r = subprocess.run(["adb", "-s", target, *args],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip()


def launch_app(name):
    spec = CFG["apps"][name]
    adb("shell", "monkey", "-p", spec["package"],
        "-c", spec["category"], "1")


# ---------- UI ----------

@app.get("/")
def index():
    return send_from_directory("ui", "index.html")


@app.get("/api/config")
def api_config():
    return jsonify({"apps": sorted(CFG["apps"].keys())})


# ---------- Samsung TV ----------

@app.post("/tv/key/<key>")
def tv_key(key):
    tv.send_key(key)
    return jsonify(ok=True)


# ---------- Fire Stick ----------

@app.post("/stick/key/<code>")
def stick_key(code):
    adb("shell", "input", "keyevent", code)
    return jsonify(ok=True)


@app.post("/stick/text")
def stick_text():
    text = (request.get_json(silent=True) or {}).get("text", "")
    adb("shell", "input", "text", text.replace(" ", "%s"))
    return jsonify(ok=True)


@app.post("/stick/launch/<name>")
def stick_launch(name):
    launch_app(name)
    return jsonify(ok=True, app=name)


@app.get("/stick/apps")
def stick_apps():
    """List installed third-party packages. Use this to find exact
    package names for apps you want to add to config.json."""
    out = adb("shell", "pm", "list", "packages", "-3")
    pkgs = [l.split(":", 1)[1] for l in out.splitlines()
            if l.startswith("package:")]
    return jsonify(sorted(pkgs))


@app.get("/stick/current")
def stick_current():
    out = adb("shell", "dumpsys", "window", "windows")
    for line in out.splitlines():
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            return jsonify(focus=line.strip())
    return jsonify(focus="unknown")


# ---------- Macros ----------

def run_macro_steps(steps):
    for step in steps:
        action = step["action"]
        if action == "tv_key":
            tv.send_key(step["key"])
        elif action == "stick_key":
            adb("shell", "input", "keyevent", step["code"])
        elif action == "stick_launch":
            launch_app(step["app"])
        elif action == "wait":
            time.sleep(float(step["seconds"]))
        else:
            raise ValueError(f"unknown macro action: {action}")


def watch_macro(app_name):
    """Standard 'watch something' macro: TV to the stick's HDMI input,
    wake the stick, launch the app."""
    return [
        {"action": "tv_key", "key": CFG.get("hdmi_key", "KEY_HDMI")},
        {"action": "wait", "seconds": 1.5},
        {"action": "stick_key", "code": "KEYCODE_WAKEUP"},
        {"action": "wait", "seconds": 0.5},
        {"action": "stick_launch", "app": app_name},
    ]


@app.post("/macro/<name>")
def macro(name):
    if name in CFG.get("macros", {}):
        run_macro_steps(CFG["macros"][name])
    elif name in CFG["apps"]:
        run_macro_steps(watch_macro(name))
    else:
        return jsonify(ok=False, error="unknown macro"), 404
    return jsonify(ok=True, macro=name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CFG.get("port", 5000))
