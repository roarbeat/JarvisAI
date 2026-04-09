"""
Medien-Steuerung fuer Jarvis.
Spotify API, YouTube, App-Lautstaerke, Anruf-Stummschaltung.
"""
import os
import time
import urllib.parse
import subprocess

from browser import open_in_brave
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI


# ============================================================
#  SPOTIFY
# ============================================================

_spotify_instance = None   # Singleton – einmalige Auth, danach gecacht


def _get_spotify():
    """
    Gibt ein authentifiziertes Spotipy-Objekt zurueck.

    Authentifizierungs-Reihenfolge:
      1. PKCE-Flow (empfohlen fuer Desktop – nur CLIENT_ID noetig, kein Server)
      2. OAuth-Flow mit lokalem Callback-Server auf Port 9090 (Fallback)

    Beim ersten Aufruf oeffnet sich der Browser einmalig zur Freigabe.
    Das Token wird in .spotify_cache gecacht – danach kein Login mehr noetig.
    """
    global _spotify_instance
    if _spotify_instance is not None:
        return _spotify_instance

    try:
        import spotipy
    except ImportError:
        return None

    scope = (
        "user-read-playback-state user-modify-playback-state "
        "user-read-currently-playing playlist-read-private "
        "user-library-modify"
    )
    cache = os.path.join(os.path.dirname(__file__), ".spotify_cache")

    # --- Weg 1: PKCE (Desktop-optimiert, kein Client-Secret noetig) ---
    try:
        from spotipy.oauth2 import SpotifyPKCE
        auth = SpotifyPKCE(
            client_id=SPOTIFY_CLIENT_ID,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=scope,
            cache_path=cache,
            open_browser=True,
        )
        sp = spotipy.Spotify(auth_manager=auth)
        sp.current_user()   # Verbindung testen
        _spotify_instance = sp
        return sp
    except Exception:
        pass   # Weiter zu Weg 2

    # --- Weg 2: OAuth mit lokalem Callback-Server auf Port 9090 ---
    try:
        from spotipy.oauth2 import SpotifyOAuth
        auth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=scope,
            cache_path=cache,
            open_browser=True,
        )
        sp = spotipy.Spotify(auth_manager=auth)
        sp.current_user()
        _spotify_instance = sp
        return sp
    except Exception:
        return None


def spotify_control(action, query=None, playlist=None, device_id=None):
    """Spotify steuern: play, pause, next, prev, playlist, suche."""
    if not SPOTIFY_CLIENT_ID:
        # Fallback: Medientasten senden
        import pyautogui
        key_map = {
            "next": "nexttrack",
            "prev": "prevtrack",
            "previous": "prevtrack",
            "pause": "playpause",
            "play": "playpause",
            "stop": "playpause",
        }
        key = key_map.get(action.lower())
        if key:
            pyautogui.press(key)
            return f"Medientaste '{action}' gesendet (kein Spotify-API-Key konfiguriert)."
        return "Spotify-API nicht konfiguriert (SPOTIFY_CLIENT_ID in config.py eintragen)."

    sp = _get_spotify()
    if not sp:
        return "Spotify-Verbindung fehlgeschlagen – bitte spotipy installieren und API-Keys pruefen."

    try:
        # Aktives Geraet ermitteln
        devices = sp.devices()
        active = next((d for d in devices.get("devices", []) if d["is_active"]), None)
        if not active and devices.get("devices"):
            active = devices["devices"][0]
        dev_id = device_id or (active["id"] if active else None)

        action = action.lower()

        if action in ("next", "naechster", "skip"):
            sp.next_track(device_id=dev_id)
            return "Naechster Song."

        elif action in ("prev", "previous", "zurueck", "vorheriger"):
            sp.previous_track(device_id=dev_id)
            return "Vorheriger Song."

        elif action in ("pause", "stop"):
            sp.pause_playback(device_id=dev_id)
            return "Spotify pausiert."

        elif action in ("play", "weiter", "resume"):
            sp.start_playback(device_id=dev_id)
            return "Spotify laeuft."

        elif action in ("current", "aktuell", "was_laeuft"):
            t = sp.currently_playing()
            if t and t.get("item"):
                name = t["item"]["name"]
                artist = t["item"]["artists"][0]["name"]
                return f"Aktuell laeuft: {name} von {artist}."
            return "Momentan laeuft nichts."

        elif action in ("playlist", "playlist_wechseln"):
            if not query:
                return "Welche Playlist soll ich abspielen?"
            results = sp.search(q=query, type="playlist", limit=1)
            items = results.get("playlists", {}).get("items", [])
            if items:
                uri = items[0]["uri"]
                sp.start_playback(device_id=dev_id, context_uri=uri)
                return f"Playlist '{items[0]['name']}' wird abgespielt."
            return f"Keine Playlist '{query}' gefunden."

        elif action in ("suche", "search", "song_suchen"):
            if not query:
                return "Was soll ich suchen?"
            results = sp.search(q=query, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                uri = items[0]["uri"]
                sp.start_playback(device_id=dev_id, uris=[uri])
                name = items[0]["name"]
                artist = items[0]["artists"][0]["name"]
                return f"Spiele '{name}' von {artist}."
            return f"Song '{query}' nicht gefunden."

        elif action in ("shuffle", "zufaellig"):
            current = sp.current_playback()
            state = not (current.get("shuffle_state", False) if current else False)
            sp.shuffle(state, device_id=dev_id)
            return f"Shuffle {'an' if state else 'aus'}."

        elif action in ("volume", "lautstaerke"):
            if query and str(query).isdigit():
                sp.volume(int(query), device_id=dev_id)
                return f"Spotify-Lautstaerke auf {query}%."
            return "Kein Lautstaerke-Wert angegeben."

        elif action in ("like", "gefaellt_mir"):
            t = sp.currently_playing()
            if t and t.get("item"):
                sp.current_user_saved_tracks_add([t["item"]["id"]])
                return f"'{t['item']['name']}' geliked."
            return "Kein aktiver Song."

        return f"Unbekannte Spotify-Aktion: {action}"

    except Exception as e:
        return f"Spotify-Fehler: {e}"


# ============================================================
#  YOUTUBE
# ============================================================

def youtube_action(action, query=None):
    """YouTube-Videos suchen und im Browser oeffnen."""
    try:
        action = action.lower()

        if action in ("search", "suche", "suchen", "play", "abspielen"):
            if not query:
                open_in_brave("https://www.youtube.com")
                return "YouTube geoeffnet."
            encoded = urllib.parse.quote(query)
            # Direkt das erste Ergebnis oeffnen via ytsearch
            url = f"https://www.youtube.com/results?search_query={encoded}"
            open_in_brave(url)
            return f"YouTube-Suche nach '{query}' geoeffnet."

        elif action in ("home", "start"):
            open_in_brave("https://www.youtube.com")
            return "YouTube-Startseite geoeffnet."

        elif action == "trending":
            open_in_brave("https://www.youtube.com/feed/trending")
            return "YouTube Trending geoeffnet."

        return "Unbekannte YouTube-Aktion."
    except Exception as e:
        return f"YouTube-Fehler: {e}"


# ============================================================
#  APP-LAUTSTAERKE (per Prozess)
# ============================================================

def set_app_volume(app_name, level):
    """Lautstaerke einer einzelnen App regeln (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities
        level_f = max(0.0, min(1.0, int(level) / 100.0))

        from pycaw.pycaw import ISimpleAudioVolume
        sessions = AudioUtilities.GetAllSessions()
        found = False
        for session in sessions:
            if session.Process and app_name.lower() in session.Process.name().lower():
                sav = session._ctl.QueryInterface(ISimpleAudioVolume)
                sav.SetMasterVolume(level_f, None)
                found = True

        if found:
            return f"Lautstaerke von '{app_name}' auf {level}% gesetzt."
        return f"App '{app_name}' nicht gefunden oder laeuft nicht."
    except Exception as e:
        return f"Fehler bei App-Lautstaerke: {e}"


def get_app_volume(app_name):
    """Aktuelle Lautstaerke einer App abfragen."""
    try:
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and app_name.lower() in session.Process.name().lower():
                sav = session._ctl.QueryInterface(ISimpleAudioVolume)
                vol = int(sav.GetMasterVolume() * 100)
                return f"'{app_name}' laeuft bei {vol}%."
        return f"App '{app_name}' nicht aktiv."
    except Exception as e:
        return f"Fehler: {e}"


def set_all_app_volumes(level):
    """Lautstaerke aller laufenden Apps auf einen Wert setzen."""
    try:
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
        level_f = max(0.0, min(1.0, int(level) / 100.0))
        sessions = AudioUtilities.GetAllSessions()
        count = 0
        for session in sessions:
            if session.Process:
                try:
                    sav = session._ctl.QueryInterface(ISimpleAudioVolume)
                    sav.SetMasterVolume(level_f, None)
                    count += 1
                except Exception:
                    pass
        return f"Lautstaerke von {count} Apps auf {level}% gesetzt."
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================
#  VIDEO-ANRUF STUMMSCHALTEN (Teams / Zoom)
# ============================================================

def mute_call(app="auto"):
    """Aktiven Video-Anruf stummschalten (Teams: Strg+Shift+M, Zoom: Alt+A)."""
    try:
        import pyautogui
        import psutil

        app = app.lower()

        # Auto-Erkennung
        if app == "auto":
            running = [p.name().lower() for p in psutil.process_iter(["name"])]
            if any("teams" in n for n in running):
                app = "teams"
            elif any("zoom" in n for n in running):
                app = "zoom"
            elif any("discord" in n for n in running):
                app = "discord"
            else:
                app = "teams"

        if app in ("teams", "microsoft teams"):
            pyautogui.hotkey("ctrl", "shift", "m")
            return "Mikrofon in Teams umgeschaltet (Strg+Shift+M)."
        elif app == "zoom":
            pyautogui.hotkey("alt", "a")
            return "Mikrofon in Zoom umgeschaltet (Alt+A)."
        elif app == "discord":
            # Discord Shortcut anpassbar – Standard: kein globaler Shortcut
            pyautogui.hotkey("ctrl", "shift", "m")
            return "Stummschaltung in Discord (Strg+Shift+M)."
        elif app == "google meet":
            pyautogui.hotkey("ctrl", "d")
            return "Mikrofon in Google Meet umgeschaltet (Strg+D)."

        return f"App '{app}' fuer Stummschaltung nicht unterstuetzt."
    except Exception as e:
        return f"Fehler beim Stummschalten: {e}"


def camera_toggle(app="auto"):
    """Kamera in Video-Anruf an/aus."""
    try:
        import pyautogui
        import psutil

        running = [p.name().lower() for p in psutil.process_iter(["name"])]

        if any("teams" in n for n in running):
            pyautogui.hotkey("ctrl", "shift", "o")
            return "Kamera in Teams umgeschaltet."
        elif any("zoom" in n for n in running):
            pyautogui.hotkey("alt", "v")
            return "Kamera in Zoom umgeschaltet."
        elif any("meet" in n for n in running):
            pyautogui.hotkey("ctrl", "e")
            return "Kamera in Google Meet umgeschaltet."

        return "Kein laufender Video-Anruf gefunden."
    except Exception as e:
        return f"Fehler beim Kamera-Toggle: {e}"


# ============================================================
#  MEDIENTASTEN (Fallback)
# ============================================================

def media_key(action):
    """Systemweite Medientaste druecken (unabhaengig von der App)."""
    try:
        import pyautogui
        key_map = {
            "play":  "playpause",  "pause": "playpause",
            "next":  "nexttrack",  "naechster": "nexttrack",
            "prev":  "prevtrack",  "zurueck": "prevtrack",
            "stop":  "stop",
        }
        key = key_map.get(action.lower(), "playpause")
        pyautogui.press(key)
        return f"Medientaste '{key}' gedrueckt."
    except Exception as e:
        return f"Fehler: {e}"
