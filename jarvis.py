"""
J A R V I S - Lokaler KI-Sprachassistent v4.1
===============================================
Wake-Word: "Jarvis"  |  Browser: Brave
LLM: Ollama          |  STT: Whisper  |  TTS: Piper
Sprache: Deutsch

Neu in v4.1:
  - "Jarvis stopp" unterbricht Sprachausgabe
  - Folgefragen moeglich ohne erneutes Wake-Word
  - Wetter wird direkt gesprochen (kein zweiter LLM-Call)
  - Robusteres Action-Parsing

Module:
  config.py        - Konfiguration & Konstanten
  phonetic.py      - Phonetik-Korrekturen fuer TTS
  browser.py       - Brave, APP_MAP, open_app
  weather.py       - Wetter-Abfragen
  smart_home.py    - Home-Assistant-Integration
  tts.py           - Speaker (Piper TTS, unterbrechbar)
  stt.py           - Listener (Whisper + VAD + Folgefragen)
  actions.py       - execute_action Dispatcher
  llm.py           - ask_llm, System-Prompt
  pc_control.py    - Maus, Fenster, Clipboard, Scroll, Monitor
  media.py         - Spotify, YouTube, App-Lautstaerke, Anrufe
  automation.py    - Timer, Alarm, Routine, Nacht-Modus
  productivity.py  - Rechner, Wiki, Notizen, Kalender, E-Mail
  system_monitor.py- CPU/RAM/GPU, Prozesse, Netzwerk, Updates
  communication.py - WhatsApp, E-Mail senden, Discord
  ai_features.py   - Screenshot-Analyse, Gedaechtnis
"""

import os
import sys
import shutil
import time
import threading

import sounddevice as sd
import ollama

from config  import PIPER_EXE, PIPER_VOICE, USERNAME
from browser import BRAVE_EXE
from tts     import Speaker, get_stop_event, reset_stop_event
from stt     import Listener
from actions import execute_action
from llm     import ask_llm
import automation


# ============================================================
#  AKTIONEN DIE EIN ERGEBNIS ZURUECKLIEFERN
# ============================================================

_ERGEBNIS_AKTIONEN = {
    "get_weather",
    "system_stats", "disk_space", "list_processes",
    "network_speed", "network_info", "ping", "system_summary",
    "calculate", "convert_currency", "convert_unit",
    "wikipedia", "read_note", "list_notes", "read_emails", "read_calendar",
    "analyze_screenshot", "read_clipboard", "summarize_clipboard",
    "summarize_document", "get_preference", "list_preferences",
    "list_timers",
}

# Aktionen bei denen der LLM-speak-Text VOR der Aktion gesprochen wird
_SOFORT_SPRECHEN = {
    "open_app", "close_app", "web_search", "open_website",
    "set_volume", "volume_up", "volume_down", "volume_mute",
    "set_brightness", "open_settings", "shutdown", "restart",
    "sleep", "lock", "control_home", "spotify", "youtube",
    "media_key", "night_light", "bluetooth_toggle", "wifi_toggle",
    "set_timer", "set_alarm", "remind_me", "morning_routine", "night_mode",
    "screenshot", "save_note", "type_text", "run_command",
    "whatsapp_send", "send_email", "compose_email",
    "discord_send", "discord_open",
    "save_preference", "switch_language",
}

# Schluesselwoerter fuer Stopp
_STOPP_WORTE = {"stopp", "stop", "aufhoer", "halt", "ruhig", "schweig"}

# Schluesselwoerter fuer Abbruch-Folgefrage
_ABBRUCH_WORTE = {"danke", "okay", "ok", "tschues", "bye", "genug", "reicht"}


def _ist_stoppbefehl(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in _STOPP_WORTE)


def _ist_abbruchbefehl(text: str) -> bool:
    t = text.lower().strip()
    # Nur kurze Saetze pruefen (lange Saetze sind echte Befehle)
    if len(t) > 30:
        return False
    return any(w in t for w in _ABBRUCH_WORTE)


def _start_interrupt_thread(listener: Listener, speaker: Speaker):
    """Startet Hintergrund-Thread der auf 'Stopp' hoert waehrend Jarvis spricht."""
    stop_event = get_stop_event()
    end_event  = threading.Event()   # signalisiert Thread-Ende

    def _run():
        listener.listen_for_stop_word(stop_event)
        end_event.set()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t, end_event


def _process_command(command: str, speaker: Speaker, listener: Listener) -> bool:
    """Verarbeitet einen Befehl. Gibt True zurueck wenn Jarvis weiterlaufen soll."""
    if not command:
        speaker.say("Nicht verstanden, bitte wiederholen.")
        return True

    print(f"  > \"{command}\"")

    # Stopp-Befehl direkt abfangen
    if _ist_stoppbefehl(command):
        speaker.stop()
        return True

    t_start  = time.time()
    speak, action = ask_llm(command)
    print(f"  [Zeit] KI-Antwort: {time.time() - t_start:.2f}s")

    act = action.get("action", "") if action else ""

    # ---- Sprachausgabe & Ausfuehrung ----

    reset_stop_event()
    stop_thread, end_event = _start_interrupt_thread(listener, speaker)

    if act in _ERGEBNIS_AKTIONEN:
        # Erst intro-Satz sprechen, dann Aktion ausfuehren, dann Ergebnis sprechen
        if speak and not get_stop_event().is_set():
            speaker.say(speak)
        if action and not get_stop_event().is_set():
            result = execute_action(action)
            print(f"  -> {result}")
            if result and not get_stop_event().is_set():
                speaker.say(str(result))

    elif act in _SOFORT_SPRECHEN:
        # Erst sprechen, dann Aktion ausfuehren
        if speak and not get_stop_event().is_set():
            speaker.say(speak)
        if action and not get_stop_event().is_set():
            result = execute_action(action)
            print(f"  -> {result}")
            # Fehlermeldungen sprechen
            if result and isinstance(result, str):
                r_low = result.lower()
                if any(w in r_low for w in ["fehler", "nicht gefunden", "konnte nicht", "error"]):
                    speaker.say(result)

    elif action:
        # Sonstige Aktionen
        if speak and not get_stop_event().is_set():
            speaker.say(speak)
        result = execute_action(action)
        print(f"  -> {result}")
        if result and not get_stop_event().is_set():
            r_low = str(result).lower()
            if any(w in r_low for w in ["fehler", "nicht", "error"]):
                speaker.say(str(result))

    else:
        # Nur Antwort, keine Aktion
        if speak and not get_stop_event().is_set():
            speaker.say(speak)

    # Interrupt-Thread sauber beenden (MUSS vor Folgefragen passieren!)
    get_stop_event().set()
    end_event.wait(timeout=2.0)
    # Kurz warten damit InputStream im Thread geschlossen wird
    time.sleep(0.1)
    reset_stop_event()

    print(f"  [Zeit] Gesamt: {time.time() - t_start:.2f}s\n")
    return True


def main():
    print("\n  J A R V I S  v4.1")
    print(f"  Browser: {'Brave' if BRAVE_EXE else 'Standard'}")
    print("  Strg+C zum Beenden\n")

    # Voraussetzungen pruefen
    errors = []
    if not shutil.which("ollama"):
        errors.append("Ollama fehlt – bitte installieren")
    else:
        try:
            ollama.list()
        except Exception:
            errors.append("Ollama-Server laeuft nicht – 'ollama serve' ausfuehren")

    if not os.path.exists(PIPER_EXE):
        errors.append("piper.exe fehlt – SETUP.bat ausfuehren")
    if not os.path.exists(PIPER_VOICE):
        errors.append("Piper-Stimme fehlt – SETUP.bat ausfuehren")
    try:
        sd.query_devices(kind="input")
    except Exception:
        errors.append("Kein Mikrofon gefunden")

    if errors:
        for e in errors:
            print(f"  ! {e}")
        input("\n  Enter zum Beenden...")
        sys.exit(1)

    print("  Alles bereit!\n")

    speaker  = Speaker()
    listener = Listener()

    # Automation-Modul mit Speaker verbinden
    automation.set_speak_callback(speaker.say)

    speaker.say(f"Hallo {USERNAME}, Jarvis ist bereit.")

    while True:
        try:
            print("  Lausche auf 'Jarvis'...")
            wake_audio = listener.listen_for_wake_word()
            print("  Wake-Word erkannt!")

            automation.update_activity()

            command = listener.listen_command(wake_audio)
            _process_command(command, speaker, listener)

            # ---- Folgefragen-Fenster ----
            # Nach einer Antwort kurz auf Folgefragen warten (kein Wake-Word noetig)
            followup_count = 0
            while followup_count < 2:   # max 2 Folgefragen hintereinander
                print("  [Folgefrage-Fenster aktiv]")
                follow_up = listener.listen_quick(timeout=4.0)

                if not follow_up:
                    break  # Stille -> zurueck zum Wake-Word-Hoeren

                print(f"  [Folgefrage]: \"{follow_up}\"")

                if _ist_abbruchbefehl(follow_up):
                    speaker.say("Gerne.")
                    break

                if _ist_stoppbefehl(follow_up):
                    break

                # Folgefrage verarbeiten
                _process_command(follow_up, speaker, listener)
                followup_count += 1

        except KeyboardInterrupt:
            print("\n  Jarvis wird beendet.")
            speaker.say("Auf Wiedersehen!")
            break


if __name__ == "__main__":
    main()
