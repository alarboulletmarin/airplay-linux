# AirPlay Mirror

Mirror a Linux desktop to an Apple TV over Wi-Fi, with a small GTK interface.
English and French.

## Who this is for

- Linux users with an Apple TV who want to mirror their desktop over Wi-Fi
  without extra hardware or a cable. Developed and tested on GNOME/Wayland.
- People comfortable installing a few packages from the terminal.
- Personal and interoperability use. This is an unofficial community project,
  not a supported Apple product, so expect rough edges.

## How it works

The AirPlay 2 mirroring protocol (pairing, FairPlay SAP, the encrypted H.264
stream) is handled by [doubletake](https://github.com/omarroth/doubletake),
which this project bundles and drives. This project is the front-end around it:

- discovers Apple TVs on the network with mDNS (no avahi daemon required),
- starts and stops the doubletake process from a single button,
- prompts for the pairing PIN in a dialog,
- restarts capture automatically when the GNOME screencast pipeline drops
  mid-stream, so a known GStreamer renegotiation failure no longer ends the
  session.

It is a GTK client, not a reimplementation of AirPlay.

## Install

The doubletake engine is downloaded and bundled by every method below (pinned
version, checksum verified), so there is nothing else to set up. x86_64 only.

### Arch Linux

```sh
git clone https://github.com/alarboulletmarin/airplay-linux.git
cd airplay-linux
makepkg -si
```

This builds a real pacman package and pulls every dependency from the official
repositories, so no AUR helper is needed. Remove it with
`sudo pacman -R airplay-mirror`.

### Other distributions

Install the runtime libraries first.

Debian, Ubuntu:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-zeroconf \
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-pipewire
```

Fedora:

```sh
sudo dnf install python3-gobject gtk4 libadwaita python3-zeroconf \
  gstreamer1 gstreamer1-plugins-base gstreamer1-plugins-good \
  gstreamer1-plugins-bad-free gstreamer1-plugin-openh264 pipewire-gstreamer
```

Then install the app for your user, no root required:

```sh
curl -fsSL https://raw.githubusercontent.com/alarboulletmarin/airplay-linux/main/install.sh | sh
```

Or, from a checkout, run `./install.sh`. Either way the package goes into your
Python user site directory, an `airplay-mirror` launcher into `~/.local/bin`,
and a desktop entry into your applications menu. Run it again to update.

To uninstall:

```sh
rm -rf ~/.local/bin/airplay-mirror ~/.local/lib/airplay-mirror \
  ~/.local/share/applications/org.airplaymirror.AirPlayMirror.desktop \
  "$(python3 -c 'import site; print(site.getusersitepackages())')/airplay_mirror"
```

### Run from source

```sh
./scripts/fetch-doubletake.sh   # once, downloads the engine
python3 -m airplay_mirror
```

### Dependencies

For reference, the Arch package names (`makepkg -si` installs them for you):

- `python`, `python-gobject`, `gtk4`, `libadwaita`, `python-zeroconf`
- `gstreamer`, `gst-plugins-base`, `gst-plugins-good`, `gst-plugins-bad`
  (includes the OpenH264 encoder), `gst-plugin-pipewire`
- `gst-plugin-va` for hardware VA-API on Intel and AMD GPUs. `gst-plugins-ugly`
  adds the x264 software encoder.

## Usage

1. Launch AirPlay Mirror. Detected Apple TVs appear in the list. Use the
   refresh button to scan again.
2. Select a device and press Start mirroring.
3. First time on a new device: enable Pair, then enter the PIN shown on the
   Apple TV when prompted.

The language menu in the header switches between English and French. The
default follows the system locale.

## Encoders

| | VA-API | OpenH264 |
| --- | --- | --- |
| Runs on | GPU (`vah264enc`) | CPU (`openh264enc`) |
| CPU cost | near zero | moderate, fine at 1080p30 |
| Quality per bitrate | higher | good |
| Stability on GNOME | fragile today | more stable |

VA-API gives the best quality with almost no CPU, but its pipeline pins a rigid
`vapostproc` stage that does not survive the GNOME portal renegotiating the
format mid-stream, which drops the stream after a while. OpenH264 feeds a
`videoconvert` stage that absorbs those format changes. Automatic restart makes
both usable; OpenH264 is the default for stability.

## Known limitations

- The GNOME screencast portal can renegotiate the capture format mid-stream and
  make the doubletake pipeline exit. The app restarts it and shows
  "Reconnecting", then gives up after several rapid failures. A durable fix
  belongs upstream in doubletake.
- Latency is higher than Apple's native mirroring. For low-latency streaming
  without AirPlay, Sunshine and Moonlight are a better fit.
- doubletake describes itself as mostly LLM-written and not for security
  sensitive use. Treat it accordingly.

## Alternatives

There is little direct competition for a native Linux app that mirrors to an
Apple TV over AirPlay. Related projects and how they differ:

| Project | Platform | Interface | What it is |
| --- | --- | --- | --- |
| doubletake | Linux | CLI, daemon | The AirPlay mirroring engine this app drives |
| CanAIRy, WinPlay | Windows | GUI | Other front-ends around doubletake |
| doubletake-rs, easyair | Rust library, Android | varies | Ports of the engine |
| AirParrot, Mirroring360, 5KPlayer | macOS, Windows | GUI | Commercial, no Linux version |
| GNOME Network Displays | Linux | GUI | Miracast and Chromecast, not AirPlay |
| Sunshine with Moonlight, Steam Link | Linux | GUI | Low latency streaming, not AirPlay |

The engine exists and its ecosystem is growing, but a native Linux GTK client
was missing. That is the gap this project fills.

## Legal and disclaimer

- Not affiliated with, authorized by, or endorsed by Apple. AirPlay and Apple TV
  are trademarks of Apple Inc.
- Mirroring relies on doubletake, which implements the FairPlay SAP handshake
  using white-box tables derived by reverse engineering Apple software.
  Depending on your country, reverse engineering and redistributing such
  material may be restricted. You are responsible for complying with your local
  laws and with Apple's terms.
- Provided for interoperability and personal use, as is, without warranty. It
  does not touch FairPlay DRM on protected media and must not be used to
  circumvent content protection.
- Before redistributing binaries, review doubletake's own terms, since its
  embedded tables originate from Apple software.
- This package bundles and redistributes the doubletake binary, including those
  FairPlay tables. If you publish the package, you become the distributor of
  that material and take on the responsibility above.

## License

This front-end is under the GNU GPL-3.0 license (see `LICENSE`). It is an
independent program that launches doubletake as a separate process and does not
link against it. This repository contains no doubletake code: the installers
download its release binary. doubletake itself is LGPL-3.0.

## Credits

Mirroring by [doubletake](https://github.com/omarroth/doubletake).
