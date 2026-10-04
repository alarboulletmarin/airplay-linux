"""AirPlay Mirror: a GTK front-end for mirroring a Linux screen to an Apple TV.

The heavy lifting (AirPlay 2 handshake, FairPlay SAP, encrypted video stream)
is done by the external `doubletake` binary. This package only discovers
receivers, drives the doubletake process, restarts it when the GNOME capture
pipeline drops, and provides a bilingual GTK interface.
"""

__version__ = "0.1.0"
