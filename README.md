# FieldStation Cyber Deck

A Raspberry Pi touchscreen interface for an offline library, music and video, art, learning, and portable computing. Designed around a 1024 × 600 display with large touch controls.

## Features

- Content-first Library, Education, Languages, and Contents & Search pages.
- Local Wikipedia/Kiwix and Gutenberg browsing, book covers, reading controls and bookmarks.
- Music categories, shuffle, playlists, favorites, playlist editing and optional metadata-based AI playlist generation.
- Music-video and concert thumbnails with artist captions; local video playback through VLC.
- Spotify integration and controls for a separately installed PipeWire EQ/limiter chain.
- Offline art galleries and randomized full-screen exhibitions.
- Battery voltage, UPS-reported percentage, measured-runtime estimates, and particulate-sensor readings on supported hardware.
- Wi-Fi controls and confirmed reboot/shutdown actions in the sidebar.
- Embedded websites with a persistent sidebar and maximize/restore controls.
- Optional local Codex terminal and read-only VeraCrypt file browsing.

## Hardware

The 3D-printed Peli 1400 enclosure (print files, source scripts and assembly notes) is in [`hardware/`](hardware/README.md).

## Status

This is a source snapshot of an actively used, customized Raspberry Pi installation, not a turnkey operating-system image. Hardware services, external applications, downloaded collections, and generated catalogue databases must be provisioned separately. Some paths and device choices reflect the original build. Runtime estimates are calibrated to that build and should not be treated as universal battery measurements.

## Run

Use Python 3.10 or newer. Raspberry Pi OS with a desktop is the primary target. Install the Python dependencies in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python server.py --help
python server.py --library "/media/library/Offline Library" --media "/media/library/YouTube Downloads"
```

Open http://127.0.0.1:8765 in Chromium. The interface does not require a frontend build step; assets live in `dist/`.

Optional integrations require their own software: VLC, FFmpeg/ffprobe, Kiwix Server, PipeWire/WirePlumber, NetworkManager, libgpiod tools, VeraCrypt, LibreOffice, and Codex CLI as applicable. Optional local language-model files are not included. `codex_terminal.py` also requires xterm.js, its CSS and fit addon in `terminal-assets/`; third-party browser bundles are not vendored here.

Gutenberg discovery requires a separately generated `data/gutenberg.sqlite3`; art discovery requires a local collection/index. These generated/downloaded assets are intentionally excluded. The core catalogue scans configured library paths; specific integrations may need additional provisioning.

`start-browser.sh`, `desktop-session.sh`, and `fieldstation-browser.service` provide kiosk-launch examples. Review paths before installing them. The supplied launcher uses `--password-store=basic` to avoid keyring prompts on the original dedicated device; this does not provide OS-keyring protection for stored browser login data. Adjust it for your deployment.

## Source layout

- `server.py`: local HTTP application and integration routes.
- `dist/`: browser interface, styling, readers and players.
- `media_catalogue.py`, `catalogue.py`, `topics.py`: content indexing.
- `playlists.py`, `playlist_ai.py`, `category_playlists.py`: playlists and optional AI generation.
- `audio_settings.py`, `audio_compat.py`: EQ settings and cached lossless compatibility conversion.
- `battery_status.py`, `air_quality.py`: hardware readings.
- `wifi.py`, `power_control.py`: local device controls.
- `sharing.py`, `private_files.py`: document sharing and isolated private-file access.

## Data and security

Media files, personal playlists, private containers, generated databases, battery history, credentials, SSH keys, browser profiles, and downloaded tools/models are not included. Never add these to the repository. The sample topic list includes its source attribution in `data/wiki-topics-source.json`.

Most content is used locally. Online services, embedded websites, Spotify and Codex require internet access. AI playlist generation sends selected music metadata, not audio. Read-only sharing uses a separate LAN listener; review its reachability before deploying on an untrusted network. Privileged device actions require local same-origin requests and normal operating-system permissions.

## Development and deployment

Check Python syntax with `python -m compileall -q .` in a source-only checkout, and JavaScript syntax with `node --check dist/<changed-file>.js`. Test navigation and playback on the target touchscreen. UI confirmations can be tested without actually rebooting or powering off.

Commit reviewed source changes here before deploying them to the device. Keep machine-specific configuration and content backups separately. This repository does not yet include an automated installer or full integration-test suite.
