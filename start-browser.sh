#!/bin/sh
set -eu
# Desktop autostart imports the active Wayland/X11 display before this runs.
for attempt in $(seq 1 60); do
    if curl -fsS --max-time 2 http://127.0.0.1:8765/ >/dev/null; then
        exec /usr/bin/chromium --start-fullscreen --no-first-run --noerrdialogs --password-store=basic \
            --autoplay-policy=no-user-gesture-required --disable-session-crashed-bubble \
            --user-data-dir="$HOME/.config/fieldstation-browser" \
            http://127.0.0.1:8765/#home
    fi
    sleep 2
done
exit 1
