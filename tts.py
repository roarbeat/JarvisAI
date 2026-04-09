"""
Text-to-Speech fuer Jarvis (Piper TTS).
Unterstuetzt Lautstaerkeregelung via ROBIN_VOICE_VOLUME.
Unterstuetzt Unterbrechung durch 'Jarvis stopp'.
"""
import os
import re
import sys
import time
import threading
import subprocess
import tempfile

import sounddevice as sd
import numpy as np
import wave

from config import PIPER_EXE, PIPER_VOICE, ROBIN_VOICE_VOLUME
from phonetic import phonetic_fix

# Lautstaerke zur Laufzeit aenderbar
_current_volume = ROBIN_VOICE_VOLUME

# Globales Stopp-Event (wird von interrupt-Thread gesetzt)
_stop_event = threading.Event()


def set_voice_volume(level):
    """Jarvis-Stimme Lautstaerke setzen (0.0 bis 2.0)."""
    global _current_volume
    _current_volume = max(0.0, min(2.0, float(level)))
    return f"Stimm-Lautstaerke auf {int(_current_volume * 100)}%."


def get_voice_volume():
    return _current_volume


def get_stop_event():
    """Gibt das globale Stopp-Event zurueck."""
    return _stop_event


def reset_stop_event():
    """Stopp-Event zuruecksetzen (nach Unterbrechung)."""
    _stop_event.clear()


class Speaker:
    def __init__(self):
        if not os.path.exists(PIPER_EXE):
            print(f"  piper.exe fehlt: {PIPER_EXE}")
            sys.exit(1)
        if not os.path.exists(PIPER_VOICE):
            print(f"  Stimme fehlt: {PIPER_VOICE}")
            sys.exit(1)
        print("  Piper TTS bereit.")

    def stop(self):
        """Sprachausgabe sofort unterbrechen."""
        _stop_event.set()
        try:
            sd.stop()
        except Exception:
            pass

    def say(self, text):
        if not text or not text.strip():
            return

        # Vor dem Sprechen Stopp-Event pruefen
        if _stop_event.is_set():
            return

        # Text bereinigen
        text = re.sub(r"```[\w]*\s*\n.*?\n```", "", text, flags=re.DOTALL)
        text = re.sub(r"\{[^}]{0,300}\}", "", text)
        text = re.sub(r"[*_`#>~|]", "", text)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = phonetic_fix(text)
        if not text:
            return

        # Langer Text: satzweise aufteilen fuer bessere Unterbrechbarkeit
        sentences = self._split_sentences(text)

        print(f"  Jarvis: {text}")

        for sentence in sentences:
            if _stop_event.is_set():
                break
            if not sentence.strip():
                continue
            self._speak_sentence(sentence.strip())

    def _split_sentences(self, text):
        """Teilt Text in Saetze auf."""
        # Splitte an Satzenden, aber behalte kurze Texte zusammen
        if len(text) < 100:
            return [text]
        parts = re.split(r'(?<=[.!?])\s+', text)
        return parts if parts else [text]

    def _speak_sentence(self, text):
        """Spricht einen einzelnen Satz via Piper + sounddevice."""
        if _stop_event.is_set():
            return

        tmp_path = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()

            r = subprocess.run(
                [PIPER_EXE, "--model", PIPER_VOICE, "--output_file", tmp_path],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30
            )
            if r.returncode != 0:
                raise Exception(r.stderr.decode("utf-8", errors="ignore")[:200])
            if os.path.getsize(tmp_path) < 500:
                raise Exception("WAV leer")

            # WAV laden und mit sounddevice abspielen (immer, fuer Unterbrechbarkeit)
            audio, samplerate = self._load_wav(tmp_path)

            vol = _current_volume
            if abs(vol - 1.0) > 0.05:
                audio = np.clip(audio * vol, -1.0, 1.0)

            if not _stop_event.is_set():
                sd.play(audio, samplerate=samplerate)
                # Warten mit Event-Check alle 50ms (zeitbasiert, sd.get_stream kann fehlen)
                duration = len(audio) / samplerate
                t0 = time.time()
                while (time.time() - t0) < duration + 0.3:
                    if _stop_event.is_set():
                        sd.stop()
                        break
                    time.sleep(0.05)

        except Exception as e:
            print(f"  TTS-Fehler: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _load_wav(self, wav_path):
        """WAV-Datei laden und als float32-Array zurueckgeben."""
        with wave.open(wav_path, "rb") as wf:
            frames     = wf.readframes(wf.getnframes())
            samplerate = wf.getframerate()
            sampwidth  = wf.getsampwidth()
            nchannels  = wf.getnchannels()

        dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
        dtype     = dtype_map.get(sampwidth, np.int16)
        audio     = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        audio    /= np.iinfo(dtype).max

        if nchannels > 1:
            audio = audio.reshape(-1, nchannels)

        return audio, samplerate
