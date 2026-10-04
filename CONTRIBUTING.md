# Contributing

Thanks for your interest. This is a small GTK front-end around the doubletake
mirroring engine. Contributions that keep it small and focused are welcome.

## Run from source

Vendor the engine once, then run:

```sh
./scripts/fetch-doubletake.sh
python -m airplay_mirror
```

Runtime dependencies: `python-gobject`, `gtk4`, `libadwaita`, `python-zeroconf`,
and GStreamer with an H.264 encoder. See the README for the full list. If a
`doubletake` binary is already on PATH, the vendoring step is optional.

## Project layout

```
airplay_mirror/
  discovery.py   mDNS discovery of AirPlay receivers (zeroconf)
  session.py     drives the doubletake process, restarts, PIN input
  i18n.py        English and French translation catalog
  app.py         GTK4/Adwaita interface
  __main__.py    entry point
  vendor/        bundled doubletake engine (fetched, not committed)
scripts/         helper scripts (fetch the engine)
data/            desktop entry
```

## Style

- Python code and comments in English. Keep functions small and named after
  what they do.
- No new runtime dependency unless a few lines cannot do the same job.
- Match the existing style. There is no build step and no framework to learn.

## Translations

Strings live in `airplay_mirror/i18n.py`. To add or fix a string, edit the `en`
and `fr` entries in `CATALOG`. To add a language, add a new code to `CATALOG`
and `LANGUAGES`, then add its button in `_build_language_button` in `app.py`.

## Reporting issues

Include your distribution, desktop session (X11 or Wayland), GPU, the Apple TV
model, the selected encoder, and the doubletake output. For capture failures,
run doubletake directly with `-debug` and attach the relevant lines.

## Publishing to the AUR

Not published yet. To let anyone install with `yay -S airplay-mirror`:

1. Tag a release: `git tag vX.Y.Z && git push --tags`.
2. Point the PKGBUILD at that tag instead of the local checkout. Add a source
   line and read from `$srcdir/$pkgname` in `package()`:

   ```sh
   source=("git+$url.git#tag=v$pkgver")
   sha256sums=('SKIP')
   ```

3. Generate the metadata and push to the AUR:

   ```sh
   makepkg --printsrcinfo > .SRCINFO
   git clone ssh://aur@aur.archlinux.org/airplay-mirror.git aur
   cp PKGBUILD .SRCINFO aur/
   cd aur && git add -A && git commit -m "airplay-mirror 0.1.0" && git push
   ```

The last step needs an AUR account with an SSH key.

## License of contributions

By contributing, you agree that your contribution is licensed under the
project's license (see `LICENSE`).
