#!/bin/sh
set -eu
# A physical keyboard is attached; do not auto-open the desktop touch keyboard.
if command -v gsettings >/dev/null 2>&1; then
    gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled false || true
fi
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE
systemctl --user restart fieldstation.service
systemctl --user start fieldstation-browser.service
