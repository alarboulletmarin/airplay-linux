#!/bin/sh
# Per-user install (no root). Fetches the bundled doubletake engine, copies the
# package into the user site directory, adds a launcher on PATH, and registers
# the desktop entry. Runs from a checkout, or standalone through `curl | sh`.
set -eu

repo_tarball="https://github.com/alarboulletmarin/airplay-linux/archive/refs/heads/main.tar.gz"

here=$(cd "$(dirname "$0")" && pwd)
if [ ! -d "$here/airplay_mirror" ]; then
    echo "Downloading AirPlay Mirror..."
    here=$(mktemp -d)
    trap 'rm -rf "$here"' EXIT
    curl -fsSL "$repo_tarball" | tar -xz -C "$here" --strip-components=1
fi
site=$(python3 -c 'import site; print(site.getusersitepackages())')
bindir="$HOME/.local/bin"
libdir="$HOME/.local/lib/airplay-mirror"
appdir="$HOME/.local/share/applications"

doubletake_ver=0.4.0
doubletake_url="https://github.com/omarroth/doubletake/releases/download/v${doubletake_ver}/doubletake"
doubletake_sha="1a19517cef2ab5c9712cdfd5995a103bdcb0f3b415cf8cccd9c1d90ffd302840"

echo "Checking runtime libraries..."
missing=""
python3 -c 'import gi; gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")' 2>/dev/null \
    || missing="$missing python-gobject/gtk4/libadwaita"
python3 -c 'import zeroconf' 2>/dev/null || missing="$missing python-zeroconf"
command -v gst-inspect-1.0 >/dev/null 2>&1 || missing="$missing gstreamer"
if [ -n "$missing" ]; then
    echo "Missing:$missing"
    echo "Install them first, the app will not start without them:"
    echo "  https://github.com/alarboulletmarin/airplay-linux#other-distributions"
fi

echo "Fetching the doubletake engine..."
mkdir -p "$libdir"
curl -fL "$doubletake_url" -o "$libdir/doubletake"
echo "$doubletake_sha  $libdir/doubletake" | sha256sum -c - \
    || { echo "Checksum mismatch, aborting."; exit 1; }
chmod +x "$libdir/doubletake"

echo "Installing to $site ..."
mkdir -p "$site" "$bindir" "$appdir"
rm -rf "$site/airplay_mirror"
cp -r "$here/airplay_mirror" "$site/airplay_mirror"

cat > "$bindir/airplay-mirror" <<EOF
#!/bin/sh
exec python3 -m airplay_mirror "\$@"
EOF
chmod +x "$bindir/airplay-mirror"

cp "$here/data/org.airplaymirror.AirPlayMirror.desktop" "$appdir/"
update-desktop-database "$appdir" 2>/dev/null || true

echo "Done. Launch 'AirPlay Mirror' from your applications, or run: airplay-mirror"
case ":$PATH:" in
    *":$bindir:"*) ;;
    *) echo "Note: add $bindir to your PATH to use the 'airplay-mirror' command." ;;
esac
