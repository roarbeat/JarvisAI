# JARVIS – Lokaler KI-Sprachassistent

## Projektübersicht
Jarvis ist ein vollständig lokaler Windows-Sprachassistent. Er läuft auf dem PC des Nutzers (Robin) und benötigt keine Cloud-Dienste für Kernfunktionen.

**Stack:**
- **STT:** faster-whisper (Medium-Modell, CUDA), Silero VAD für Stille-Erkennung
- **LLM:** Ollama mit Modell `gemma4:e4b`
- **TTS:** Piper TTS (`de_DE-thorsten-high.onnx`)
- **Wake-Word:** "Jarvis" (+ phonetische Varianten)
- **Browser:** Brave (mit Fallback auf Standard-Browser)
- **Smart Home:** Home Assistant (`http://192.168.0.187:8123`)
- **Nutzer:** Robin

## Dateistruktur

| Datei | Aufgabe |
|-------|---------|
| `jarvis.py` | Hauptschleife: Wake-Word → Befehl → LLM → Aktion → Sprache |
| `config.py` | Alle Konstanten (Modelle, Pfade, API-Keys) |
| `stt.py` | Listener: Wake-Word + Befehlsaufnahme (Whisper + VAD) |
| `tts.py` | Speaker: Piper TTS, Lautstärke, Unterbrechbarkeit |
| `llm.py` | ask_llm(): System-Prompt, Konversationsverlauf, Action-Parsing |
| `actions.py` | execute_action()-Dispatcher für alle Aktionen |
| `browser.py` | Brave-Integration, APP_MAP, open_app(), open_in_brave() |
| `weather.py` | Wetter via wttr.in + open-meteo (kein API-Key nötig) |
| `smart_home.py` | Home Assistant REST API |
| `media.py` | Spotify, YouTube, Lautstärke |
| `automation.py` | Timer, Alarm, Erinnerungen, Nacht-Modus |
| `productivity.py` | Rechner, Wikipedia, Notizen, E-Mail |
| `system_monitor.py` | CPU/RAM/GPU, Prozesse, Netzwerk |
| `communication.py` | WhatsApp, E-Mail, Discord |
| `ai_features.py` | Screenshot-Analyse, Clipboard, Gedächtnis |
| `pc_control.py` | Maus, Fenster, Scroll, Clipboard |
| `phonetic.py` | Phonetik-Korrekturen für TTS |

## Wichtige Konfiguration (config.py)
- Wake-Word: `"jarvis"` + Varianten (jarwis, yarvis, garvis, etc.)
- Ollama-Modell: `gemma4:e4b`
- Whisper: Medium (CUDA, float16)
- VAD-Schwellwert: 0.25 (empfindlich)
- Stille-Erkennung: 1.2 Sekunden
- Max. Befehlsaufnahme: 30 Sekunden
- Piper Voice: `de_DE-thorsten-high.onnx`
- Home Assistant: `http://192.168.0.187:8123`

## Bekannte Issues & Fixes
- **initial_prompt in stt.py** MUSS neutral sein (kein "Jarvis ist ein Sprachassistent" – Whisper gibt das sonst als Transkription aus)
- **Wetter**: Direkt den `result`-String sprechen, KEIN zweiter LLM-Call (verändert sonst die Daten)
- **Action-Parsing**: Fallback-JSON-Extraktion notwendig, da `gemma4:e4b` manchmal keinen ```action```-Block erzeugt
- **Screenshot**: PyAutoGUI als primär, PowerShell als Fallback
- **Stopp-Interrupt**: Speaker nutzt `sd.play()` (nicht winsound) für Unterbrechbarkeit via "Jarvis stopp"
- **Folgefragen**: Nach Antwort kurzes Aufnahmefenster (4 Sek.) ohne erneutes Wake-Word nötig

## Entwicklungshinweise
- Alle Module werden lazy importiert (kein Import-Fehler bricht das System)
- Konversationsverlauf: max. 10 Nachrichten in `llm.py`
- Aktionen brauchen immer ein ```action```-JSON-Objekt mit Schlüssel `"action"`
- TTS bereinigt automatisch Markdown, URLs und JSON vor dem Sprechen
- Piper läuft synchron (subprocess), WAV wird in Temp geschrieben und dann abgespielt

## Start
```
START.bat
```
oder direkt:
```
python jarvis.py
```
