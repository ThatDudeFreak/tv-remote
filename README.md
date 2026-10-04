# TV Remote

A phone remote for a Samsung TV + Amazon Fire Stick on the same Wi-Fi.
Big buttons, one-tap app launching, and macros like "switch to the
Fire Stick input and open Hulu" in a single tap. Optional Siri voice
via iOS Shortcuts.

## How it works

Your phone talks to a small bridge server on your home network
(a Raspberry Pi or any computer that stays on). The bridge translates
taps into:

- **Samsung TV**: key presses over the TV's local WebSocket remote API
  (power, volume, HDMI input, etc.)
- **Fire Stick**: commands over ADB on your network (launch apps
  directly by package name, d-pad navigation, text input)

## Setup

### 1. Fire Stick: enable ADB

1. Settings > My Fire TV > About > click the device name 7 times
   to unlock Developer Options.
2. Go back to My Fire TV > Developer Options > turn **ADB debugging** ON.
3. Note the stick's IP: Settings > My Fire TV > About > Network.

The first time the bridge connects, the stick shows an
"Allow USB debugging?" prompt. Accept it with the Fire Stick remote
and tick "always allow".

### 2. Bridge machine

Needs Python 3 and the `adb` tool on the same Wi-Fi as the TV and stick.

```bash
# Debian/Raspberry Pi
sudo apt install python3-pip adb
# macOS
brew install android-platform-tools

git clone <this-repo>
cd tv-remote
pip install -r requirements.txt
cp config.example.json config.json
```

Edit `config.json` with your TV and Fire Stick IPs. If your stick
is on a different HDMI input than the default, change `hdmi_key`
(try `KEY_HDMI` first; some models need the input cycled manually once).

### 3. Pair the Samsung TV (one time)

```bash
python3 pair.py
```

Accept the Allow prompt on the TV with the TV remote. Paste the
printed token into `config.json` as `tv_token`.

### 4. Run it

```bash
python3 bridge.py
```

Open `http://<bridge-ip>:5000` on your phone and use Add to Home
Screen for an app-like icon.

### 5. Siri voice (optional)

In the Shortcuts app, make a shortcut per command:

1. Add action: Get Contents of URL
2. URL: `http://<bridge-ip>:5000/macro/hulu`, method POST
3. Name the shortcut "Hulu"

Then "Hey Siri, Hulu" switches input and opens Hulu.

## Finding app package names

Open `http://<bridge-ip>:5000/stick/apps` in a browser to list
installed packages, then add them to the `apps` section of
`config.json`. The five defaults are Hulu, Netflix, Disney+,
Prime Video, and YouTube.

## Notes

- Everything stays on your home network. Do not expose port 5000
  to the internet.
- Samsung power-on over the network only works if the TV has
  Wake-on-LAN enabled ("Power on with mobile" in TV settings).
  Power-off always works.
- ADB over your network means anyone on your Wi-Fi could send
  commands to the stick. Fine for home use; just know it.
