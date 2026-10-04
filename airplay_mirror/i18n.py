"""Minimal in-process translation catalog for English and French.

A full gettext setup is overkill for two languages and a few dozen strings,
so translations live in a plain dict. `Translator` is a callable: `tr("start")`
returns the string for the active language, with `{placeholder}` formatting.
"""

from __future__ import annotations

import locale

CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "app_name": "AirPlay Mirror",
        "search": "Search again",
        "devices_group": "Detected Apple TVs",
        "encoder": "Encoder",
        "enc_openh264": "OpenH264 (software, robust)",
        "enc_vaapi": "VA-API (hardware)",
        "enc_auto": "Automatic",
        "audio": "Audio",
        "audio_sub": "Desktop sound (may reduce stability)",
        "pair": "Pair",
        "pair_sub": "Enable for a new Apple TV (PIN)",
        "start": "Start mirroring",
        "stop": "Stop mirroring",
        "st_ready": "Ready",
        "st_searching": "Searching...",
        "st_connecting": "Connecting...",
        "st_mirroring": "Mirroring",
        "st_mirroring_time": "Mirroring {time}",
        "st_reconnecting": "Reconnecting...",
        "st_error": "Error",
        "no_devices": "No Apple TV found",
        "err_too_many": "Too many capture failures. Try again or switch encoder.",
        "err_search": "Search failed: {error}",
        "err_launch": "Cannot launch doubletake: {error}",
        "err_no_doubletake": "doubletake is not installed",
        "pin_heading": "Pairing PIN",
        "pin_body": "Enter the code shown on the Apple TV.",
        "cancel": "Cancel",
        "confirm": "Confirm",
    },
    "fr": {
        "app_name": "AirPlay Mirror",
        "search": "Rechercher",
        "devices_group": "Apple TV détectées",
        "encoder": "Encodeur",
        "enc_openh264": "OpenH264 (logiciel, robuste)",
        "enc_vaapi": "VA-API (matériel)",
        "enc_auto": "Automatique",
        "audio": "Audio",
        "audio_sub": "Son du bureau (peut réduire la stabilité)",
        "pair": "Appairer",
        "pair_sub": "Activer pour un nouvel Apple TV (PIN)",
        "start": "Démarrer la recopie",
        "stop": "Arrêter la recopie",
        "st_ready": "Prêt",
        "st_searching": "Recherche...",
        "st_connecting": "Connexion...",
        "st_mirroring": "Recopie en cours",
        "st_mirroring_time": "Recopie en cours {time}",
        "st_reconnecting": "Reconnexion...",
        "st_error": "Erreur",
        "no_devices": "Aucun Apple TV trouvé",
        "err_too_many": "Trop d'échecs de capture. Réessaie ou change d'encodeur.",
        "err_search": "Échec de la recherche : {error}",
        "err_launch": "Lancement de doubletake impossible : {error}",
        "err_no_doubletake": "doubletake n'est pas installé",
        "pin_heading": "Code d'appairage",
        "pin_body": "Saisis le code affiché sur l'Apple TV.",
        "cancel": "Annuler",
        "confirm": "Valider",
    },
}

LANGUAGES = ("en", "fr")


def system_language() -> str:
    """Return 'fr' when the system locale is French, otherwise 'en'."""
    try:
        code = (locale.getlocale()[0] or "").lower()
    except (ValueError, TypeError):
        code = ""
    return "fr" if code.startswith("fr") else "en"


class Translator:
    def __init__(self, language: str | None = None) -> None:
        self.language = language if language in LANGUAGES else system_language()

    def set_language(self, language: str) -> None:
        if language in LANGUAGES:
            self.language = language

    def __call__(self, key: str, **fields: object) -> str:
        text = CATALOG[self.language].get(key) or CATALOG["en"].get(key, key)
        return text.format(**fields) if fields else text
