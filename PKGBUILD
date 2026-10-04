# Maintainer: Andrea Larboullet Marin <a.larboulletmarin@gmail.com>
pkgname=airplay-mirror
pkgver=0.1.0
pkgrel=1
pkgdesc="Self-contained AirPlay screen mirroring to an Apple TV, with a GTK interface"
arch=('x86_64')
url="https://github.com/alarboulletmarin/airplay-linux"
license=('GPL3')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'python-zeroconf'
         'gstreamer' 'gst-plugins-base' 'gst-plugins-good' 'gst-plugins-bad'
         'gst-plugin-pipewire' 'gst-plugin-va')
optdepends=('gst-plugins-ugly: x264 software encoder'
            'pipewire: Wayland screen capture'
            'xdg-desktop-portal: Wayland capture portal')
options=('!debug' '!strip')  # the bundled engine is a prebuilt stripped binary

# The doubletake engine is bundled, so installing this package pulls in no other
# AirPlay component and every remaining dependency comes from the official
# repositories. doubletake is LGPL-3.0; see the README disclaimer about
# redistributing its reverse-engineered FairPlay tables.
_doubletake_ver=0.4.0
source=("doubletake-$_doubletake_ver::https://github.com/omarroth/doubletake/releases/download/v${_doubletake_ver}/doubletake")
sha256sums=('1a19517cef2ab5c9712cdfd5995a103bdcb0f3b415cf8cccd9c1d90ffd302840')

package() {
    install -Dm755 "$srcdir/doubletake-$_doubletake_ver" \
        "$pkgdir/usr/lib/airplay-mirror/doubletake"

    local site
    site="$(python -c 'import site; print(site.getsitepackages()[0])')"
    install -d "$pkgdir$site"
    cp -r "$startdir/airplay_mirror" "$pkgdir$site/airplay_mirror"
    find "$pkgdir$site/airplay_mirror" -name __pycache__ -type d -exec rm -rf {} +

    install -Dm755 /dev/stdin "$pkgdir/usr/bin/airplay-mirror" <<'EOF'
#!/bin/sh
exec python -m airplay_mirror "$@"
EOF

    install -Dm644 "$startdir/data/org.airplaymirror.AirPlayMirror.desktop" \
        "$pkgdir/usr/share/applications/org.airplaymirror.AirPlayMirror.desktop"
    install -Dm644 "$startdir/LICENSE" \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
