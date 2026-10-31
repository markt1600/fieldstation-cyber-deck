# FieldStation Cyber Deck

A Raspberry Pi touchscreen interface for an offline library, music and video, art, learning, and portable computing. Designed around a 1024 × 600 display with large touch controls.

## Features

- Content-first Library, Education, Languages, and Contents & Search pages.
- Local Wikipedia/Kiwix and Gutenberg browsing, book covers, reading controls and bookmarks.
- Music categories, shuffle, playlists, favorites, playlist editing and optional metadata-based AI playlist generation.
- Music-video and concert thumbnails with artist captions; local video playback through VLC.
- Spotify integration and controls for a separately installed PipeWire EQ/limiter chain.
- Offline art galleries and randomized full-screen exhibitions.
- Offline maps with a world overview, detailed Southeast Asia coverage, highest-detail Singapore/Malaysia maps, local place search, and regional driving/walking/cycling route planning.
- Battery voltage, UPS-reported percentage, measured-runtime estimates, and particulate-sensor readings on supported hardware.
- Wi-Fi controls and confirmed reboot/shutdown actions in the sidebar.
- Embedded websites with a persistent sidebar and maximize/restore controls.
- Optional local Codex terminal and read-only VeraCrypt file browsing.

## Offline maps

Open **Offline maps** in the offline sidebar. The viewer stays inside Fieldstation and supports touch navigation, coverage selection, place-name search and maximising. Expand **Offline directions**, select start and destination on the map, choose a travel mode, then calculate a route. Tap a direction to view that turn on the map.

The deployed collection (28 October 2026) uses about 2.6 GB on the internal SSD, including dependencies and the address-search source/index:

| Coverage | Map detail | Archive size |
| --- | --- | --- |
| World | Zoom 0-8 overview | 560 MB |
| Southeast Asia | Zoom 0-12 | 798 MB |
| Singapore and Malaysia, including Malaysian Borneo | Zoom 0-15, source maximum | 516 MB |

Files live in `/media/library/Maps` (override with `FIELD_MAPS` for the web server). MapLibre, PMTiles, fonts and sprites are served locally; viewing does not use a CDN. GeoNames provides world-city search plus Singapore/Malaysia place records. An additional 939,329-record Geofabrik/OpenStreetMap index supports streets, landmarks, mapped house numbers and postcodes in Singapore/Malaysia. Search accepts common abbreviations and prioritises results near the map centre. Address coverage is incomplete, and unit numbers generally are not available. Map zoom beyond the source maximum enlarges existing detail.

BRouter runs as the user service `fieldstation-routing`, bound only to `127.0.0.1:17777`. Regional road segments cover Singapore/Malaysia. Routing is offline planning with distance, estimated duration and turn instructions, not live traffic, spoken navigation or automatic GPS tracking. Its walking profile is derived from the bundled pedestrian template, with mountain difficulty limited to SAC T1 and no hiking-route preference. Route availability depends on downloaded OpenStreetMap roads and access tags; route estimates are not guarantees of access.

Provision on a 64-bit Raspberry Pi with Python 3.12+, curl and a mounted writable SSD:

```sh
python3 scripts/install_offline_maps.py
python3 scripts/install_map_places.py
python3 scripts/install_map_addresses.py
python3 scripts/install_offline_routing.py
```

The scripts download map data and local runtime dependencies; the routing installer enables its user service. Map archives are published only after PMTiles verification. There is no automatic map update schedule. The map installer preserves existing finished archives, so it is not an in-place update command. Keep download files and runtime binaries out of Git.

Sources and attribution: [Protomaps / OpenStreetMap](https://docs.protomaps.com/basemaps/downloads), [BRouter](https://github.com/abrensch/brouter), and [GeoNames, CC BY 4.0](https://www.geonames.org/). OpenStreetMap attribution remains visible on the map. Dependency licence files are retained with downloaded viewer assets.

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

`start-browser.sh`, `desktop-session.sh`, and `fieldstation-browser.service` provide fullscreen-launch examples (F11 toggles fullscreen). Review paths before installing them. The supplied launcher uses `--password-store=basic` to avoid keyring prompts on the original dedicated device; this does not provide OS-keyring protection for stored browser login data. Adjust it for your deployment.

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


## Offline games and learning

The offline Games page provides graphical launch tiles for Crispy Doom with Freedoom Phase 2, LTris 2, XBoard/GNU Chess, a Pac-Man-style maze game and LinCity-NG. Games open in the local desktop; close the game window to return. The original commercial Doom levels are not bundled. Install Debian ARM64 packages into the user directory with `sh scripts/install_offline_games.sh`. This assumes the Pi desktop SDL2 dependencies, bubblewrap, xset and mkfontdir are already present; check missing libraries on other images. Launch requests are fixed allowlisted choices restricted to the local same-origin browser.

Kolibri 0.19.5 is installed in a separate Python environment at `~/fieldstation-kolibri`. Create it with `python3 -m venv ~/fieldstation-kolibri` and `~/fieldstation-kolibri/bin/pip install kolibri==0.19.5`, then run `python3 scripts/setup_offline_learning.py`. All course data and local learner progress live at `/media/library/Education/Kolibri` on the SSD. Setup generates a private local administrator credential in `~/.config/fieldstation-kolibri-admin` (mode 0600); never commit it. Learners can browse as guests or create local learner profiles; an online Khan Academy account is not needed.

Kolibri listens on loopback ports 8085 and 8086. Fieldstation proxies `/kolibri/` for its local embedded view; exercise content remains on the separate 8086 origin. Education links to a learning overview with download progress. The official English US-curriculum channel ID is `c9d7f950ab6b5a1199e3d6c10d7f0103`; its catalogue contains about 67 GB of files. `scripts/download_khan.py` imports a sample first and then the complete channel, resuming existing downloads. On the device this runs as the enabled `fieldstation-khan-download` user service, with logs on the SSD. Content is not bundled in GitHub and retains its source licences.

The Chromium launcher uses `--hide-crash-restore-bubble` to suppress the restore-tabs prompt at startup while retaining the normal full-screen mode and F11 exit.


### Additional offline games

Run `python3 scripts/install_extra_games.py` on the Pi to download Debian ARM64 packages and extract them into `~/fieldstation-games/root`, without changing system packages. The installer also compiles the local GSettings schemas. Existing base games use `scripts/install_offline_games.sh`.

Games now include SuperTuxKart, SuperTux, Frozen Bubble, OpenTTD, Hedgewars, Blob Wars, Warzone 2100, Pioneers, GTKAtlantic, Aisleriot, FreeCell, Spider and Mahjongg. The Games page groups graphical cards by genre. Aisleriot provides over 80 solitaire variants; Mahjongg is tile-matching solitaire.

Additional games use a read-only merged `/usr` runtime with minimal standard devices and explicitly bound graphics devices. Warzone uses its native binary and an explicit data path. GTKAtlantic and its local monopd server share a private network namespace; connect to `localhost:1234` in the client. This Monopoly-style client has no built-in AI opponents. Pioneers includes local server and AI executables. No commercial game assets are required.

Short desktop launch checks were performed; these do not establish performance across all levels. Start 3D games with modest graphics settings. Original package artwork and licence notices are included in `dist/game-art/credits.txt`.


### Offline productivity tools

The sidebar's **Calculator, translate & docs** page contains a local scientific calculator, text translation and fixed desktop launch buttons for the installed LibreOffice Writer, Calc and Draw. Calculator expressions use a bounded parser (no JavaScript eval). Document launch and translation POST endpoints require the Pi's local same-origin browser.

Translation supports English, Japanese, Malay, French and Korean using eight Argos language models and CPU CTranslate2 inference. Non-English pairs pivot through English. Models and a Python virtualenv are stored under `/media/library/Tools/Translation` (about 1 GB). Create the venv with `python3 -m venv /media/library/Tools/Translation/venv`, install `ctranslate2 sentencepiece` into it, then run `python3 scripts/install_translation.py`. Model source URLs are recorded on the SSD. Translation makes no network requests and does not persist submitted text. Requests are limited to 2,000 characters, one at a time, with a 90-second timeout. Machine translation quality varies, especially across pivot pairs and Malay/Indonesian vocabulary.

Validated all eight direct directions and a French-to-Japanese pivot, calculator arithmetic/functions/precedence, local-origin rejection, and DOCX/PDF export. Word and PDF editing may alter complex document layouts; save a copy before editing.
