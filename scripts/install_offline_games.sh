#!/bin/sh
# Debian/Raspberry Pi OS ARM64: user-local installation, no sudo.
set -eu
root="$HOME/fieldstation-games/root"
mkdir -p "$HOME/fieldstation-games/packages" "$root"
cd "$HOME/fieldstation-games/packages"
apt download crispy-doom freedoom libsdl2-net-2.0-0 ltris xboard gnuchess pacman xfonts-base xfonts-75dpi lincity-ng lincity-ng-data libphysfs1 libsdl2-gfx-1.0-0
for package in ./*.deb; do dpkg-deb -x "$package" "$root"; done
for font in misc 75dpi; do
    mkfontdir "$root/usr/share/fonts/X11/$font"
done
cp "$root/etc/X11/fonts/misc/xfonts-base.alias" "$root/usr/share/fonts/X11/misc/fonts.alias"
cp "$root/etc/X11/fonts/75dpi/xfonts-75dpi.alias" "$root/usr/share/fonts/X11/75dpi/fonts.alias"
# Requires existing bubblewrap, xset, mkfontdir and SDL2 desktop dependencies.
# Diagnose missing libraries with ldd before using on a different OS image.
