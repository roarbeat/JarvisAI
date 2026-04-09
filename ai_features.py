"""
Erweiterte KI-Funktionen fuer Jarvis.
Screenshot-Analyse, Clipboard-Vorlesen, Dokument-Zusammenfassung,
Konversationsgedaechtnis (JSON).
"""
import os
import json
import base64
import time
import datetime

import ollama

from config import OLLAMA_MODEL, MEMORY_FILE, USERNAME


# ============================================================
#  SCREENSHOT ANALYSIEREN
# ============================================================

def _take_screenshot(path: str) -> bool:
    """Screenshot aufnehmen – versucht mehrere Methoden."""
    # Methode 1: pyautogui
    try:
        import pyautogui
        pyautogui.screenshot(path)
        return os.path.exists(path) and os.path.getsize(path) > 1000
    except Exception:
        pass

    # Methode 2: PIL/ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(path)
        return os.path.exists(path) and os.path.getsize(path) > 1000
    except Exception:
        pass

    # Methode 3: PowerShell (Windows Fallback)
    try:
        import subprocess
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "Add-Type -AssemblyName System.Drawing;"
            "$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            "$bmp = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height;"
            "$g = [System.Drawing.Graphics]::FromImage($bmp);"
            "$g.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size);"
            f"$bmp.Save('{path}');"
            "$g.Dispose(); $bmp.Dispose()"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=15
        )
        return os.path.exists(path) and os.path.getsize(path) > 1000
    except Exception:
        pass

    return False


def analyze_screenshot(question="Was siehst du auf meinem Bildschirm?"):
    """Screenshot aufnehmen und mit dem Vision-Modell analysieren."""
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{ts}.png")

    if not _take_screenshot(path):
        return "Screenshot konnte nicht erstellt werden. Bitte pyautogui oder PIL installieren."

    try:
        from PIL import Image
        import io
        img = Image.open(path)
        img = img.resize((1280, 720), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        try:
            r = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{
                    "role": "user",
                    "content": question,
                    "images": [img_b64],
                }],
                options={"num_ctx": 2048, "num_gpu": 99}
            )
            return r["message"]["content"][:600]
        except Exception as e:
            return f"Screenshot auf Desktop gespeichert. Vision-Analyse fehlgeschlagen: {e}"
    except Exception as e:
        return f"Screenshot gespeichert unter {path}, aber Analyse fehlgeschlagen: {e}"


# ============================================================
#  CLIPBOARD VORLESEN
# ============================================================

def read_clipboard():
    """Inhalt der Zwischenablage vorlesen."""
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content or not content.strip():
            return "Die Zwischenablage ist leer."
        text = content.strip()
        if len(text) > 800:
            return f"Zwischenablage (gekuerzt): {text[:800]} ..."
        return f"In der Zwischenablage: {text}"
    except Exception as e:
        return f"Fehler beim Lesen der Zwischenablage: {e}"


def summarize_clipboard():
    """Text aus der Zwischenablage mit KI zusammenfassen."""
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content or len(content.strip()) < 20:
            return "Zwischenablage ist leer oder zu kurz."

        r = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                "role": "user",
                "content": f"Fasse folgenden Text kurz und praegnant auf Deutsch zusammen:\n\n{content[:4000]}"
            }],
            options={"num_ctx": 2048, "num_gpu": 99}
        )
        return r["message"]["content"][:500]
    except Exception as e:
        return f"Fehler beim Zusammenfassen: {e}"


# ============================================================
#  DOKUMENT ZUSAMMENFASSEN
# ============================================================

def summarize_document(file_path):
    """Datei oeffnen und mit KI zusammenfassen."""
    try:
        if not os.path.exists(file_path):
            return f"Datei nicht gefunden: {file_path}"

        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext in (".txt", ".md", ".py", ".js", ".html", ".csv", ".log"):
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                text = f.read()

        elif ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(
                        page.extract_text() or "" for page in pdf.pages[:10]
                    )
            except ImportError:
                try:
                    import PyPDF2
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join(
                            page.extract_text() or "" for page in reader.pages[:10]
                        )
                except Exception as e2:
                    return f"PDF-Lesefehler: {e2} – bitte pdfplumber installieren."

        elif ext in (".docx",):
            try:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return "Fehler: python-docx nicht installiert."

        else:
            os.startfile(file_path)
            return f"Dateiformat '{ext}' wird geoeffnet – Zusammenfassung nur fuer txt/pdf/docx."

        if not text.strip():
            return "Datei ist leer oder konnte nicht gelesen werden."

        # KI-Zusammenfassung
        r = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    f"Fasse folgenden Text (Datei: {os.path.basename(file_path)}) "
                    f"kurz und praegnant auf Deutsch zusammen:\n\n{text[:4000]}"
                )
            }],
            options={"num_ctx": 4096, "num_gpu": 99}
        )
        return r["message"]["content"][:600]
    except Exception as e:
        return f"Fehler beim Zusammenfassen: {e}"


# ============================================================
#  KONVERSATIONSGEDAECHTNIS (JSON)
# ============================================================

def _load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_memory(data):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_preference(key, value):
    """Nutzer-Vorliebe/Einstellung dauerhaft speichern."""
    try:
        mem = _load_memory()
        mem[key.lower()] = {
            "value": value,
            "saved_at": datetime.datetime.now().isoformat()
        }
        _save_memory(mem)
        return f"Gespeichert: '{key}' = '{value}'"
    except Exception as e:
        return f"Speicherfehler: {e}"


def get_preference(key):
    """Gespeicherte Vorliebe abrufen."""
    try:
        mem = _load_memory()
        entry = mem.get(key.lower())
        if entry:
            return f"{key}: {entry['value']}"
        return f"Keine gespeicherte Einstellung fuer '{key}'."
    except Exception as e:
        return f"Lesefehler: {e}"


def list_preferences():
    """Alle gespeicherten Vorlieben auflisten."""
    try:
        mem = _load_memory()
        if not mem:
            return "Keine Einstellungen gespeichert."
        items = [f"{k}: {v['value']}" for k, v in list(mem.items())[:10]]
        return "Gespeicherte Einstellungen: " + " | ".join(items)
    except Exception as e:
        return f"Fehler: {e}"


def delete_preference(key):
    """Gespeicherte Vorliebe loeschen."""
    try:
        mem = _load_memory()
        if key.lower() in mem:
            del mem[key.lower()]
            _save_memory(mem)
            return f"Einstellung '{key}' geloescht."
        return f"Keine Einstellung '{key}' gefunden."
    except Exception as e:
        return f"Fehler: {e}"


def forget_all():
    """Alle gespeicherten Einstellungen loeschen."""
    try:
        _save_memory({})
        return "Alle gespeicherten Einstellungen geloescht."
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================
#  MEHRSPRACHIGER MODUS
# ============================================================

_language = {"current": "de"}


def switch_language(lang):
    """Sprache umschalten (de / en)."""
    lang = lang.lower().strip()
    lang_map = {
        "deutsch": "de", "german": "de", "de": "de",
        "englisch": "en", "english": "en", "en": "en",
    }
    code = lang_map.get(lang, "de")
    _language["current"] = code
    # Persistenz
    save_preference("language", code)
    if code == "en":
        return "Switched to English mode."
    return "Auf Deutsch umgeschaltet."


def get_current_language():
    """Aktuelle Sprache abfragen."""
    lang = _language.get("current", "de")
    return "en" if lang == "en" else "de"
