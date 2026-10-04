#!/bin/sh
# Vendor the doubletake engine into the source tree so `python -m airplay_mirror`
# runs self-contained from a checkout. Not needed after a package install.
set -eu

here=$(cd "$(dirname "$0")/.." && pwd)
ver=0.4.0
sha="1a19517cef2ab5c9712cdfd5995a103bdcb0f3b415cf8cccd9c1d90ffd302840"
dest="$here/airplay_mirror/vendor"

mkdir -p "$dest"
curl -fL "https://github.com/omarroth/doubletake/releases/download/v$ver/doubletake" \
    -o "$dest/doubletake"
echo "$sha  $dest/doubletake" | sha256sum -c - \
    || { echo "Checksum mismatch, aborting."; exit 1; }
chmod +x "$dest/doubletake"
echo "Vendored doubletake $ver into airplay_mirror/vendor/doubletake"
