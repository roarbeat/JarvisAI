"""
Browser- und App-Steuerung fuer Jarvis.
Enthaelt: Brave-Integration, APP_MAP, open_in_brave, open_app
"""
import os
import re
import subprocess
import webbrowser

# ============================================================
#  BRAVE-BROWSER ERKENNUNG
# ============================================================

BRAVE_PATHS = [
    os.path.join(os.environ.get("PROGRAMFILES", ""),       "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", ""),  "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""),       "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
    # Portable / benutzerdefinierte Installationen
    r"C:\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"D:\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.join(os.environ.get("APPDATA", ""), "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
]
BRAVE_EXE = None
for _p in BRAVE_PATHS:
    if _p and os.path.exists(_p):
        BRAVE_EXE = _p
        break


def open_in_brave(url):
    """Oeffnet URL in Brave oder Standard-Browser (mehrere Fallbacks)."""
    # Brave direkt
    if BRAVE_EXE:
        try:
            subprocess.Popen([BRAVE_EXE, url])
            return
        except Exception:
            pass

    # Windows start-Befehl (oeffnet Standard-Browser)
    try:
        subprocess.Popen(["cmd", "/c", "start", "", url],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception:
        pass

    # Python webbrowser Modul
    try:
        webbrowser.open(url)
        return
    except Exception:
        pass

    # Letzter Fallback: os.startfile
    try:
        os.startfile(url)
    except Exception as e:
        print(f"  [Browser] Oeffnen fehlgeschlagen: {e}")


# ============================================================
#  APP-MAP
# Konventionen:
#   "%VAR%\\pfad.exe"  = Umgebungsvariable expandieren + direkt starten
#   "xxx:"             = URI-Scheme via os.startfile
#   "https://..."      = im Browser oeffnen
#   "name.exe"         = Windows-Systembefehl via os.startfile
# ============================================================

APP_MAP = {
    # Texteditoren
    "notepad": "notepad.exe", "editor": "notepad.exe", "wordpad": "wordpad.exe",
    # Rechner
    "rechner": "calc.exe", "taschenrechner": "calc.exe", "calculator": "calc.exe",
    # Explorer
    "explorer": "explorer.exe", "datei-explorer": "explorer.exe", "dateiexplorer": "explorer.exe",
    # Grafik
    "paint": "mspaint.exe",
    # Terminal
    "terminal": "wt.exe", "windows terminal": "wt.exe", "cmd": "cmd.exe",
    "powershell": "powershell.exe", "eingabeaufforderung": "cmd.exe",
    # Browser
    "brave":        "__brave__",
    "chrome":       "%PROGRAMFILES%\\Google\\Chrome\\Application\\chrome.exe",
    "google chrome":"%PROGRAMFILES%\\Google\\Chrome\\Application\\chrome.exe",
    "firefox":      "%PROGRAMFILES%\\Mozilla Firefox\\firefox.exe",
    "edge":         "%PROGRAMFILES(X86)%\\Microsoft\\Edge\\Application\\msedge.exe",
    "browser":      "__brave__",
    "opera":        "%LOCALAPPDATA%\\Programs\\Opera\\launcher.exe",
    # Musik & Medien
    "spotify":      "spotify.exe",
    "vlc":          "%PROGRAMFILES%\\VideoLAN\\VLC\\vlc.exe",
    "vlc x86":      "%PROGRAMFILES(X86)%\\VideoLAN\\VLC\\vlc.exe",
    "media player": "wmplayer.exe",
    # Office
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe", "onenote": "onenote.exe", "access": "msaccess.exe",
    # Kommunikation
    "teams":    "msteams:",
    "discord":  "%LOCALAPPDATA%\\Discord\\Update.exe",
    "skype":    "skype:",
    "zoom":     "%APPDATA%\\Zoom\\bin\\Zoom.exe",
    "slack":    "%LOCALAPPDATA%\\slack\\slack.exe",
    "whatsapp": "whatsapp:",
    "telegram": "%APPDATA%\\Telegram Desktop\\Telegram.exe",
    # Gaming
    "steam":        "%PROGRAMFILES(X86)%\\Steam\\steam.exe",
    "epic games":   "%PROGRAMFILES(X86)%\\Epic Games\\Launcher\\Portal\\Binaries\\Win64\\EpicGamesLauncher.exe",
    "epic":         "%PROGRAMFILES(X86)%\\Epic Games\\Launcher\\Portal\\Binaries\\Win64\\EpicGamesLauncher.exe",
    # Dev
    "vscode": "code", "vs code": "code", "visual studio code": "code",
    "visual studio": "devenv.exe",
    # System
    "taskmanager": "taskmgr.exe", "task manager": "taskmgr.exe",
    "task-manager": "taskmgr.exe", "taskverwaltung": "taskmgr.exe",
    "einstellungen": "ms-settings:", "settings": "ms-settings:",
    "systemsteuerung": "control.exe", "control panel": "control.exe",
    "geraetemanager": "devmgmt.msc", "dienste": "services.msc",
    "snipping tool": "snippingtool.exe", "snip": "snippingtool.exe",
    # Windows Store-Apps (URI)
    "fotos": "ms-photos:", "kamera": "microsoft.windows.camera:",
    "uhr": "ms-clock:", "alarm": "ms-clock:", "kalender": "outlookcal:",
    "maps": "bingmaps:", "karten": "bingmaps:",
    "store": "ms-windows-store:", "microsoft store": "ms-windows-store:",
    "defender": "windowsdefender:", "sicherheit": "windowsdefender:",
    # Sonstiges
    "7zip":     "%PROGRAMFILES%\\7-Zip\\7zFM.exe",
    "winrar":   "%PROGRAMFILES%\\WinRAR\\WinRAR.exe",
    "obs":      "%PROGRAMFILES%\\obs-studio\\bin\\64bit\\obs64.exe",
    "obs studio": "%PROGRAMFILES%\\obs-studio\\bin\\64bit\\obs64.exe",
    "audacity": "%PROGRAMFILES%\\Audacity\\Audacity.exe",
    "gimp":     "%PROGRAMFILES%\\GIMP 2\\bin\\gimp-2.10.exe",
    "blender":  "%PROGRAMFILES%\\Blender Foundation\\Blender 4.0\\blender.exe",
    "figma":    "%LOCALAPPDATA%\\Figma\\Figma.exe",
    # Web-Apps im Browser
    "netflix":   "https://www.netflix.com",
    "youtube":   "https://www.youtube.com",
    "twitch":    "https://www.twitch.tv",
    "instagram": "https://www.instagram.com",
    "tiktok":    "https://www.tiktok.com",
    "twitter":   "https://x.com",
    "reddit":    "https://www.reddit.com",
    "facebook":  "https://www.facebook.com",
    "linkedin":  "https://www.linkedin.com",
    "chatgpt":   "https://chat.openai.com",
    "claude":    "https://claude.ai",
}


def open_app(name):
    """Oeffnet App mit der passenden Methode je nach Typ."""
    key = name.lower().strip()
    target = APP_MAP.get(key, name)

    try:
        # Sonderfall: Brave Browser
        if target == "__brave__":
            if BRAVE_EXE:
                subprocess.Popen([BRAVE_EXE])
            else:
                subprocess.Popen('start brave', shell=True)
            return f"{name} geoeffnet."

        # URL -> Browser
        if target.startswith("http://") or target.startswith("https://"):
            open_in_brave(target)
            return f"{name} geoeffnet."

        # Pfad mit Umgebungsvariable
        if target.startswith("%"):
            expanded = os.path.expandvars(target)
            if os.path.exists(expanded):
                if "Discord" in expanded and "Update.exe" in expanded:
                    subprocess.Popen([expanded, "--processStart", "Discord.exe"])
                else:
                    subprocess.Popen([expanded])
                return f"{name} geoeffnet."
            # VLC-Fallback auf x86
            if "VideoLAN" in target:
                vlc_x86 = os.path.expandvars("%PROGRAMFILES(X86)%\\VideoLAN\\VLC\\vlc.exe")
                if os.path.exists(vlc_x86):
                    subprocess.Popen([vlc_x86])
                    return f"{name} geoeffnet."
            # Allgemeiner Fallback
            app_name = os.path.basename(expanded)
            subprocess.Popen(f'start "" "{app_name}"', shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"{name} geoeffnet."

        # URI-Scheme
        if target.endswith(":") or (re.match(r'^[a-z][a-z0-9+\-.]*:', target)
                                     and "\\" not in target and "/" not in target):
            os.startfile(target)
            return f"{name} geoeffnet."

        # .msc Konsolen
        if target.endswith(".msc"):
            os.startfile(target)
            return f"{name} geoeffnet."

        # .exe – erst als Systembefehl, dann als Shell-Start
        if target.endswith(".exe"):
            try:
                subprocess.Popen([target],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"{name} geoeffnet."
            except Exception:
                pass
            try:
                subprocess.Popen(f'start "" "{target}"', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"{name} geoeffnet."
            except Exception:
                pass
            try:
                os.startfile(target)
                return f"{name} geoeffnet."
            except Exception as e:
                return f"Konnte {name} nicht oeffnen: {e}"

        # Letzter Ausweg: Shell start
        try:
            subprocess.Popen(["cmd", "/c", "start", "", target],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            subprocess.Popen(f'start "" "{target}"', shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"{name} geoeffnet."

    except Exception as err:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", target],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"{name} geoeffnet."
        except Exception:
            return f"Konnte {name} nicht oeffnen: {err}"
