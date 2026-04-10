# JarvisAI – Funktionsreferenz

Lokaler KI-Sprachassistent für Windows. Nutzt Ollama (LLM), Faster-Whisper (STT), Piper TTS und Home Assistant.

---

## Projektstruktur

| Datei | Zuständigkeit |
|---|---|
| `jarvis.py` | Hauptschleife, Wake-Word-Loop, Befehlsverarbeitung |
| `config.py` | Alle Einstellungen (Modell, Pfade, Tokens, API-Keys) |
| `llm.py` | LLM-Integration (Ollama), System-Prompt, Konversationsverlauf |
| `stt.py` | Spracherkennung (Faster-Whisper + Silero VAD) |
| `tts.py` | Sprachausgabe (Piper TTS + sounddevice) |
| `actions.py` | Zentraler Action-Dispatcher – verteilt alle Befehle an Module |
| `browser.py` | Browser- und App-Steuerung |
| `smart_home.py` | Home Assistant Integration |
| `automation.py` | Timer, Alarm, Routinen, Inaktivitätssperre |
| `weather.py` | Wetterdaten (wttr.in / open-meteo) |
| `productivity.py` | Rechner, Einheiten, Währung, Wikipedia, Notizen, E-Mail, Kalender |
| `media.py` | Spotify, YouTube, Lautstärke, Kamera, Medientasten |
| `pc_control.py` | Maus, Tastatur, Fenster, Clipboard, Scrollen |
| `system_monitor.py` | CPU/RAM/GPU, Festplatte, Prozesse, Netzwerk, Windows Update |
| `communication.py` | WhatsApp, E-Mail, Discord |
| `ai_features.py` | Screenshot-Analyse, Clipboard-KI, Dokument-Zusammenfassung, Gedächtnis |
| `phonetic.py` | Phonetische Korrekturen für TTS-Aussprache |

---

## jarvis.py – Hauptprogramm

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `_ist_stoppbefehl(text)` | 87 | Prüft ob der Text ein Stopp-Befehl ist ("stop", "halt", "schweig" usw.) |
| `_ist_abbruchbefehl(text)` | 92 | Prüft ob der Text ein Abbruch-Befehl ist ("abbrechen", "cancel" usw.) |
| `_start_interrupt_thread(listener, speaker)` | 100 | Startet einen Hintergrund-Thread der auf "Jarvis stopp" wartet und die Sprachausgabe unterbricht |
| `_process_command(command, speaker, listener)` | 114 | Verarbeitet einen erkannten Sprachbefehl: ruft `ask_llm()` auf, führt die Aktion aus, spricht das Ergebnis |
| `main()` | 189 | Startet Jarvis: initialisiert STT/TTS, prüft Modell, startet Wake-Word-Schleife |

---

## config.py – Einstellungen

Keine Funktionen – nur Konfigurationsvariablen:

| Variable | Beschreibung |
|---|---|
| `WAKE_WORD` | Wake-Word (Standard: "jarvis") |
| `OLLAMA_MODEL` | LLM-Modell (Standard: "gemma4:e4b") |
| `SAMPLE_RATE` | Mikrofon-Samplerate (16000 Hz) |
| `WHISPER_MODEL_WAKE` | Whisper-Modell für Wake-Word-Erkennung |
| `WHISPER_MODEL_CMD` | Whisper-Modell für Befehlserkennung |
| `USERNAME` | Benutzername für Begrüßungen |
| `HA_URL` | Home Assistant URL |
| `HA_TOKEN` | Home Assistant JWT-Token |
| `PIPER_EXE` | Pfad zur piper.exe |
| `PIPER_VOICE` | Pfad zur Stimmdatei (.onnx) |
| `ROBIN_VOICE_VOLUME` | Standard-Lautstärke der Jarvis-Stimme (0.0–2.0) |
| `SILENCE_DURATION` | Sekunden Stille bis Aufnahme endet |
| `MAX_RECORD_SECONDS` | Maximale Länge einer Befehlsaufnahme |
| `WAKE_RECORD_SECONDS` | Länge des Wake-Word-Fensters |
| `WAKE_WORD_SENSITIVITY` | VAD-Empfindlichkeit (0.2 = sehr empfindlich) |
| `SPOTIFY_CLIENT_ID/SECRET` | Spotify API-Zugangsdaten |
| `DISCORD_WEBHOOK_URL` | Discord Webhook-URL |
| `EMAIL_ADDRESS/PASSWORD` | E-Mail Zugangsdaten (IMAP/SMTP) |
| `GOOGLE_CALENDAR_CREDENTIALS` | Pfad zur Google Calendar OAuth JSON-Datei |
| `NOTES_DIR` | Speicherort für Notizen |
| `MEMORY_FILE` | Speicherort für Jarvis-Gedächtnis (JSON) |

---

## llm.py – KI-Integration

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `check_model_available()` | 161 | Prüft ob das konfigurierte Ollama-Modell installiert ist. Gibt eine Fehlermeldung zurück oder `None` wenn alles OK. Kompatibel mit ollama-API alter und neuer Versionen. |
| `ask_llm(user_text, context="")` | 196 | Sendet den Befehl des Nutzers an das LLM. Gibt `(sprechbarer_text, aktion_dict_oder_None)` zurück. Extrahiert `action`-Blöcke aus der Antwort. Pflegt den Konversationsverlauf. |

---

## stt.py – Spracherkennung

| Klasse / Funktion | Zeile | Beschreibung |
|---|---|---|
| `Listener` (Klasse) | 27 | Kapselt die gesamte Spracherkennung. Lädt Whisper-Modelle (CUDA mit CPU-Fallback) und Silero VAD beim Start. |
| `Listener.__init__()` | 28 | Initialisierung: lädt Wake-Word-Modell, Befehlsmodell und VAD-Modell. |
| `Listener.listen_for_wake_word()` | – | Nimmt kontinuierlich auf und gibt zurück sobald das Wake-Word erkannt wurde. |
| `Listener.listen_command()` | – | Nimmt einen Befehl auf (bis Stille erkannt wird) und gibt den transkribierten Text zurück. |
| `Listener._transcribe()` | – | Interne Methode: transkribiert einen Audio-Buffer mit Whisper, mit VAD-Filterung. |

---

## tts.py – Sprachausgabe

| Funktion / Klasse | Zeile | Beschreibung |
|---|---|---|
| `set_voice_volume(level)` | 28 | Setzt die Lautstärke der Jarvis-Stimme zur Laufzeit (0.0–2.0). |
| `get_voice_volume()` | 35 | Gibt die aktuelle Stimm-Lautstärke zurück. |
| `get_stop_event()` | 39 | Gibt das globale Threading-Event zurück das Sprachausgabe unterbricht. |
| `reset_stop_event()` | 44 | Setzt das Stopp-Event zurück (nach einer Unterbrechung). |
| `Speaker` (Klasse) | 49 | Kapselt die gesamte Sprachausgabe via Piper TTS + sounddevice. |
| `Speaker.say(text)` | 67 | Spricht einen Text aus. Bereinigt Sonderzeichen, teilt lange Texte in Sätze auf, prüft vor jedem Satz ob gestoppt werden soll. |
| `Speaker.stop()` | 59 | Unterbricht die laufende Sprachausgabe sofort. |
| `Speaker._split_sentences(text)` | 97 | Teilt langen Text in einzelne Sätze auf für bessere Unterbrechbarkeit. |
| `Speaker._speak_sentence(text)` | 105 | Spricht einen einzelnen Satz: ruft Piper auf, lädt die WAV-Datei, spielt sie via sounddevice ab. |
| `Speaker._load_wav(wav_path)` | 154 | Lädt eine WAV-Datei als float32-Array für sounddevice. |

---

## actions.py – Zentraler Dispatcher

Empfängt von `ask_llm()` ein Action-Dict und leitet es an das zuständige Modul weiter.

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `_load(module_name)` | 22 | Lazy-Import-Helfer: lädt ein Modul einmalig und cached es. Fehler beim Import brechen das System nicht ab. |
| `web_search(query)` | 36 | Öffnet eine Brave-Suche nach dem angegebenen Begriff. |
| `execute_action(action_data)` | 80 | Hauptfunktion: nimmt ein Action-Dict, wendet Aliase an und leitet an das richtige Modul weiter. |

### Unterstützte Aktionen in `execute_action()`

| Action-Name | Modul | Beschreibung |
|---|---|---|
| `open_app` | browser.py | App oder Website öffnen |
| `close_app` | – | App per Prozessname beenden |
| `get_weather` | weather.py | Wetter für eine Stadt abrufen |
| `web_search` | browser.py | Websuche in Brave öffnen |
| `open_website` | browser.py | Direkte URL öffnen |
| `search_files` | – | Dateien nach Name durchsuchen |
| `open_file` | – | Datei mit Standardprogramm öffnen |
| `set_volume` | – | System-Lautstärke setzen (0–100%) |
| `volume_up/down/mute` | – | Lautstärke rauf/runter/stumm |
| `set_app_volume` | media.py | Lautstärke einer einzelnen App setzen |
| `set_voice_volume` | tts.py | Jarvis-Stimme lauter/leiser stellen |
| `set_brightness` | – | Bildschirmhelligkeit setzen |
| `open_settings` | – | Windows-Einstellungsseite öffnen |
| `night_light` | – | Nachtlicht-Einstellungen öffnen |
| `bluetooth_toggle` | – | Bluetooth-Einstellungen öffnen |
| `wifi_toggle` | – | WLAN ein-/ausschalten |
| `shutdown/restart/sleep/lock` | – | System herunterfahren, neu starten, Ruhezustand, sperren |
| `abort_shutdown` | – | Geplanten Shutdown abbrechen |
| `screenshot` | – | Screenshot auf Desktop speichern (pyautogui / PIL / PowerShell) |
| `type_text` | – | Text per Tastatur eintippen |
| `run_command` | – | Shell-Befehl ausführen |
| `control_home` | smart_home.py | Smart-Home-Gerät über Home Assistant schalten |
| `move_mouse` | pc_control.py | Maus bewegen (Richtung oder Koordinaten) |
| `click_mouse` | pc_control.py | Mausklick (links/rechts/doppelt) |
| `manage_window` | pc_control.py | Fenster minimieren/maximieren/schließen/snappen |
| `clipboard` | pc_control.py | Zwischenablage lesen/setzen/einfügen |
| `scroll` | pc_control.py | Seite hoch/runter scrollen |
| `move_to_monitor` | pc_control.py | Fenster auf anderen Monitor verschieben |
| `taskbar_pin` | pc_control.py | App an Taskleiste anheften/lösen |
| `spotify` | media.py | Spotify steuern (play/pause/next/prev/suche/playlist) |
| `youtube` | media.py | YouTube öffnen oder suchen |
| `mute_call` | media.py | Mikrofon in Teams/Zoom/Discord stumm schalten |
| `camera_toggle` | media.py | Kamera in Video-Calls ein-/ausschalten |
| `media_key` | media.py | Medientaste senden (play/pause/next/prev/stop) |
| `set_timer` | automation.py | Timer starten |
| `set_alarm` | automation.py | Wecker stellen |
| `remind_me` | automation.py | Erinnerung erstellen |
| `morning_routine` | automation.py | Morgenroutine starten |
| `night_mode` | automation.py | Nacht-Modus aktivieren/deaktivieren |
| `auto_lock` | automation.py | Automatische Sperre bei Inaktivität |
| `define_command` | automation.py | Benutzerdefinierten Sprachbefehl erstellen |
| `run_command_custom` | automation.py | Benutzerdefinierten Befehl ausführen |
| `list_timers` | automation.py | Aktive Timer auflisten |
| `calculate` | productivity.py | Mathematischen Ausdruck berechnen |
| `convert_currency` | productivity.py | Währung umrechnen |
| `convert_unit` | productivity.py | Einheit umrechnen (Länge/Gewicht/Temperatur/etc.) |
| `wikipedia` | productivity.py | Wikipedia-Artikel zusammenfassen |
| `save_note` | productivity.py | Notiz speichern |
| `read_note` | productivity.py | Letzte Notiz vorlesen |
| `list_notes` | productivity.py | Alle Notizen auflisten |
| `read_emails` | productivity.py | Ungelesene E-Mails vorlesen |
| `read_calendar` | productivity.py | Google Calendar Termine lesen |
| `system_stats` | system_monitor.py | CPU/RAM/GPU-Auslastung abrufen |
| `disk_space` | system_monitor.py | Festplattenplatz prüfen |
| `list_processes` | system_monitor.py | Laufende Prozesse auflisten |
| `kill_process` | system_monitor.py | Prozess beenden |
| `network_speed` | system_monitor.py | Netzwerkgeschwindigkeit messen |
| `network_info` | system_monitor.py | Netzwerkinformationen abrufen |
| `ping` | system_monitor.py | Host anpingen |
| `windows_update` | system_monitor.py | Windows Updates prüfen |
| `system_summary` | system_monitor.py | Gesamtübersicht des Systems |
| `whatsapp_send` | communication.py | WhatsApp-Nachricht senden |
| `send_email` | communication.py | E-Mail senden (SMTP) |
| `compose_email` | communication.py | E-Mail im Browser verfassen |
| `discord_send` | communication.py | Discord-Nachricht per Webhook senden |
| `discord_open` | communication.py | Discord-Kanal öffnen |
| `analyze_screenshot` | ai_features.py | Screenshot aufnehmen und mit KI analysieren |
| `read_clipboard` | ai_features.py | Inhalt der Zwischenablage vorlesen |
| `summarize_clipboard` | ai_features.py | Text in Zwischenablage mit KI zusammenfassen |
| `summarize_document` | ai_features.py | Datei (txt/pdf/docx) mit KI zusammenfassen |
| `save_preference` | ai_features.py | Nutzereinstellung dauerhaft speichern |
| `get_preference` | ai_features.py | Gespeicherte Einstellung abrufen |
| `list_preferences` | ai_features.py | Alle gespeicherten Einstellungen auflisten |
| `set_wake_sensitivity` | stt.py | VAD-Empfindlichkeit für Wake-Word anpassen |

---

## browser.py – Browser & Apps

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `open_in_brave(url)` | 30 | Öffnet eine URL in Brave. Fallbacks: Windows `start`, Python `webbrowser`, `os.startfile`. |
| `open_app(name)` | 151 | Öffnet eine App per Name. Sucht in einer internen App-Map (Spotify, Netflix, Chrome, etc.) und versucht mehrere Öffnungsmethoden (os.startfile, subprocess, Winstore-URI). |

---

## smart_home.py – Home Assistant

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `control_smart_home(device_name, action_state)` | 10 | Schaltet ein Smart-Home-Gerät ein oder aus. Ruft alle HA-Entities ab, sucht per Fuzzy-Match nach dem Gerätenamen (Umlaute, Teilwörter), sendet dann den turn_on/turn_off Service-Call. Unterstützt light, switch, media_player, climate, scene. |

---

## automation.py – Timer & Routinen

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `set_speak_callback(fn)` | 25 | Registriert die `Speaker.say`-Funktion damit Timer-Benachrichtigungen gesprochen werden können. |
| `update_activity()` | 38 | Aktualisiert den Inaktivitäts-Zeitstempel (wird nach jedem Befehl aufgerufen). |
| `set_timer(seconds, minutes, hours, label)` | 48 | Startet einen Timer in einem Daemon-Thread. Spricht eine Benachrichtigung wenn die Zeit abgelaufen ist. |
| `set_alarm(hour, minute, label)` | 87 | Stellt einen Wecker für eine bestimmte Uhrzeit. Läuft in eigenem Thread. |
| `remind_me(text, minutes, seconds, hours)` | 111 | Erstellt eine Erinnerung nach der angegebenen Zeit. |
| `list_timers()` | 134 | Gibt alle aktuell laufenden Timer als Text zurück. |
| `morning_routine(speaker_obj)` | 146 | Startet die Morgenroutine: begrüßt den Nutzer, öffnet Browser, Kalender, Nachrichten. |
| `night_mode(enable)` | 191 | Aktiviert/deaktiviert den Nacht-Modus: Helligkeit reduzieren, Nachtlicht an, Lautstärke senken. |
| `set_auto_lock(enable, minutes)` | 259 | Aktiviert/deaktiviert die automatische PC-Sperre nach Inaktivität. |
| `define_custom_command(name, actions_list)` | 300 | Speichert einen benutzerdefinierten Sprachbefehl als JSON-Datei. |
| `run_custom_command(name)` | 311 | Führt einen gespeicherten benutzerdefinierten Befehl aus. |
| `list_custom_commands()` | 327 | Listet alle gespeicherten benutzerdefinierten Befehle auf. |

---

## weather.py – Wetter

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `_fetch_weather(lat, lon, city_name)` | 21 | Interne Funktion: holt Wetterdaten von open-meteo per Koordinaten. |
| `get_weather(city)` | 41 | Hauptfunktion: ruft aktuelles Wetter, Tageshöchstwert und Regenwahrscheinlichkeit ab. Primär via wttr.in, Fallback via open-meteo Geocoding. Kein API-Key nötig. |

---

## productivity.py – Information & Produktivität

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `calculate(expression)` | 24 | Berechnet einen deutschen Sprachausdruck ("347 mal 12", "wurzel von 16"). Unterstützt +/-/*/÷/Potenzen/Wurzel/Pi/Prozent. |
| `convert_currency(amount, from_currency, to_currency)` | 56 | Währungsumrechnung via Frankfurter API (kostenlos, kein API-Key). |
| `convert_unit(amount, from_unit, to_unit)` | 103 | Einheitenumrechnung: Länge, Gewicht, Temperatur, Volumen, Geschwindigkeit, Datenmenge. |
| `wikipedia_search(query, lang)` | 144 | Wikipedia-Schnellabfrage. Nutzt `wikipedia`-Paket oder direkt die REST-API als Fallback. |
| `save_note(text, filename)` | 177 | Speichert eine Notiz als .txt-Datei im Notizen-Ordner mit Zeitstempel. |
| `list_notes()` | 196 | Listet alle gespeicherten Notizen auf. |
| `read_last_note()` | 209 | Liest die neueste Notiz vor. |
| `read_emails(max_count, only_unread)` | 231 | Liest ungelesene E-Mails via IMAP. Gibt Absender und Betreff zurück. |
| `get_calendar_events(max_results)` | 268 | Ruft heutige Google Calendar Termine ab. Fallback: öffnet Windows-Kalender. |

---

## media.py – Medien

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `_get_spotify()` | 19 | Interne Hilfsfunktion: initialisiert die Spotipy-Verbindung. |
| `spotify_control(action, query, playlist, device_id)` | 82 | Steuert Spotify: play/pause/next/prev/suche/playlist/shuffle/volume/like. |
| `youtube_action(action, query)` | 192 | Öffnet YouTube oder sucht nach einem Begriff. |
| `set_app_volume(app_name, level)` | 224 | Setzt die Lautstärke einer einzelnen App via Windows Audio Session API. |
| `get_app_volume(app_name)` | 246 | Gibt die aktuelle Lautstärke einer App zurück. |
| `set_all_app_volumes(level)` | 261 | Setzt die Lautstärke aller laufenden Apps gleichzeitig. |
| `mute_call(app)` | 285 | Schaltet das Mikrofon in Teams/Zoom/Discord stumm (per Tastenkürzel). |
| `camera_toggle(app)` | 324 | Schaltet die Kamera in einem Video-Call ein oder aus. |
| `media_key(action)` | 351 | Sendet eine Medientaste (play/pause/next/prev/stop) ans System. |

---

## pc_control.py – PC-Steuerung

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `move_mouse(direction, x, y, target, steps)` | 18 | Bewegt die Maus: entweder relativ (links/rechts/oben/unten) oder zu absoluten Koordinaten. |
| `click_mouse(button, double, x, y)` | 57 | Klickt die Maus (links, rechts, mittig, einfach oder doppelt). |
| `manage_window(action, app_name)` | 83 | Fenster verwalten: minimize, maximize, close, restore, snap_left, snap_right, switch. |
| `clipboard_action(action, text)` | 160 | Zwischenablage-Operationen: get (lesen), set (setzen), paste (einfügen), type_paste (tippen+einfügen), copy_selection (Auswahl kopieren). |
| `scroll_page(direction, amount)` | 200 | Scrollt die Seite hoch oder runter. |
| `move_window_to_monitor(direction)` | 231 | Verschiebt das aktive Fenster auf einen anderen Monitor. |
| `taskbar_pin(app_name, pin)` | 249 | Heftet eine App an die Taskleiste an oder löst sie (via PowerShell). |

---

## system_monitor.py – Systemüberwachung

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `get_system_stats(detail)` | 16 | Gibt CPU-, RAM- und GPU-Auslastung zurück. `detail`: "all", "cpu", "ram", "gpu". |
| `get_cpu()` | 80 | CPU-Auslastung und Kernanzahl. |
| `get_ram()` | 84 | RAM-Nutzung in GB und Prozent. |
| `get_gpu()` | 88 | GPU-Auslastung via GPUtil (NVIDIA). Fallback-Text wenn nicht verfügbar. |
| `get_disk_space(drive)` | 96 | Freier und belegter Speicherplatz eines Laufwerks. |
| `list_processes(top, sort_by)` | 125 | Listet die Top-N Prozesse nach CPU oder RAM-Nutzung. |
| `kill_process(name_or_pid)` | 148 | Beendet einen Prozess per Name oder PID. |
| `find_process(name)` | 169 | Sucht einen laufenden Prozess per Name. |
| `get_network_speed()` | 184 | Misst Download- und Upload-Geschwindigkeit (via speedtest-cli). |
| `ping(host)` | 204 | Pingt einen Host an und gibt Latenz zurück. |
| `get_network_info()` | 221 | IP-Adresse, Hostname, Netzwerkinformationen. |
| `check_windows_updates()` | 239 | Prüft verfügbare Windows-Updates via PowerShell. |
| `trigger_windows_update()` | 255 | Startet die Windows Update-Suche. |
| `system_summary()` | 275 | Gesamtübersicht: CPU, RAM, GPU, Festplatte, Netzwerk als einzelner Text. |

---

## communication.py – Kommunikation

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `whatsapp_send(contact, message)` | 24 | Öffnet WhatsApp Web und sendet eine Nachricht an eine Nummer oder einen Kontaktnamen. |
| `send_email(to_address, subject, body, cc)` | 69 | Sendet eine E-Mail via SMTP (konfiguriert in config.py). |
| `compose_email_browser(to_address, subject, body)` | 96 | Öffnet den Standard-E-Mail-Client mit vorausgefüllten Feldern (mailto-Link). |
| `discord_send_webhook(message, channel_webhook)` | 115 | Sendet eine Nachricht an einen Discord-Kanal via Webhook. |
| `discord_open_channel(channel_name)` | 131 | Öffnet Discord und navigiert zu einem bestimmten Kanal. |
| `send_sms_yourphone(contact, message)` | 156 | SMS senden via Windows "Dein Telefon"-App. |

---

## ai_features.py – KI-Funktionen

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `_take_screenshot(path)` | 20 | Interne Funktion: macht einen Screenshot via pyautogui, PIL oder PowerShell. |
| `analyze_screenshot(question)` | 63 | Screenshot aufnehmen und ans LLM senden mit einer Frage. Skaliert das Bild auf 1280×720. |
| `read_clipboard()` | 101 | Liest den Inhalt der Zwischenablage und gibt ihn zurück. |
| `summarize_clipboard()` | 116 | Sendet den Zwischenablage-Inhalt ans LLM zur Zusammenfassung. |
| `summarize_document(file_path)` | 141 | Liest eine Datei (txt/pdf/docx) und lässt sie vom LLM zusammenfassen. |
| `_load_memory()` | 208 | Interne Funktion: lädt das Gedächtnis aus memory.json. |
| `_save_memory(data)` | 215 | Interne Funktion: speichert das Gedächtnis in memory.json. |
| `save_preference(key, value)` | 222 | Speichert eine Nutzereinstellung dauerhaft (z.B. Lieblingsfarbe, Wohnort). |
| `get_preference(key)` | 236 | Ruft eine gespeicherte Einstellung ab. |
| `list_preferences()` | 248 | Listet alle gespeicherten Einstellungen auf. |
| `delete_preference(key)` | 260 | Löscht eine gespeicherte Einstellung. |
| `forget_all()` | 273 | Löscht das gesamte Jarvis-Gedächtnis. |
| `switch_language(lang)` | 289 | Schaltet zwischen Deutsch und Englisch um. Speichert die Einstellung. |
| `get_current_language()` | 305 | Gibt die aktuelle Sprache zurück ("de" oder "en"). |

---

## phonetic.py – TTS-Korrekturen

| Funktion | Zeile | Beschreibung |
|---|---|---|
| `phonetic_fix(text)` | 96 | Korrigiert die Aussprache für Piper TTS: ersetzt englische Abkürzungen, Programmnamen, Zahlen und Sonderzeichen durch deutsche Aussprache-Varianten (z.B. "YouTube" → "Jutjub", "GPU" → "GePU"). |

---

## Abhängigkeiten

```
faster-whisper       # Spracherkennung
silero-vad           # Voice Activity Detection
sounddevice          # Audioaufnahme und -ausgabe
numpy                # Audio-Verarbeitung
piper (extern)       # Text-to-Speech
ollama               # LLM-Client
requests             # HTTP-Anfragen
psutil               # Prozess-/Systeminfos
pycaw                # Windows Audio API
spotipy              # Spotify API
pyautogui            # Maus/Tastatur/Screenshot
Pillow               # Bildverarbeitung
GPUtil               # NVIDIA GPU-Infos
wikipedia            # Wikipedia-Abfragen
pyperclip            # Zwischenablage
```

---

## Konfiguration (Schnellstart)

1. `config.py` öffnen
2. `OLLAMA_MODEL` auf das installierte Modell setzen
3. `PIPER_EXE` und `PIPER_VOICE` auf die lokalen Piper-Pfade setzen
4. Optional: `HA_URL` und `HA_TOKEN` für Smart Home
5. Optional: `SPOTIFY_CLIENT_ID/SECRET` für Spotify
6. Jarvis starten: `python jarvis.py`
