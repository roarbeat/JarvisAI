"""
PC-Steuerung fuer Jarvis.
Maus, Fenster, Clipboard, Scroll, Multi-Monitor, Taskleisten-Pinning.
"""
import time
import subprocess

import pyautogui
import pyperclip

pyautogui.FAILSAFE = False   # kein sofortiger Abbruch wenn Maus an Ecke


# ============================================================
#  MAUS-STEUERUNG
# ============================================================

def move_mouse(direction=None, x=None, y=None, target=None, steps=150):
    """Maus bewegen – relativ per Richtung oder absolut per Koordinaten."""
    try:
        screen_w, screen_h = pyautogui.size()

        if x is not None and y is not None:
            pyautogui.moveTo(int(x), int(y), duration=0.3)
            return f"Maus zu ({x}, {y}) bewegt."

        if direction:
            moves = {
                "links": (-steps, 0), "left": (-steps, 0),
                "rechts": (steps, 0), "right": (steps, 0),
                "hoch": (0, -steps), "up": (0, -steps), "oben": (0, -steps),
                "runter": (0, steps), "down": (0, steps), "unten": (0, steps),
            }
            dx, dy = moves.get(direction.lower(), (0, 0))
            pyautogui.moveRel(dx, dy, duration=0.2)
            return f"Maus nach {direction} bewegt."

        if target:
            positions = {
                "mitte": (screen_w // 2, screen_h // 2),
                "center": (screen_w // 2, screen_h // 2),
                "oben links": (50, 50),
                "oben rechts": (screen_w - 50, 50),
                "unten links": (50, screen_h - 50),
                "unten rechts": (screen_w - 50, screen_h - 50),
                "taskleiste": (screen_w // 2, screen_h - 20),
            }
            pos = positions.get(target.lower(), (screen_w // 2, screen_h // 2))
            pyautogui.moveTo(*pos, duration=0.3)
            return f"Maus zu '{target}' bewegt."

        return "Keine Zielposition angegeben."
    except Exception as e:
        return f"Fehler beim Maus-Bewegen: {e}"


def click_mouse(button="left", double=False, x=None, y=None):
    """Maus klicken – links, rechts oder doppelt."""
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(int(x), int(y), duration=0.2)

        if double:
            pyautogui.doubleClick()
            return "Doppelklick ausgefuehrt."

        btn_map = {
            "links": "left", "left": "left",
            "rechts": "right", "right": "right",
            "mitte": "middle", "middle": "middle",
        }
        btn = btn_map.get(str(button).lower(), "left")
        pyautogui.click(button=btn)
        return f"{button.capitalize()}-Klick ausgefuehrt."
    except Exception as e:
        return f"Fehler beim Klicken: {e}"


# ============================================================
#  FENSTER-VERWALTUNG
# ============================================================

def manage_window(action, app_name=None):
    """Fenster verwalten: minimieren, maximieren, schliessen, wechseln, andocken."""
    try:
        action = action.lower()

        # App-Wechsel via Alt+Tab
        if action in ("switch", "alt_tab"):
            pyautogui.hotkey("alt", "tab")
            return "Zu naechster App gewechselt."

        if action in ("minimize_all", "desktop"):
            pyautogui.hotkey("win", "d")
            return "Alle Fenster minimiert / Desktop angezeigt."

        if action == "task_view":
            pyautogui.hotkey("win", "tab")
            return "Aufgabenansicht geoeffnet."

        # Aktives Fenster ueber pygetwindow steuern
        try:
            import pygetwindow as gw
            wins = gw.getAllWindows()

            if app_name:
                targets = [w for w in wins if app_name.lower() in w.title.lower()]
                win = targets[0] if targets else gw.getActiveWindow()
            else:
                win = gw.getActiveWindow()

            if not win:
                return "Kein aktives Fenster gefunden."

            if action == "minimize":
                win.minimize()
                return "Fenster minimiert."
            elif action == "maximize":
                win.maximize()
                return "Fenster maximiert."
            elif action == "restore":
                win.restore()
                return "Fenster wiederhergestellt."
            elif action == "close":
                win.close()
                return "Fenster geschlossen."
            elif action in ("snap_left", "andocken_links"):
                pyautogui.hotkey("win", "left")
                return "Fenster links angedockt."
            elif action in ("snap_right", "andocken_rechts"):
                pyautogui.hotkey("win", "right")
                return "Fenster rechts angedockt."
            elif action == "snap_top":
                pyautogui.hotkey("win", "up")
                return "Fenster maximiert / oben angedockt."

        except ImportError:
            # Fallback ohne pygetwindow
            hotkey_map = {
                "minimize": ("win", "down"),
                "maximize": ("win", "up"),
                "close":    ("alt", "F4"),
                "snap_left":  ("win", "left"),
                "snap_right": ("win", "right"),
            }
            keys = hotkey_map.get(action)
            if keys:
                pyautogui.hotkey(*keys)
                return f"Fenster-Aktion '{action}' ausgefuehrt."

        return f"Unbekannte Fenster-Aktion: {action}"
    except Exception as e:
        return f"Fehler bei Fensterverwaltung: {e}"


# ============================================================
#  CLIPBOARD
# ============================================================

def clipboard_action(action, text=None):
    """Zwischenablage steuern: setzen, einfuegen, auslesen."""
    try:
        if action == "set":
            if text:
                pyperclip.copy(str(text))
                return f"Text in Zwischenablage: '{str(text)[:60]}'"
            return "Kein Text angegeben."

        elif action == "paste":
            pyautogui.hotkey("ctrl", "v")
            return "Zwischenablage eingefuegt."

        elif action == "get":
            content = pyperclip.paste()
            return content[:500] if content else "Zwischenablage ist leer."

        elif action in ("type_paste", "diktieren"):
            if text:
                pyperclip.copy(str(text))
                time.sleep(0.15)
                pyautogui.hotkey("ctrl", "v")
                return "Text diktiert und eingefuegt."
            return "Kein Text angegeben."

        elif action == "copy_selection":
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.1)
            content = pyperclip.paste()
            return f"Kopiert: '{content[:100]}'"

        return "Unbekannte Clipboard-Aktion."
    except Exception as e:
        return f"Fehler bei Clipboard: {e}"


# ============================================================
#  SCROLLING
# ============================================================

def scroll_page(direction, amount=5):
    """Seite scrollen – hoch, runter, links, rechts."""
    try:
        direction = direction.lower()
        if direction in ("runter", "down", "unten"):
            pyautogui.scroll(-amount)
            return "Nach unten gescrollt."
        elif direction in ("hoch", "up", "oben"):
            pyautogui.scroll(amount)
            return "Nach oben gescrollt."
        elif direction in ("links", "left"):
            pyautogui.hscroll(-amount)
            return "Nach links gescrollt."
        elif direction in ("rechts", "right"):
            pyautogui.hscroll(amount)
            return "Nach rechts gescrollt."
        elif direction in ("anfang", "top", "seitenanfang"):
            pyautogui.hotkey("ctrl", "Home")
            return "Zum Seitenanfang gescrollt."
        elif direction in ("ende", "end", "seitenende"):
            pyautogui.hotkey("ctrl", "End")
            return "Zum Seitenende gescrollt."
        return f"Unbekannte Scroll-Richtung: {direction}"
    except Exception as e:
        return f"Fehler beim Scrollen: {e}"


# ============================================================
#  MULTI-MONITOR
# ============================================================

def move_window_to_monitor(direction="right"):
    """Aktives Fenster auf anderen Monitor verschieben (Win+Shift+Pfeil)."""
    try:
        direction = direction.lower()
        if direction in ("rechts", "right", "2", "naechster"):
            pyautogui.hotkey("win", "shift", "right")
            return "Fenster auf naechsten Monitor verschoben."
        else:
            pyautogui.hotkey("win", "shift", "left")
            return "Fenster auf vorherigen Monitor verschoben."
    except Exception as e:
        return f"Fehler beim Monitor-Wechsel: {e}"


# ============================================================
#  TASKLEISTEN-PINNING
# ============================================================

def taskbar_pin(app_name, pin=True):
    """App in der Taskleiste anpinnen oder loesen (ueber Shell.Application)."""
    try:
        verb = "Pin to taskbar" if pin else "Unpin from taskbar"
        script = f"""
$sh = New-Object -ComObject Shell.Application
$found = $false
foreach ($folder in @($sh.Namespace(0x02), $sh.Namespace(0x26), $sh.Namespace(0x25))) {{
    if (-not $folder) {{ continue }}
    foreach ($item in $folder.Items()) {{
        if ($item.Name -like '*{app_name}*') {{
            $verb_obj = $item.Verbs() | Where-Object {{ $_.Name -eq '{verb}' }}
            if ($verb_obj) {{ $verb_obj.DoIt(); $found = $true; break }}
        }}
    }}
    if ($found) {{ break }}
}}
if ($found) {{ Write-Output 'OK' }} else {{ Write-Output 'NotFound' }}
"""
        r = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True, text=True, timeout=15
        )
        if "OK" in r.stdout:
            return f"'{app_name}' {'angepinnt' if pin else 'geloest'}."
        return f"App '{app_name}' in Taskleiste nicht gefunden oder Aktion nicht verfuegbar."
    except Exception as e:
        return f"Fehler beim Taskbar-Pinning: {e}"
