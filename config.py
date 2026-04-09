"""
Konfiguration fuer Jarvis - Lokaler KI-Sprachassistent
"""
import os

# ============================================================
#  ALLGEMEINE EINSTELLUNGEN
# ============================================================

WAKE_WORD          = "jarvis"
OLLAMA_MODEL       = "gemma4:e4b"
SAMPLE_RATE        = 16000
CHANNELS           = 1
WHISPER_MODEL_WAKE = "medium"
WHISPER_MODEL_CMD  = "medium"
USERNAME           = "Robin"

# ============================================================
#  HOME ASSISTANT
# ============================================================

HA_URL   = "http://192.168.0.187:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzMzljYjZjZjQ5NGQ0NTQyOTVmMmE4NGEzNTM0ODc3OSIsImlhdCI6MTc3NTU2NDk2MywiZXhwIjoyMDkwOTI0OTYzfQ.uiqT8tKtbhS4feecXe6PhhmvU-N9QV75GLMzqsjzRJM"

# ============================================================
#  PIPER TTS
# ============================================================

PIPER_EXE   = os.path.join(os.path.dirname(__file__), "piper", "piper", "piper.exe")
PIPER_VOICE = os.path.join(os.path.dirname(__file__), "piper-voice", "de_DE-thorsten-high.onnx")

# Jarvis-Stimme Lautstaerke (0.0 = stumm, 1.0 = normal, 2.0 = doppelt)
ROBIN_VOICE_VOLUME = 1.0

# ============================================================
#  AUFNAHME-EINSTELLUNGEN
#  Empfindlicher & laenger fuer bessere Befehlserkennung
# ============================================================

SILENCE_DURATION    = 1.2   # Sekunden Stille bevor Aufnahme endet (hoeher = geduldiger)
MAX_RECORD_SECONDS  = 30    # Maximale Befehlslaenge
WAKE_RECORD_SECONDS = 4     # Wake-Word-Fenster

# VAD-Schwellwert: 0.2 = sehr empfindlich (leise Stimme), 0.8 = wenig empfindlich
WAKE_WORD_SENSITIVITY = 0.25

# ============================================================
#  SPOTIFY API
# Eintragen unter https://developer.spotify.com/dashboard
# ============================================================

SPOTIFY_CLIENT_ID     = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_REDIRECT_URI  = "http://127.0.0.1:9090/callback"

# ============================================================
#  DISCORD
# Webhook unter Kanal-Einstellungen > Integrationen > Webhooks
# ============================================================

DISCORD_WEBHOOK_URL = ""

# ============================================================
#  E-MAIL (SMTP / IMAP)
# Fuer Gmail: App-Passwort unter myaccount.google.com/security
# ============================================================

EMAIL_ADDRESS     = ""
EMAIL_PASSWORD    = ""
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT   = 587
EMAIL_IMAP_SERVER = "imap.gmail.com"

# ============================================================
#  GOOGLE CALENDAR
# JSON-Datei aus Google Cloud Console (OAuth 2.0 Credentials)
# ============================================================

GOOGLE_CALENDAR_CREDENTIALS = ""

# ============================================================
#  NOTIZEN-ORDNER
# ============================================================

NOTES_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Jarvis_Notizen")

# ============================================================
#  KONVERSATIONSGEDAECHTNIS
# ============================================================

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

# ============================================================
#  SPRACHE (nur Deutsch)
# ============================================================

DEFAULT_LANGUAGE = "de"
