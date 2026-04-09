"""
Kommunikations-Module fuer Jarvis.
WhatsApp Web, E-Mail senden, Discord.
"""
import os
import smtplib
import time
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    EMAIL_ADDRESS, EMAIL_PASSWORD,
    EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT,
    DISCORD_WEBHOOK_URL,
)
from browser import open_in_brave


# ============================================================
#  WHATSAPP WEB
# ============================================================

def whatsapp_send(contact, message):
    """
    WhatsApp-Nachricht ueber WhatsApp Web senden.
    Oeffnet den Chat im Browser – der Nutzer muss ggf. QR-Code einmalig scannen.
    """
    try:
        import urllib.parse
        # Methode 1: via pywhatkit (sendet direkt)
        try:
            import pywhatkit as kit
            # kit.sendwhatmsg_instantly benoetigt Telefonnummer im Format +491234567890
            # Wenn contact eine Nummer ist:
            if contact.startswith("+") or contact.replace(" ", "").isdigit():
                kit.sendwhatmsg_instantly(
                    phone_no=contact,
                    message=message,
                    wait_time=10,
                    tab_close=False
                )
                return f"WhatsApp-Nachricht an {contact} wird gesendet."
        except ImportError:
            pass

        # Methode 2: WhatsApp Web URL oeffnen
        encoded_msg = urllib.parse.quote(message)
        # Bei Nummer
        if contact.replace("+", "").replace(" ", "").isdigit():
            phone = contact.replace(" ", "").replace("-", "")
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        else:
            # Bei Kontaktname (sucht in WhatsApp Web)
            url = f"https://web.whatsapp.com/send?text={encoded_msg}"
        open_in_brave(url)
        return (
            f"WhatsApp Web geoeffnet. Bitte Nachricht an '{contact}' manuell senden "
            f"(oder einmalig QR-Code scannen)."
        )
    except Exception as e:
        return f"WhatsApp-Fehler: {e}"


# ============================================================
#  E-MAIL SENDEN (SMTP)
# ============================================================

def send_email(to_address, subject, body, cc=None):
    """E-Mail via SMTP senden (Gmail / Outlook / andere)."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "E-Mail nicht konfiguriert (EMAIL_ADDRESS und EMAIL_PASSWORD in config.py eintragen)."
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_address
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as srv:
            srv.starttls()
            srv.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            recipients = [to_address] + ([cc] if cc else [])
            srv.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())

        return f"E-Mail an {to_address} gesendet: '{subject}'"
    except smtplib.SMTPAuthenticationError:
        return "E-Mail-Fehler: Authentifizierung fehlgeschlagen – Passwort oder App-Passwort pruefen."
    except Exception as e:
        return f"E-Mail-Fehler: {e}"


def compose_email_browser(to_address="", subject="", body=""):
    """E-Mail-Entwurf im Standard-Mailclient oeffnen."""
    try:
        import urllib.parse
        mailto = (
            f"mailto:{urllib.parse.quote(to_address)}"
            f"?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )
        os.startfile(mailto)
        return f"E-Mail-Entwurf an {to_address} geoeffnet."
    except Exception as e:
        return f"Fehler beim Oeffnen des E-Mail-Entwurfs: {e}"


# ============================================================
#  DISCORD
# ============================================================

def discord_send_webhook(message, channel_webhook=None):
    """Discord-Nachricht per Webhook senden."""
    webhook_url = channel_webhook or DISCORD_WEBHOOK_URL
    if not webhook_url:
        return "Discord-Webhook nicht konfiguriert (DISCORD_WEBHOOK_URL in config.py eintragen)."
    try:
        import requests
        payload = {"content": message}
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            return "Discord-Nachricht gesendet."
        return f"Discord-Fehler: HTTP {r.status_code}"
    except Exception as e:
        return f"Discord-Fehler: {e}"


def discord_open_channel(channel_name=None):
    """Discord oeffnen und ggf. in einen Kanal navigieren."""
    try:
        # Discord als App starten
        discord_path = os.path.expandvars("%LOCALAPPDATA%\\Discord\\Update.exe")
        if os.path.exists(discord_path):
            subprocess.Popen(
                [discord_path, "--processStart", "Discord.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)
        else:
            open_in_brave("https://discord.com/app")

        if channel_name:
            return f"Discord geoeffnet. Bitte manuell zu Kanal '{channel_name}' navigieren."
        return "Discord geoeffnet."
    except Exception as e:
        return f"Discord-Fehler: {e}"


# ============================================================
#  SMS (Windows-Nachrichtendienst – optional)
# ============================================================

def send_sms_yourphone(contact, message):
    """SMS ueber Windows 'Your Phone' / 'Link to Windows' App senden."""
    try:
        os.startfile("ms-yourphone:")
        return "Link-to-Windows-App geoeffnet. Bitte SMS manuell senden."
    except Exception as e:
        return f"Fehler: {e}"
