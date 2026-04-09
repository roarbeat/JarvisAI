"""
Aktions-Dispatcher fuer Jarvis.
Alle neuen Module werden lazy importiert – ein fehlgeschlagener Import
bricht NICHT das gesamte System, sondern gibt eine verstaendliche Fehlermeldung.
"""
import os
import subprocess
import time

from browser    import open_in_brave, open_app
from weather    import get_weather
from smart_home import control_smart_home


# ============================================================
#  LAZY-IMPORT-HELFER
#  Laed ein Modul einmalig und gibt None zurueck wenn es fehlt.
# ============================================================

_mod_cache = {}

def _load(module_name):
    if module_name in _mod_cache:
        return _mod_cache[module_name]
    try:
        import importlib
        mod = importlib.import_module(module_name)
        _mod_cache[module_name] = mod
        return mod
    except Exception as e:
        print(f"  [Warnung] Modul '{module_name}' nicht geladen: {e}")
        _mod_cache[module_name] = None
        return None


def web_search(query):
    import urllib.parse
    url = "https://search.brave.com/search?q=" + urllib.parse.quote(query)
    open_in_brave(url)
    return f"Suche nach '{query}' geoeffnet."


# Aliase fuer haeufige Modell-Halluzinationen
_ACTION_ALIASES = {
    "control_device":    "control_home",
    "smart_home":        "control_home",
    "toggle_device":     "control_home",
    "set_device":        "control_home",
    "home_control":      "control_home",
    "light":             "control_home",
    "light_control":     "control_home",
    "open_browser":      "open_app",
    "launch_app":        "open_app",
    "start_app":         "open_app",
    "play_spotify":      "spotify",
    "play_music":        "spotify",
    "search_web":        "web_search",
    "google":            "web_search",
    "timer":             "set_timer",
    "alarm":             "set_alarm",
    "reminder":          "remind_me",
    "weather":           "get_weather",
    "wetter":            "get_weather",
    "note":              "save_note",
    "calc":              "calculate",
    "rechne":            "calculate",
    "wiki":              "wikipedia",
    "open_url":          "open_website",
    "navigate":          "open_website",
    "volume":            "set_volume",
    "brightness":        "set_brightness",
    "mute":              "volume_mute",
    "pause":             "media_key",
    "play":              "media_key",
    "next_track":        "media_key",
    "prev_track":        "media_key",
}


def execute_action(action_data):
    """Fuehrt eine Aktion aus. Jeder Block faengt Fehler einzeln ab."""
    a = action_data.get("action", "none")
    # Alias-Mapping: haeufige Modell-Halluzinationen korrigieren
    a = _ACTION_ALIASES.get(a, a)
    action_data["action"] = a

    try:

        # ============================================================
        #  APPS & WEB
        # ============================================================
        if a == "open_app":
            # Modell nutzt manchmal "app" statt "app_name"
            app = action_data.get("app_name") or action_data.get("app") or action_data.get("name", "")
            return open_app(app)

        elif a == "close_app":
            import psutil
            name, ok = (action_data.get("app_name") or action_data.get("app") or action_data.get("name", "")).lower(), False
            for p in psutil.process_iter(["name"]):
                if name in p.info["name"].lower():
                    p.terminate(); ok = True
            return f"{name} geschlossen." if ok else f"{name} laeuft nicht."

        elif a == "get_weather":
            city = action_data.get("city") or action_data.get("location") or action_data.get("ort", "")
            return get_weather(city)

        elif a == "web_search":
            q = action_data.get("query") or action_data.get("search_query") or action_data.get("q", "")
            return web_search(q)

        elif a == "open_website":
            url = action_data.get("url", "").strip()
            if not url: return "Keine URL angegeben."
            if not url.startswith("http"): url = "https://" + url
            open_in_brave(url)
            return "Website geoeffnet."

        elif a == "search_files":
            q = action_data.get("query", "")
            path = action_data.get("path", os.path.expanduser("~"))
            found = []
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ["AppData","node_modules","__pycache__",".git"]]
                for f in files:
                    if q.lower() in f.lower(): found.append(f)
                    if len(found) >= 5: break
                if len(found) >= 5: break
            return (", ".join(found[:5]) + " gefunden.") if found else "Nichts gefunden."

        elif a == "open_file":
            p = action_data.get("file_path", "")
            if os.path.exists(p): os.startfile(p); return "Geoeffnet."
            return "Datei nicht gefunden."

        # ============================================================
        #  LAUTSTAERKE (System)
        # ============================================================
        elif a in ("set_volume", "volume_up", "volume_down", "volume_mute"):
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                d = AudioUtilities.GetSpeakers()
                v = cast(d.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
                if a == "set_volume":
                    lv = int(action_data.get("level", 50))
                    v.SetMasterVolumeLevelScalar(max(0,min(100,lv))/100.0, None)
                    return f"Lautstaerke auf {lv}%."
                elif a == "volume_up":
                    nv = min(1.0, v.GetMasterVolumeLevelScalar() + 0.1)
                    v.SetMasterVolumeLevelScalar(nv, None); return f"Lautstaerke {int(nv*100)}%."
                elif a == "volume_down":
                    nv = max(0.0, v.GetMasterVolumeLevelScalar() - 0.1)
                    v.SetMasterVolumeLevelScalar(nv, None); return f"Lautstaerke {int(nv*100)}%."
                elif a == "volume_mute":
                    muted = v.GetMute(); v.SetMute(not muted, None)
                    return "Ton aus." if not muted else "Ton wieder an."
            except Exception as e:
                return f"Lautstaerke-Fehler: {e}"

        elif a == "set_app_volume":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.set_app_volume(action_data.get("app_name",""), action_data.get("level",50))

        elif a == "set_voice_volume":
            try:
                from tts import set_voice_volume
                lv = action_data.get("level", 1.0)
                lv = float(lv)
                # Werte > 2 werden als Prozent (0-100) interpretiert
                if lv > 2:
                    lv = lv / 100.0
                return set_voice_volume(lv)
            except Exception as e:
                return f"Fehler: {e}"

        # ============================================================
        #  HELLIGKEIT & EINSTELLUNGEN
        # ============================================================
        elif a == "set_brightness":
            try:
                import screen_brightness_control as sbc
                sbc.set_brightness(max(0, min(100, int(action_data.get("level", 50)))))
                return "Helligkeit gesetzt."
            except Exception:
                lv = max(0, min(100, int(action_data.get("level", 50))))
                os.system(f'powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{lv})"')
                return f"Helligkeit auf {lv}%."

        elif a == "open_settings":
            page = action_data.get("page", "").lower().strip()
            pages = {
                "ton":"ms-settings:sound","sound":"ms-settings:sound","audio":"ms-settings:sound",
                "lautstaerke":"ms-settings:sound","display":"ms-settings:display",
                "anzeige":"ms-settings:display","bildschirm":"ms-settings:display",
                "helligkeit":"ms-settings:display","wlan":"ms-settings:network-wifi",
                "wifi":"ms-settings:network-wifi","netzwerk":"ms-settings:network-status",
                "bluetooth":"ms-settings:bluetooth","apps":"ms-settings:appsfeatures",
                "benachrichtigungen":"ms-settings:notifications",
                "akku":"ms-settings:batterysaver","batterie":"ms-settings:batterysaver",
                "datenschutz":"ms-settings:privacy","personalisierung":"ms-settings:personalization",
                "hintergrund":"ms-settings:personalization-background","farben":"ms-settings:colors",
                "nachtmodus":"ms-settings:nightlight","nachtlicht":"ms-settings:nightlight",
                "speicher":"ms-settings:storagesense","update":"ms-settings:windowsupdate",
                "zeit":"ms-settings:dateandtime","sprache":"ms-settings:speech",
                "tastatur":"ms-settings:typing","maus":"ms-settings:mousetouchpad",
                "drucker":"ms-settings:printers","energie":"ms-settings:powersleep","info":"ms-settings:about",
            }
            os.startfile(pages.get(page, "ms-settings:"))
            return "Einstellungen geoeffnet."

        elif a == "night_light":
            os.startfile("ms-settings:nightlight"); return "Nachtlicht geoeffnet."

        elif a == "bluetooth_toggle":
            os.startfile("ms-settings:bluetooth"); return "Bluetooth-Einstellungen geoeffnet."

        elif a == "wifi_toggle":
            s = action_data.get("state","on")
            os.system(f'netsh interface set interface "Wi-Fi" {"disable" if s=="off" else "enable"}')
            return f"WLAN {'aus' if s=='off' else 'ein'}."

        # ============================================================
        #  SYSTEM
        # ============================================================
        elif a == "shutdown":   os.system("shutdown /s /t 10"); return "Faehrt in 10s herunter."
        elif a == "restart":    os.system("shutdown /r /t 10"); return "Neustart in 10s."
        elif a == "abort_shutdown": os.system("shutdown /a"); return "Abgebrochen."
        elif a == "sleep":      os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return "Ruhezustand."
        elif a == "lock":       os.system("rundll32.exe user32.dll,LockWorkStation"); return "Gesperrt."

        elif a == "screenshot":
            try:
                p = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{int(time.time())}.png")
                ok = False
                # Methode 1: pyautogui
                try:
                    import pyautogui
                    pyautogui.screenshot(p)
                    ok = os.path.exists(p) and os.path.getsize(p) > 1000
                except Exception:
                    pass
                # Methode 2: PIL ImageGrab
                if not ok:
                    try:
                        from PIL import ImageGrab
                        ImageGrab.grab().save(p)
                        ok = os.path.exists(p) and os.path.getsize(p) > 1000
                    except Exception:
                        pass
                # Methode 3: PowerShell
                if not ok:
                    ps = (
                        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
                        "$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                        "$b=New-Object System.Drawing.Bitmap $s.Width,$s.Height;"
                        "$g=[System.Drawing.Graphics]::FromImage($b);"
                        "$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size);"
                        f"$b.Save('{p}');"
                        "$g.Dispose();$b.Dispose()"
                    )
                    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                   capture_output=True, timeout=15)
                    ok = os.path.exists(p) and os.path.getsize(p) > 1000
                if ok:
                    return f"Screenshot gespeichert: {p}"
                return "Screenshot fehlgeschlagen. Bitte pyautogui installieren."
            except Exception as e:
                return f"Screenshot-Fehler: {e}"

        elif a == "type_text":
            try:
                import pyautogui
                pyautogui.write(action_data.get("text",""), interval=0.02)
                return "Text eingegeben."
            except Exception as e:
                return f"Fehler: {e}"

        elif a == "run_command":
            o = subprocess.run(action_data.get("command",""), shell=True, capture_output=True, text=True, timeout=10)
            return o.stdout[:200] or "Ausgefuehrt."

        elif a == "control_home":
            # Modell nutzt manchmal "entity", "name", "device_name" statt "device"
            device = (action_data.get("device")
                      or action_data.get("entity")
                      or action_data.get("name")
                      or action_data.get("device_name", ""))
            state = action_data.get("state", "on")
            # "aus"/"an" normalisieren
            if state in ("aus", "off", "false", "0"):
                state = "off"
            else:
                state = "on"
            return control_smart_home(device, state)

        # ============================================================
        #  PC-STEUERUNG
        # ============================================================
        elif a == "move_mouse":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar (pyautogui installieren)."
            return m.move_mouse(
                direction=action_data.get("direction"),
                x=action_data.get("x"), y=action_data.get("y"),
                target=action_data.get("target"),
                steps=int(action_data.get("steps", 150))
            )

        elif a == "click_mouse":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.click_mouse(
                button=action_data.get("button","left"),
                double=action_data.get("double", False),
                x=action_data.get("x"), y=action_data.get("y")
            )

        elif a == "manage_window":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.manage_window(
                action=action_data.get("window_action","minimize"),
                app_name=action_data.get("app_name")
            )

        elif a == "clipboard":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.clipboard_action(
                action=action_data.get("clipboard_action","get"),
                text=action_data.get("text")
            )

        elif a == "scroll":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.scroll_page(
                direction=action_data.get("direction","down"),
                amount=int(action_data.get("amount", 5))
            )

        elif a == "move_to_monitor":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.move_window_to_monitor(direction=action_data.get("direction","right"))

        elif a == "taskbar_pin":
            m = _load("pc_control")
            if not m: return "pc_control nicht verfuegbar."
            return m.taskbar_pin(
                app_name=action_data.get("app_name",""),
                pin=action_data.get("pin", True)
            )

        # ============================================================
        #  MEDIEN
        # ============================================================
        elif a == "spotify":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.spotify_control(
                action=action_data.get("spotify_action","play"),
                query=action_data.get("query"),
                playlist=action_data.get("playlist")
            )

        elif a == "youtube":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.youtube_action(
                action=action_data.get("youtube_action","search"),
                query=action_data.get("query")
            )

        elif a == "mute_call":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.mute_call(app=action_data.get("app","auto"))

        elif a == "camera_toggle":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.camera_toggle()

        elif a == "media_key":
            m = _load("media")
            if not m: return "media.py nicht geladen."
            return m.media_key(action_data.get("key","playpause"))

        # ============================================================
        #  AUTOMATISIERUNGEN
        # ============================================================
        elif a == "set_timer":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.set_timer(
                seconds=action_data.get("seconds"),
                minutes=action_data.get("minutes"),
                hours=action_data.get("hours"),
                label=action_data.get("label","Timer")
            )

        elif a == "set_alarm":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.set_alarm(
                hour=action_data.get("hour",7),
                minute=action_data.get("minute",0),
                label=action_data.get("label","Wecker")
            )

        elif a == "remind_me":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.remind_me(
                text=action_data.get("text","Erinnerung"),
                minutes=action_data.get("minutes",0),
                seconds=action_data.get("seconds",0),
                hours=action_data.get("hours",0)
            )

        elif a == "morning_routine":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.morning_routine()

        elif a == "night_mode":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.night_mode(enable=action_data.get("enable",True))

        elif a == "auto_lock":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.set_auto_lock(
                enable=action_data.get("enable",True),
                minutes=action_data.get("minutes",10)
            )

        elif a == "define_command":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.define_custom_command(
                name=action_data.get("name",""),
                actions_list=action_data.get("actions",[])
            )

        elif a == "run_command_custom":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.run_custom_command(action_data.get("name",""))

        elif a == "list_timers":
            m = _load("automation")
            if not m: return "automation.py nicht geladen."
            return m.list_timers()

        # ============================================================
        #  PRODUKTIVITAET
        # ============================================================
        elif a == "calculate":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.calculate(action_data.get("expression",""))

        elif a == "convert_currency":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.convert_currency(
                amount=action_data.get("amount",1),
                from_currency=action_data.get("from","EUR"),
                to_currency=action_data.get("to","USD")
            )

        elif a == "convert_unit":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.convert_unit(
                amount=action_data.get("amount",1),
                from_unit=action_data.get("from","km"),
                to_unit=action_data.get("to","m")
            )

        elif a == "wikipedia":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.wikipedia_search(
                query=action_data.get("query",""),
                lang=action_data.get("lang","de")
            )

        elif a == "save_note":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.save_note(
                text=action_data.get("text",""),
                filename=action_data.get("filename")
            )

        elif a == "read_note":
            m = _load("productivity"); return m.read_last_note() if m else "productivity.py nicht geladen."

        elif a == "list_notes":
            m = _load("productivity"); return m.list_notes() if m else "productivity.py nicht geladen."

        elif a == "read_emails":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.read_emails(
                max_count=int(action_data.get("count",5)),
                only_unread=action_data.get("only_unread",True)
            )

        elif a == "read_calendar":
            m = _load("productivity")
            if not m: return "productivity.py nicht geladen."
            return m.get_calendar_events(max_results=int(action_data.get("count",5)))

        # ============================================================
        #  SYSTEM-MONITORING
        # ============================================================
        elif a == "system_stats":
            m = _load("system_monitor")
            if not m: return "system_monitor.py nicht geladen."
            return m.get_system_stats(detail=action_data.get("detail","all"))

        elif a == "disk_space":
            m = _load("system_monitor")
            if not m: return "system_monitor.py nicht geladen."
            return m.get_disk_space(drive=action_data.get("drive"))

        elif a == "list_processes":
            m = _load("system_monitor")
            if not m: return "system_monitor.py nicht geladen."
            return m.list_processes(
                top=int(action_data.get("count",10)),
                sort_by=action_data.get("sort_by","cpu")
            )

        elif a == "kill_process":
            m = _load("system_monitor")
            if not m: return "system_monitor.py nicht geladen."
            return m.kill_process(action_data.get("name_or_pid",""))

        elif a == "network_speed":
            m = _load("system_monitor"); return m.get_network_speed() if m else "system_monitor nicht geladen."

        elif a == "network_info":
            m = _load("system_monitor"); return m.get_network_info() if m else "system_monitor nicht geladen."

        elif a == "ping":
            m = _load("system_monitor")
            if not m: return "system_monitor nicht geladen."
            return m.ping(host=action_data.get("host","8.8.8.8"))

        elif a == "windows_update":
            m = _load("system_monitor"); return m.check_windows_updates() if m else "system_monitor nicht geladen."

        elif a == "system_summary":
            m = _load("system_monitor"); return m.system_summary() if m else "system_monitor nicht geladen."

        # ============================================================
        #  KOMMUNIKATION
        # ============================================================
        elif a == "whatsapp_send":
            m = _load("communication")
            if not m: return "communication.py nicht geladen."
            return m.whatsapp_send(
                contact=action_data.get("contact",""),
                message=action_data.get("message","")
            )

        elif a == "send_email":
            m = _load("communication")
            if not m: return "communication.py nicht geladen."
            return m.send_email(
                to_address=action_data.get("to",""),
                subject=action_data.get("subject",""),
                body=action_data.get("body",""),
                cc=action_data.get("cc")
            )

        elif a == "compose_email":
            m = _load("communication")
            if not m: return "communication.py nicht geladen."
            return m.compose_email_browser(
                to_address=action_data.get("to",""),
                subject=action_data.get("subject",""),
                body=action_data.get("body","")
            )

        elif a == "discord_send":
            m = _load("communication")
            if not m: return "communication.py nicht geladen."
            return m.discord_send_webhook(
                message=action_data.get("message",""),
                channel_webhook=action_data.get("webhook")
            )

        elif a == "discord_open":
            m = _load("communication")
            if not m: return "communication.py nicht geladen."
            return m.discord_open_channel(channel_name=action_data.get("channel"))

        # ============================================================
        #  KI-FUNKTIONEN
        # ============================================================
        elif a == "analyze_screenshot":
            m = _load("ai_features")
            if not m: return "ai_features.py nicht geladen."
            return m.analyze_screenshot(
                question=action_data.get("question","Was siehst du auf meinem Bildschirm?")
            )

        elif a == "read_clipboard":
            m = _load("ai_features"); return m.read_clipboard() if m else "ai_features nicht geladen."

        elif a == "summarize_clipboard":
            m = _load("ai_features"); return m.summarize_clipboard() if m else "ai_features nicht geladen."

        elif a == "summarize_document":
            m = _load("ai_features")
            if not m: return "ai_features nicht geladen."
            return m.summarize_document(action_data.get("file_path",""))

        elif a == "save_preference":
            m = _load("ai_features")
            if not m: return "ai_features nicht geladen."
            return m.save_preference(action_data.get("key",""), action_data.get("value",""))

        elif a == "get_preference":
            m = _load("ai_features")
            if not m: return "ai_features nicht geladen."
            return m.get_preference(action_data.get("key",""))

        elif a == "list_preferences":
            m = _load("ai_features"); return m.list_preferences() if m else "ai_features nicht geladen."

        elif a == "switch_language":
            m = _load("ai_features")
            if not m: return "ai_features nicht geladen."
            return m.switch_language(action_data.get("language","de"))

        elif a == "set_wake_sensitivity":
            try:
                import stt as _stt
                level = max(0.1, min(0.95, float(action_data.get("level", 0.25))))
                _stt.VAD_THRESHOLD = level
                return f"Wake-Word-Empfindlichkeit auf {level:.2f} gesetzt."
            except Exception as e:
                return f"Fehler: {e}"

        elif a == "none":
            return ""
        else:
            return f"Unbekannte Aktion: {a}"

    except Exception as e:
        return f"Fehler bei '{a}': {e}"
