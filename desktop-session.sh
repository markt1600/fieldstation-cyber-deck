#!/bin/sh
set -eu
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE
systemctl --user restart fieldstation.service
systemctl --user start fieldstation-browser.service
