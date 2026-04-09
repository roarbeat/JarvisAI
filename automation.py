"""
Smarte Automatisierungen fuer Jarvis.
Timer, Alarm, Tagesroutine, Inaktivitaets-Sperre, Nacht-Modus.
"""
import os
import time
import threading
import datetime
import subprocess

from config import USERNAME

# ============================================================
#  SPRECHER-CALLBACK (wird von jarvis.py gesetzt)
# ============================================================

_speak_callback = None
_active_timers: list = []
_inactivity_thread = None
_inactivity_enabled = False
_last_activity_time = time.time()
_inactivity_minutes = 10


def set_speak_callback(fn):
    """Registriert die Speaker.say-Funktion fuer Timer-Benachrichtigungen."""
    global _speak_callback
    _speak_callback = fn


def _speak(text):
    if _speak_callback:
        _speak_callback(text)
    else:
        print(f"  [Automation] {text}")


def update_activity():
    """Aktualisiert den Inaktivitaets-Zeitstempel (wird aus jarvis.py gerufen)."""
    global _last_activity_time
    _last_activity_time = time.time()


# ============================================================
#  TIMER & ALARM
# ============================================================

def set_timer(seconds=None, minutes=None, hours=None, label="Timer"):
    """Stellt einen Timer, der nach Ablauf spricht."""
    try:
        total_s = 0
        if seconds:
            total_s += int(seconds)
        if minutes:
            total_s += int(minutes) * 60
        if hours:
            total_s += int(hours) * 3600

        if total_s <= 0:
            return "Keine gueltige Zeit angegeben."

        # Lesbare Dauer
        h, rem = divmod(total_s, 3600)
        m, s   = divmod(rem, 60)
        parts  = []
        if h:  parts.append(f"{h} Stunde{'n' if h > 1 else ''}")
        if m:  parts.append(f"{m} Minute{'n' if m > 1 else ''}")
        if s:  parts.append(f"{s} Sekunde{'n' if s > 1 else ''}")
        readable = " und ".join(parts)

        def _fire():
            time.sleep(total_s)
            _speak(f"{label} abgelaufen! {readable} sind um.")

        # Abgelaufene Timer aus der Liste entfernen
        _active_timers[:] = [th for th in _active_timers if th.is_alive()]
        t = threading.Thread(target=_fire, daemon=True, name=f"timer_{label}")
        _active_timers.append(t)
        t.start()
        return f"Timer fuer {readable} gestartet."
    except Exception as e:
        return f"Fehler beim Timer: {e}"


def set_alarm(hour, minute=0, label="Wecker"):
    """Stellt einen Wecker fuer eine bestimmte Uhrzeit."""
    try:
        now = datetime.datetime.now()
        alarm = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if alarm <= now:
            alarm += datetime.timedelta(days=1)

        delta_s = (alarm - now).total_seconds()
        time_str = alarm.strftime("%H:%M")

        def _fire():
            time.sleep(delta_s)
            _speak(f"Guten Morgen, {USERNAME}! Es ist {time_str} Uhr – dein {label} klingelt.")

        _active_timers[:] = [th for th in _active_timers if th.is_alive()]
        t = threading.Thread(target=_fire, daemon=True, name=f"alarm_{time_str}")
        _active_timers.append(t)
        t.start()
        return f"Wecker fuer {time_str} Uhr gestellt."
    except Exception as e:
        return f"Fehler beim Wecker: {e}"


def remind_me(text, minutes=0, seconds=0, hours=0):
    """Erinnerung nach einer bestimmten Zeit."""
    total_s = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    if total_s <= 0:
        total_s = 60  # 1 Minute als Fallback

    def _fire():
        time.sleep(total_s)
        _speak(f"Erinnerung: {text}")

    _active_timers[:] = [th for th in _active_timers if th.is_alive()]
    t = threading.Thread(target=_fire, daemon=True, name="reminder")
    _active_timers.append(t)
    t.start()
    m, s = divmod(total_s, 60)
    h, m = divmod(m, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}min")
    if s: parts.append(f"{s}s")
    return f"Ich erinnere dich in {' '.join(parts)} an: {text}"


def list_timers():
    """Listet aktive Timer auf."""
    alive = [t.name for t in _active_timers if t.is_alive()]
    if not alive:
        return "Keine aktiven Timer."
    return f"Aktive Timer: {', '.join(alive)}"


# ============================================================
#  TAEGLICH-ROUTINE
# ============================================================

def morning_routine(speaker_obj=None):
    """
    Morgenroutine: Begruessung, Wetter, Kalender.
    speaker_obj wird vom Dispatcher uebergeben.
    """
    try:
        from weather import get_weather

        now  = datetime.datetime.now()
        hour = now.hour
        if hour < 12:
            greet = "Guten Morgen"
        elif hour < 18:
            greet = "Guten Tag"
        else:
            greet = "Guten Abend"

        _speak(f"{greet}, {USERNAME}! Es ist {now.strftime('%H:%M')} Uhr.")
        time.sleep(1)

        # Wetter (Standard: Berlin als Fallback-Stadt)
        try:
            weather_info = get_weather("Berlin")
            _speak(weather_info[:200] if weather_info else "Wetter nicht verfuegbar.")
            time.sleep(1)
        except Exception:
            pass

        # Kalender (falls konfiguriert)
        try:
            from productivity import get_calendar_events
            events = get_calendar_events()
            _speak(events)
        except Exception:
            pass

        return "Morgenroutine abgeschlossen."
    except Exception as e:
        return f"Fehler in Routine: {e}"


# ============================================================
#  NACHT-MODUS
# ============================================================

def night_mode(enable=True):
    """Nacht-Modus: Lautstaerke senken, Nachtlicht an, DND-Simulation."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        if enable:
            # Lautstaerke auf 20%
            d = AudioUtilities.GetSpeakers()
            v = cast(d.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                     POINTER(IAudioEndpointVolume))
            v.SetMasterVolumeLevelScalar(0.2, None)

            # Nachtlicht aktivieren (Windows Registrierung)
            subprocess.run(
                ["powershell", "-Command",
                 "(Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate')"],
                capture_output=True, timeout=5
            )
            os.startfile("ms-settings:nightlight")

            # Benachrichtigungen deaktivieren (Fokus-Modus)
            subprocess.run(
                ["powershell", "-Command",
                 "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' "
                 "-Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 0 -Type DWord"],
                capture_output=True, timeout=5
            )
            return "Nacht-Modus aktiviert: Lautstaerke 20%, Nachtlicht und Fokusmodus an."
        else:
            # Lautstaerke auf 60%
            d = AudioUtilities.GetSpeakers()
            v = cast(d.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                     POINTER(IAudioEndpointVolume))
            v.SetMasterVolumeLevelScalar(0.6, None)

            subprocess.run(
                ["powershell", "-Command",
                 "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' "
                 "-Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 1 -Type DWord"],
                capture_output=True, timeout=5
            )
            return "Nacht-Modus deaktiviert: Lautstaerke 60%, Benachrichtigungen wieder an."
    except Exception as e:
        return f"Fehler im Nacht-Modus: {e}"


# ============================================================
#  INAKTIVITAETS-SPERRE
# ============================================================

def _inactivity_watcher():
    """Hintergrund-Thread: sperrt PC nach Inaktivitaet."""
    global _last_activity_time
    while _inactivity_enabled:
        time.sleep(30)
        if not _inactivity_enabled:
            break
        elapsed = time.time() - _last_activity_time
        if elapsed >= _inactivity_minutes * 60:
            _speak("Ich sperre jetzt den Bildschirm wegen Inaktivitaet.")
            time.sleep(2)
            os.system("rundll32.exe user32.dll,LockWorkStation")
            # Danach pausieren damit nicht sofort wieder gesperrt wird
            _last_activity_time = time.time()


def set_auto_lock(enable=True, minutes=10):
    """Automatische Inaktivitaets-Sperre aktivieren oder deaktivieren."""
    global _inactivity_enabled, _inactivity_minutes, _inactivity_thread
    _inactivity_minutes = int(minutes)

    if enable:
        if _inactivity_enabled:
            return f"Auto-Lock laeuft bereits (alle {_inactivity_minutes} Minuten)."
        _inactivity_enabled = True
        _inactivity_thread  = threading.Thread(
            target=_inactivity_watcher, daemon=True, name="auto_lock"
        )
        _inactivity_thread.start()
        return f"Auto-Lock aktiviert: Sperre nach {minutes} Minuten Inaktivitaet."
    else:
        _inactivity_enabled = False
        return "Auto-Lock deaktiviert."


# ============================================================
#  EIGENE BEFEHLE (Custom Commands)
# ============================================================

_custom_commands: dict = {}
_CUSTOM_COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "custom_commands.json")


def _load_custom_commands():
    global _custom_commands
    if os.path.exists(_CUSTOM_COMMANDS_FILE):
        import json
        with open(_CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as f:
            _custom_commands = json.load(f)


def _save_custom_commands():
    import json
    with open(_CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(_custom_commands, f, ensure_ascii=False, indent=2)


def define_custom_command(name, actions_list):
    """
    Eigenen Befehl definieren.
    actions_list = Liste von action-Dicts, die hintereinander ausgefuehrt werden.
    """
    _load_custom_commands()
    _custom_commands[name.lower()] = actions_list
    _save_custom_commands()
    return f"Befehl '{name}' mit {len(actions_list)} Aktionen gespeichert."


def run_custom_command(name):
    """Gespeicherten eigenen Befehl ausfuehren."""
    _load_custom_commands()
    key = name.lower()
    if key not in _custom_commands:
        return f"Kein eigener Befehl '{name}' gefunden."

    from actions import execute_action
    results = []
    for act in _custom_commands[key]:
        result = execute_action(act)
        results.append(result)
        time.sleep(0.3)
    return f"Befehl '{name}' ausgefuehrt: {'; '.join(str(r) for r in results[:3])}"


def list_custom_commands():
    """Alle gespeicherten eigenen Befehle auflisten."""
    _load_custom_commands()
    if not _custom_commands:
        return "Keine eigenen Befehle gespeichert."
    names = ", ".join(_custom_commands.keys())
    return f"Eigene Befehle: {names}"


# Beim Import laden
_load_custom_commands()
