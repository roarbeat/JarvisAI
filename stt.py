"""
Speech-to-Text fuer Jarvis (Faster-Whisper + Silero VAD).
Nur Deutsch. Empfindlichere und laengere Aufnahme.
"""
import re
import time
import threading

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    WAKE_WORD, SAMPLE_RATE, CHANNELS,
    WHISPER_MODEL_WAKE, WHISPER_MODEL_CMD,
    SILENCE_DURATION, MAX_RECORD_SECONDS, WAKE_RECORD_SECONDS,
    WAKE_WORD_SENSITIVITY,
)

# Laufzeit-aenderbar (fuer set_wake_sensitivity)
VAD_THRESHOLD = WAKE_WORD_SENSITIVITY

# Thread-Lock fuer Whisper-Modell (CUDA ist nicht thread-safe)
_whisper_lock = threading.Lock()


class Listener:
    def __init__(self):
        import torch
        self.torch = torch

        print(f"  Lade Faster-Whisper '{WHISPER_MODEL_WAKE}'...")
        self.wake_model = WhisperModel(WHISPER_MODEL_WAKE, device="cuda", compute_type="float16")

        if WHISPER_MODEL_CMD != WHISPER_MODEL_WAKE:
            print(f"  Lade Faster-Whisper '{WHISPER_MODEL_CMD}'...")
            self.cmd_model = WhisperModel(WHISPER_MODEL_CMD, device="cuda", compute_type="float16")
        else:
            self.cmd_model = self.wake_model

        print("  Lade Silero VAD...")
        self.vad_model, _ = self.torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True
        )
        self.vad_model.eval()
        print("  Faster-Whisper & VAD bereit.")

    def _record_until_silence(self, max_s=MAX_RECORD_SECONDS):
        """Nimmt auf bis Stille erkannt wird – empfindlicher und geduldiger."""
        chunks, silence_start, heard = [], None, False

        def cb(indata, *_):
            chunks.append(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
                            blocksize=512, callback=cb):
            t0       = time.time()
            last_idx = 0

            while time.time() - t0 < max_s:
                time.sleep(0.01)

                while last_idx < len(chunks):
                    chunk    = chunks[last_idx].flatten()
                    last_idx += 1

                    if len(chunk) == 512:
                        tensor = self.torch.from_numpy(chunk).unsqueeze(0)
                        prob   = self.vad_model(tensor, SAMPLE_RATE).item()

                        # Empfindlichkeit: globaler VAD_THRESHOLD
                        if prob > VAD_THRESHOLD:
                            heard         = True
                            silence_start = None
                        elif heard:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start > SILENCE_DURATION:
                                break

                if heard and silence_start is not None and (time.time() - silence_start > SILENCE_DURATION):
                    break

        return np.concatenate(chunks).flatten() if chunks else None

    def _record_chunk(self, sec):
        a = sd.rec(int(sec * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
        sd.wait()
        return a.flatten()

    def _transcribe(self, audio, model):
        """Transkription – nur Deutsch. Thread-safe durch Lock."""
        with _whisper_lock:
            segments, _ = model.transcribe(
                audio,
                language="de",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                initial_prompt="Sprachbefehle auf Deutsch."
            )
            return "".join([segment.text for segment in segments]).strip()

    def listen_for_wake_word(self):
        """Lauscht auf Wake-Word 'Jarvis' und Varianten."""
        varianten = [
            WAKE_WORD,          # "jarvis"
            "jarwis", "jarwes", "jarves", "yarvis",
            "garvis", "dschärwis", "djarvis",
            "jarvis,", "jarvis.", "jarvis!",
            "hey jarvis", "hei jarvis", "ok jarvis",
        ]
        while True:
            a = self._record_chunk(WAKE_RECORD_SECONDS)
            # Mindestpegel pruefen (sehr leise = ignorieren)
            if np.abs(a).mean() * 32768 < 5:
                continue
            t = self._transcribe(a, self.wake_model).lower()
            if t and len(t) > 2 and not all(c in ".-!?, " for c in t):
                print(f"  [hoert]: \"{t}\"")
            if any(w in t for w in varianten):
                return a

    def listen_quick(self, timeout=4.0):
        """Kurzes Aufnahme-Fenster fuer Folgefragen (kein Wake-Word noetig).
        Gibt leeren String zurueck wenn nichts gesprochen wurde."""
        a = self._record_until_silence(max_s=timeout)
        if a is None or len(a) < SAMPLE_RATE * 0.4:
            return ""
        t = self._transcribe(a, self.cmd_model)
        for w in ["jarvis", "jarwis", "garvis"]:
            t = re.sub(rf"\b{w}\b", "", t, flags=re.IGNORECASE).strip()
        return t.strip("., !?").strip()

    def listen_for_stop_word(self, stop_event):
        """Laeuft im Hintergrund-Thread waehrend Jarvis spricht.
        Setzt stop_event wenn 'Stopp' erkannt wird."""
        if stop_event.is_set():
            return

        chunks = []

        def cb(indata, *_):
            if not stop_event.is_set():
                chunks.append(indata.copy())

        stop_words = ["stopp", "stop", "halt", "aufhoer", "schweig", "ruhig"]
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS,
                dtype="float32", blocksize=512, callback=cb
            ):
                while not stop_event.is_set():
                    time.sleep(0.3)
                    if len(chunks) >= 20:   # ~0.6 Sekunden Audio
                        audio = np.concatenate(chunks).flatten()
                        chunks.clear()
                        # Energiecheck – ignoriere sehr leise Signale (TTS-Bleed)
                        energy = float(np.abs(audio).mean())
                        if energy > 0.012:
                            try:
                                t = self._transcribe(audio, self.wake_model).lower()
                                if any(w in t for w in stop_words):
                                    stop_event.set()
                                    return
                            except Exception:
                                # Lock belegt (Hauptthread transkribiert gerade) – Skip
                                pass
        except Exception as e:
            print(f"  [Interrupt-Listener] Fehler: {e}")

    def listen_command(self, wake_audio=None):
        """Nimmt den Befehl nach dem Wake-Word auf – laenger und geduldiger."""
        # Pruefen ob der Befehl schon im Wake-Chunk steckt
        if wake_audio is not None:
            cmd_inline = self._transcribe(wake_audio, self.cmd_model)
            for w in ["jarvis", "jarwis", "garvis"]:
                cmd_inline = re.sub(rf"\b{w}\b[,.]?\s*", "", cmd_inline, flags=re.IGNORECASE).strip()
            cmd_inline = cmd_inline.strip("., !?").strip()
            if len(cmd_inline) > 3:
                print(f"  [Inline-Befehl]: \"{cmd_inline}\"")
                return cmd_inline

        # Frisch aufnehmen
        a = self._record_until_silence(max_s=MAX_RECORD_SECONDS)
        if a is None or len(a) < SAMPLE_RATE * 0.3:
            return ""
        t = self._transcribe(a, self.cmd_model)
        for w in ["jarvis", "jarwis", "garvis"]:
            t = re.sub(rf"\b{w}\b", "", t, flags=re.IGNORECASE).strip()
        return t
