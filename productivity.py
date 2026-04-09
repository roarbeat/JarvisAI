"""
Informationen & Produktivitaet fuer Jarvis.
Kalender, E-Mail vorlesen, Notizen, Rechner, Waehrung, Einheiten, Wikipedia.
"""
import os
import re
import math
import datetime
import imaplib
import email
import email.header
import json
import requests

from config import (
    EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_IMAP_SERVER,
    NOTES_DIR, GOOGLE_CALENDAR_CREDENTIALS,
)


# ============================================================
#  RECHNER (Sprach-Ausdruecke)
# ============================================================

def calculate(expression):
    """Berechnet einen mathematischen Ausdruck (sicher via ast.literal_eval-Ersatz)."""
    try:
        # Deutschen Stil normalisieren
        expr = expression.lower()
        expr = expr.replace(",", ".")
        expr = expr.replace("mal", "*").replace("durch", "/")
        expr = expr.replace("plus", "+").replace("minus", "-")
        expr = expr.replace("hoch", "**").replace("^", "**")
        # "wurzel von 16" oder "wurzel 16"  ->  math.sqrt(16)
        expr = re.sub(r"wurzel\s+(?:von\s+)?([\d.]+)", r"math.sqrt(\1)", expr)
        expr = expr.replace("wurzel", "math.sqrt")   # Fallback: wurzel(N)
        expr = expr.replace("pi", str(math.pi))
        expr = expr.replace("prozent", "/100")
        # Kleinbuchstaben und '_' erlauben damit math.sqrt, math.pi etc. erhalten bleiben
        expr = re.sub(r"[^0-9a-z_.+\-*/().,%\s]", "", expr)
        expr = expr.strip()
        if not expr:
            return "Kein gueltiger Ausdruck."
        result = eval(expr, {"__builtins__": {}, "math": math})  # noqa: S307
        # Lesbar formatieren
        if isinstance(result, float) and result == int(result):
            result = int(result)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Rechenfehler: {e}"


# ============================================================
#  WAEHRUNGSUMRECHNUNG
# ============================================================

def convert_currency(amount, from_currency, to_currency):
    """Waehrungsumrechnung via Open Exchange Rates (keine API-Key noetig)."""
    try:
        from_c = from_currency.upper()
        to_c   = to_currency.upper()
        amount = float(str(amount).replace(",", "."))

        # ECB Free API (EUR als Basis)
        url = "https://api.frankfurter.app/latest"
        r = requests.get(url, params={"from": from_c, "to": to_c}, timeout=5)
        r.raise_for_status()
        data = r.json()
        rate   = data["rates"][to_c]
        result = amount * rate
        return f"{amount} {from_c} = {result:.2f} {to_c} (Kurs: {rate:.4f})"
    except Exception as e:
        return f"Waehrungsfehler: {e}"


# ============================================================
#  EINHEITENUMRECHNUNG
# ============================================================

_UNIT_MAP = {
    # Laenge
    "km": ("meter", 1000), "m": ("meter", 1), "cm": ("meter", 0.01),
    "mm": ("meter", 0.001), "mile": ("meter", 1609.34), "meile": ("meter", 1609.34),
    "foot": ("meter", 0.3048), "fuss": ("meter", 0.3048), "inch": ("meter", 0.0254), "zoll": ("meter", 0.0254),
    "yard": ("meter", 0.9144),
    # Gewicht
    "kg": ("gramm", 1000), "g": ("gramm", 1), "mg": ("gramm", 0.001),
    "tonne": ("gramm", 1_000_000), "pfund": ("gramm", 453.592), "pound": ("gramm", 453.592),
    "lb": ("gramm", 453.592), "unze": ("gramm", 28.3495), "oz": ("gramm", 28.3495),
    # Temperatur (gesondert)
    # Volumen
    "liter": ("ml", 1000), "l": ("ml", 1000), "ml": ("ml", 1),
    "gallone": ("ml", 3785.41), "gallon": ("ml", 3785.41),
    "cup": ("ml", 236.588), "tasse": ("ml", 250),
    # Geschwindigkeit
    "kmh": ("ms", 1 / 3.6), "km/h": ("ms", 1 / 3.6),
    "mph": ("ms", 0.44704), "ms": ("ms", 1), "m/s": ("ms", 1),
    # Datenmenge
    "byte": ("byte", 1), "kb": ("byte", 1024), "mb": ("byte", 1024**2),
    "gb": ("byte", 1024**3), "tb": ("byte", 1024**4),
}


def convert_unit(amount, from_unit, to_unit):
    """Einheitenumrechnung."""
    try:
        val    = float(str(amount).replace(",", "."))
        from_u = from_unit.lower().strip()
        to_u   = to_unit.lower().strip()

        # Temperatur-Sonderfall
        if from_u in ("grad", "celsius", "c") and to_u in ("fahrenheit", "f"):
            result = val * 9 / 5 + 32
            return f"{val}°C = {result:.2f}°F"
        if from_u in ("fahrenheit", "f") and to_u in ("celsius", "c", "grad"):
            result = (val - 32) * 5 / 9
            return f"{val}°F = {result:.2f}°C"
        if from_u in ("kelvin", "k") and to_u in ("celsius", "c"):
            result = val - 273.15
            return f"{val}K = {result:.2f}°C"
        if from_u in ("celsius", "c") and to_u in ("kelvin", "k"):
            result = val + 273.15
            return f"{val}°C = {result:.2f}K"

        if from_u not in _UNIT_MAP or to_u not in _UNIT_MAP:
            return f"Einheit '{from_u}' oder '{to_u}' nicht bekannt."

        base_from, fac_from = _UNIT_MAP[from_u]
        base_to,   fac_to   = _UNIT_MAP[to_u]

        if base_from != base_to:
            return f"'{from_u}' und '{to_u}' sind nicht umrechenbar (unterschiedliche Groessen)."

        in_base = val * fac_from
        result  = in_base / fac_to
        return f"{val} {from_unit} = {result:.4g} {to_unit}"
    except Exception as e:
        return f"Umrechnungsfehler: {e}"


# ============================================================
#  WIKIPEDIA
# ============================================================

def wikipedia_search(query, lang="de"):
    """Wikipedia-Schnellabfrage."""
    try:
        import wikipedia as wp
        wp.set_lang(lang)
        try:
            summary = wp.summary(query, sentences=3, auto_suggest=True)
            return summary[:500]
        except wp.exceptions.DisambiguationError as e:
            # Ersten Vorschlag nehmen
            summary = wp.summary(e.options[0], sentences=3)
            return summary[:500]
        except wp.exceptions.PageError:
            return f"Kein Wikipedia-Artikel zu '{query}' gefunden."
    except ImportError:
        # Fallback: Wikipedia API direkt
        try:
            url = f"https://de.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json().get("extract", "Kein Inhalt.")[:500]
            return f"Wikipedia-Seite nicht gefunden."
        except Exception as e2:
            return f"Wikipedia-Fehler: {e2}"
    except Exception as e:
        return f"Wikipedia-Fehler: {e}"


# ============================================================
#  NOTIZEN
# ============================================================

def save_note(text, filename=None):
    """Notiz als .txt Datei speichern."""
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        if not filename:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"notiz_{ts}.txt"
        elif not filename.endswith(".txt"):
            filename += ".txt"

        path = os.path.join(NOTES_DIR, filename)
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"[{timestamp}]\n{text}\n")
        return f"Notiz gespeichert: {path}"
    except Exception as e:
        return f"Fehler beim Speichern: {e}"


def list_notes():
    """Alle Notizen auflisten."""
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".txt")]
        if not files:
            return "Keine Notizen vorhanden."
        files.sort(reverse=True)
        return f"{len(files)} Notiz(en): {', '.join(files[:5])}"
    except Exception as e:
        return f"Fehler: {e}"


def read_last_note():
    """Letzte Notiz vorlesen."""
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        files = sorted(
            [f for f in os.listdir(NOTES_DIR) if f.endswith(".txt")],
            reverse=True
        )
        if not files:
            return "Keine Notizen vorhanden."
        path = os.path.join(NOTES_DIR, files[0])
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return f"Letzte Notiz: {content[:400]}"
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================
#  E-MAIL VORLESEN (IMAP)
# ============================================================

def read_emails(max_count=5, only_unread=True):
    """Ungelesene E-Mails via IMAP vorlesen."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "E-Mail nicht konfiguriert (EMAIL_ADDRESS und EMAIL_PASSWORD in config.py eintragen)."
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        criteria = "UNSEEN" if only_unread else "ALL"
        _, data   = mail.search(None, criteria)
        ids = data[0].split()

        if not ids:
            return "Keine ungelesenen E-Mails."

        recent = ids[-min(max_count, len(ids)):][::-1]
        summaries = []
        for mid in recent:
            _, msg_data = mail.fetch(mid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject_raw = msg.get("Subject", "Kein Betreff")
            subject = email.header.decode_header(subject_raw)[0]
            subject = subject[0].decode(subject[1] or "utf-8") if isinstance(subject[0], bytes) else subject[0]
            sender = msg.get("From", "Unbekannt")
            summaries.append(f"Von {sender[:30]}: {subject[:60]}")

        mail.logout()
        return f"{len(ids)} ungelesene Mail(s). Die letzten: " + " | ".join(summaries)
    except Exception as e:
        return f"E-Mail-Fehler: {e}"


# ============================================================
#  GOOGLE CALENDAR
# ============================================================

def get_calendar_events(max_results=5):
    """Heutige Kalender-Termine aus Google Calendar auslesen."""
    if not GOOGLE_CALENDAR_CREDENTIALS:
        # Fallback: Windows-Kalender oeffnen
        os.startfile("outlookcal:")
        return "Google Calendar nicht konfiguriert – Windows-Kalender geoeffnet."

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds  = None
        token_path = os.path.join(os.path.dirname(__file__), "google_token.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow  = InstalledAppFlow.from_client_secrets_file(GOOGLE_CALENDAR_CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)
        now     = datetime.datetime.utcnow().isoformat() + "Z"
        end     = (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now, timeMax=end,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        if not events:
            return "Heute keine Termine."

        summaries = []
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date", ""))
            if "T" in start:
                t = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                t_local = t.astimezone()
                time_str = t_local.strftime("%H:%M")
            else:
                time_str = "Ganztaegig"
            summaries.append(f"{time_str}: {ev.get('summary', 'Kein Titel')}")

        return "Deine Termine heute: " + ", ".join(summaries)
    except Exception as e:
        return f"Kalender-Fehler: {e}"
