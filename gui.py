"""
J A R V I S  –  Grafische Benutzeroberflaeche
==============================================
Startet Jarvis mit moderner Dark-UI statt Terminal.

Abhaengigkeit:
    pip install customtkinter

Starten:
    python gui.py
"""

import sys
import os
import math
import time
import queue
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import customtkinter as ctk

from config   import OLLAMA_MODEL, USERNAME, PIPER_EXE, PIPER_VOICE
from llm      import ask_llm, check_model_available
from tts      import Speaker, get_stop_event, reset_stop_event
from stt      import Listener
from actions  import execute_action
import automation

# ================================================================
#  FARBPALETTE
# ================================================================

C = {
    "bg":       "#090b12",
    "panel":    "#0e1018",
    "card":     "#131622",
    "border":   "#1c2035",
    "accent":   "#00c8ff",
    "accent2":  "#004d63",
    "dim":      "#3a4460",
    "text":     "#c8d6f0",
    "text_dim": "#5a6a90",
    "ok":       "#00ffaa",
    "warn":     "#ffaa33",
    "err":      "#ff5566",
    "user_bg":  "#122040",
    "bot_bg":   "#0c1a28",
    "sep":      "#171c2e",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ================================================================
#  ANIMIERTER JARVIS-KREIS
# ================================================================

class JarvisOrb(tk.Canvas):
    """Holographischer Jarvis-Kreis mit Animations-Loop."""

    STATES = ("idle", "listening", "thinking", "speaking")

    def __init__(self, master, size=210, **kw):
        super().__init__(
            master, width=size, height=size,
            bg=C["bg"], highlightthickness=0, **kw
        )
        self.size   = size
        self.cx     = size / 2
        self.cy     = size / 2
        self.r      = size / 2 - 14

        self._state    = "idle"
        self._angle    = 0.0
        self._pulse    = 0.0
        self._pulse_v  = 0.012
        self._rings    = []   # [{radius, alpha, expanding}]
        self._bars     = [0.0] * 12   # Welle-Balken

        self._animate()

    # ── public ──────────────────────────────────────────────

    def set_state(self, state: str):
        if state not in self.STATES:
            return
        if state == "listening" and self._state != "listening":
            self._spawn_ring()
        self._state = state

    # ── private ─────────────────────────────────────────────

    @staticmethod
    def _blend(color: str, alpha: float, bg: str = "#090b12") -> str:
        """Simuliert Alpha durch Mischen mit dem Hintergrund (tkinter kennt kein RGBA)."""
        try:
            def parse(h):
                h = h.lstrip("#")
                return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r1, g1, b1 = parse(color)
            r2, g2, b2 = parse(bg)
            r = int(r1 * alpha + r2 * (1 - alpha))
            g = int(g1 * alpha + g2 * (1 - alpha))
            b = int(b1 * alpha + b2 * (1 - alpha))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return color

    def _spawn_ring(self):
        self._rings.append({"r": self.r * 0.55, "a": 1.0})

    def _animate(self):
        self.delete("all")
        cx, cy, r = self.cx, self.cy, self.r
        s = self._state

        # ── Pulse ──
        speed = {"idle": 0.008, "listening": 0.05,
                 "thinking": 0.025, "speaking": 0.035}[s]
        self._pulse += speed
        pulse = (math.sin(self._pulse) + 1) / 2   # 0..1

        # ── Rotationsgeschwindigkeit ──
        rot = {"idle": 0.3, "listening": 1.8,
               "thinking": 2.5, "speaking": 1.2}[s]
        self._angle += rot

        # ── Farben nach Zustand ──
        colors = {
            "idle":      ("#00c8ff", "#004466", "#002233"),
            "listening": ("#00ffaa", "#005533", "#002211"),
            "thinking":  ("#aa88ff", "#441166", "#220033"),
            "speaking":  ("#ffcc44", "#664400", "#331e00"),
        }[s]
        c_main, c_mid, c_dark = colors

        # ── Äußere Pulsringe (kein RGBA – Farbe wird mit Hintergrund gemischt) ──
        for ring in list(self._rings):
            ring["r"] += 1.4
            ring["a"] -= 0.025
            if ring["a"] <= 0:
                self._rings.remove(ring)
                continue
            rr = ring["r"]
            ring_color = self._blend(c_main, ring["a"] * 0.55)
            self.create_oval(
                cx - rr, cy - rr, cx + rr, cy + rr,
                outline=ring_color, width=1
            )

        # ── Äußerer Rotationsring (3 Segmente) ──
        for i, seg_len in enumerate([100, 60, 30]):
            start = self._angle + i * 120
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start, extent=seg_len,
                outline=c_main if i == 0 else c_mid,
                width=2 if i == 0 else 1,
                style="arc"
            )

        # ── Tick-Markierungen ──
        for deg in range(0, 360, 30):
            rad  = math.radians(deg + self._angle * 0.15)
            long = deg % 90 == 0
            r1   = r - (6 if long else 3)
            r2   = r + (3 if long else 1)
            x1, y1 = cx + r1 * math.cos(rad), cy + r1 * math.sin(rad)
            x2, y2 = cx + r2 * math.cos(rad), cy + r2 * math.sin(rad)
            self.create_line(x1, y1, x2, y2,
                             fill=c_mid if long else self._dim_color(c_mid),
                             width=1)

        # ── Mittelkreis-Hintergrund ──
        ri = r * 0.5
        self.create_oval(
            cx - ri, cy - ri, cx + ri, cy + ri,
            fill=c_dark, outline=c_mid, width=1
        )

        # ── Welle-Balken (nur beim Sprechen/Hören) ──
        if s in ("listening", "speaking"):
            n = len(self._bars)
            for i, val in enumerate(self._bars):
                target = 0.15 + 0.7 * abs(math.sin(
                    self._pulse * (2 + i * 0.4) + i
                )) if s == "speaking" else (
                    0.1 + 0.6 * abs(math.sin(self._pulse * 3 + i * 0.5))
                )
                self._bars[i] += (target - val) * 0.25
                val = self._bars[i]

                angle_rad = math.radians(i / n * 360)
                bar_len   = ri * 0.35 + ri * 0.45 * val
                x1 = cx + (ri * 0.2) * math.cos(angle_rad)
                y1 = cy + (ri * 0.2) * math.sin(angle_rad)
                x2 = cx + bar_len * math.cos(angle_rad)
                y2 = cy + bar_len * math.sin(angle_rad)
                self.create_line(x1, y1, x2, y2,
                                 fill=c_main, width=1)
        else:
            self._bars = [0.0] * len(self._bars)

        # ── Zweiter Innenring (gestrichelt via create_arc statt create_oval) ──
        ri2 = r * 0.62
        self.create_arc(
            cx - ri2, cy - ri2, cx + ri2, cy + ri2,
            start=0, extent=359,
            outline=c_mid, width=1,
            style="arc", dash=(4, 8)
        )

        # ── Zustandstext ──
        labels = {
            "idle":      ("JARVIS", C["accent"]),
            "listening": ("HÖRE", C["ok"]),
            "thinking":  ("DENKT", "#aa88ff"),
            "speaking":  ("SPRICHT", C["warn"]),
        }
        label, lcolor = labels[s]
        self.create_text(cx, cy - 6, text=label,
                         fill=lcolor,
                         font=("Consolas", 9, "bold"))

        # ── Hilfstext (Version) ──
        self.create_text(cx, cy + 7, text="v4.1",
                         fill=self._dim_color(lcolor),
                         font=("Consolas", 7))

        self.after(32, self._animate)   # ~30 FPS

    @staticmethod
    def _dim_color(hex_color: str) -> str:
        """Gibt eine abgedunkelte Version einer Hex-Farbe zurück."""
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"#{r//3:02x}{g//3:02x}{b//3:02x}"
        except Exception:
            return "#333333"


# ================================================================
#  NACHRICHTENBLASE
# ================================================================

class Bubble(ctk.CTkFrame):
    """Einzelne Chat-Nachricht."""

    def __init__(self, master, text: str, role: str,
                 action: dict | None = None, result: str | None = None,
                 **kw):
        bg = C["user_bg"] if role == "user" else C["bot_bg"]
        super().__init__(master, fg_color=bg, corner_radius=10, **kw)

        # Name-Chip
        name   = f"  {USERNAME}" if role == "user" else "  JARVIS"
        ncolor = C["text"]       if role == "user" else C["accent"]
        ctk.CTkLabel(
            self, text=name,
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=ncolor, anchor="w"
        ).pack(fill="x", padx=10, pady=(8, 1))

        # Nachrichtentext
        ctk.CTkLabel(
            self, text=text,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=C["text"],
            wraplength=360, justify="left", anchor="w"
        ).pack(fill="x", padx=12, pady=(0, action and 0 or 8))

        # Aktions-Badge
        if action:
            act_name = action.get("action", "?")
            badge_frame = ctk.CTkFrame(self, fg_color="#00110a",
                                       corner_radius=6)
            badge_frame.pack(anchor="w", padx=10, pady=(3, 0))
            ctk.CTkLabel(
                badge_frame, text=f" ⚡ {act_name} ",
                font=ctk.CTkFont("Consolas", 10),
                text_color=C["ok"]
            ).pack(padx=4, pady=2)

        # Ergebnis
        if result:
            short = result[:120] + ("…" if len(result) > 120 else "")
            ctk.CTkLabel(
                self, text=short,
                font=ctk.CTkFont("Consolas", 10),
                text_color=C["text_dim"],
                wraplength=360, justify="left", anchor="w"
            ).pack(fill="x", padx=12, pady=(2, 8))
        elif action:
            self.pack_configure()
            ctk.CTkFrame(self, height=6, fg_color="transparent").pack()


# ================================================================
#  AKTIONS-EINTRAG (linke Sidebar)
# ================================================================

class ActionEntry(ctk.CTkFrame):
    def __init__(self, master, action_name: str, result: str = "", **kw):
        super().__init__(master, fg_color=C["card"],
                         corner_radius=6, **kw)
        ts = time.strftime("%H:%M:%S")
        ctk.CTkLabel(
            self,
            text=f"⚡ {action_name}",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=C["ok"], anchor="w"
        ).pack(fill="x", padx=8, pady=(5, 1))
        if result:
            short = result[:55] + ("…" if len(result) > 55 else "")
            ctk.CTkLabel(
                self, text=f"  {short}",
                font=ctk.CTkFont("Consolas", 9),
                text_color=C["text_dim"], anchor="w",
                wraplength=190
            ).pack(fill="x", padx=8, pady=(0, 1))
        ctk.CTkLabel(
            self, text=f"  {ts}",
            font=ctk.CTkFont("Consolas", 8),
            text_color=C["dim"], anchor="w"
        ).pack(fill="x", padx=8, pady=(0, 4))


# ================================================================
#  HAUPT-APP
# ================================================================

class JarvisApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("JARVIS AI  ·  v4.1")
        self.geometry("1080x700")
        self.minsize(860, 580)
        self.configure(fg_color=C["bg"])

        self._q_ui:     queue.Queue = queue.Queue()
        self._q_status: queue.Queue = queue.Queue()

        self.speaker:  Speaker | None  = None
        self.listener: Listener | None = None
        self._running = False
        self._chat_row = 0
        self._action_row = 0

        self._build_layout()
        self._start_backend()
        self._poll()

    # ── Layout ──────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=258)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._build_header()
        self._build_left()
        self._build_chat()
        self._build_input()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["panel"],
                           corner_radius=0, height=50)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(2, weight=1)

        # Logo
        ctk.CTkLabel(
            hdr, text="◈  JARVIS AI",
            font=ctk.CTkFont("Consolas", 15, "bold"),
            text_color=C["accent"]
        ).grid(row=0, column=0, padx=18, pady=13)

        # Trennlinie (Canvas)
        sep = tk.Canvas(hdr, width=1, height=26,
                        bg=C["border"], highlightthickness=0)
        sep.grid(row=0, column=1, padx=4)

        # Modell-Badge
        ctk.CTkLabel(
            hdr, text=f"  {OLLAMA_MODEL}",
            font=ctk.CTkFont("Consolas", 10),
            text_color=C["text_dim"]
        ).grid(row=0, column=2, padx=8, sticky="w")

        # Status-Label
        self._lbl_status = ctk.CTkLabel(
            hdr, text="● Initialisierung...",
            font=ctk.CTkFont("Consolas", 10),
            text_color=C["warn"]
        )
        self._lbl_status.grid(row=0, column=3, padx=18)

        # Schließen-Button
        ctk.CTkButton(
            hdr, text="✕", width=32, height=28,
            font=ctk.CTkFont("Consolas", 11),
            fg_color=C["panel"], hover_color="#2a0a0a",
            text_color=C["dim"], corner_radius=6,
            command=self._on_close
        ).grid(row=0, column=4, padx=(4, 12))

    def _build_left(self):
        left = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0)
        left.grid(row=1, column=0, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

        # Orb
        self.orb = JarvisOrb(left, size=210)
        self.orb.configure(bg=C["panel"])
        self.orb.grid(row=0, column=0, pady=(20, 6))

        # Mic-Button
        self._btn_mic = ctk.CTkButton(
            left, text="◉   AUFNEHMEN",
            font=ctk.CTkFont("Consolas", 11, "bold"),
            fg_color=C["accent2"], hover_color="#006688",
            text_color=C["accent"],
            corner_radius=22, height=42,
            command=self._manual_trigger
        )
        self._btn_mic.grid(row=1, column=0, padx=20, pady=6, sticky="ew")

        # Stopp-Button
        ctk.CTkButton(
            left, text="◼   STOPP",
            font=ctk.CTkFont("Consolas", 10),
            fg_color=C["card"], hover_color="#2a0808",
            text_color=C["err"],
            corner_radius=22, height=34,
            command=self._on_stop
        ).grid(row=2, column=0, padx=20, pady=(2, 8), sticky="ew")

        # Aktionen-Log
        ctk.CTkLabel(
            left, text="  LETZTE AKTIONEN",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=C["dim"], anchor="w"
        ).grid(row=3, column=0, padx=12, pady=(10, 2), sticky="w")

        self._action_frame = ctk.CTkScrollableFrame(
            left, fg_color=C["bg"], corner_radius=0,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent2"]
        )
        self._action_frame.grid(row=3, column=0, padx=6, pady=(0, 6),
                                sticky="nsew")
        self._action_frame.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

    def _build_chat(self):
        right = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Chat-Header
        chat_hdr = ctk.CTkFrame(right, fg_color=C["sep"],
                                corner_radius=0, height=30)
        chat_hdr.grid(row=0, column=0, sticky="ew")
        chat_hdr.grid_propagate(False)
        ctk.CTkLabel(
            chat_hdr, text="  KONVERSATION",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=C["dim"], anchor="w"
        ).pack(side="left", padx=12, pady=6)

        # Chat-Nachrichten
        self._chat = ctk.CTkScrollableFrame(
            right, fg_color=C["bg"], corner_radius=0,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent2"]
        )
        self._chat.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._chat.grid_columnconfigure(0, weight=1)

    def _build_input(self):
        bar = ctk.CTkFrame(self, fg_color=C["panel"],
                           corner_radius=0, height=56)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)

        self._entry = ctk.CTkEntry(
            bar,
            placeholder_text="Befehl tippen und Enter drücken...",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=C["bg"],
            border_color=C["border"],
            text_color=C["text"],
            placeholder_text_color=C["text_dim"],
            corner_radius=18, height=36
        )
        self._entry.grid(row=0, column=0, padx=(14, 8), pady=10, sticky="ew")
        self._entry.bind("<Return>", lambda _: self._on_send())

        ctk.CTkButton(
            bar, text="→", width=46, height=36,
            font=ctk.CTkFont("Consolas", 15, "bold"),
            fg_color=C["accent2"], hover_color="#007a99",
            text_color=C["accent"], corner_radius=18,
            command=self._on_send
        ).grid(row=0, column=1, padx=(0, 14), pady=10)

    # ── Backend ─────────────────────────────────────────────

    def _start_backend(self):
        self._running = True
        threading.Thread(target=self._backend_loop, daemon=True).start()

    def _backend_loop(self):
        try:
            self._status("Prüfe Modell...", "warn")
            err = check_model_available()
            if err:
                self._status(f"⚠  {err[:50]}", "err")
                self._log("Fehler", err)
                # Trotzdem weitermachen – Text-Eingabe funktioniert noch

            # ── TTS laden ──────────────────────────────────────
            self._status("Lade TTS...", "warn")
            try:
                self.speaker = Speaker()
                automation.set_speak_callback(self.speaker.say)
            except Exception as e_tts:
                print(f"  [GUI] TTS nicht geladen: {e_tts}")
                self._status(f"⚠  TTS-Fehler: {e_tts}", "warn")
                self.speaker = None

            # ── STT laden (optional – bei Fehler: nur Texteingabe) ──
            self._status("Lade STT / VAD-Modell...", "warn")
            stt_ok = False
            try:
                self.listener = Listener()
                stt_ok = True
            except ModuleNotFoundError as e_mod:
                pkg = str(e_mod).replace("No module named ", "").strip("'")
                msg = (f"Spracheingabe deaktiviert – fehlendes Paket: {pkg}\n"
                       f"Bitte installieren: pip install {pkg}")
                print(f"  [GUI] {msg}")
                self._status(f"⚠  pip install {pkg}", "err")
                self._q_ui.put(("bot_msg",
                                f"⚠  Mikrofon nicht verfügbar.\n"
                                f"Fehlendes Paket: {pkg}\n"
                                f"Fix: pip install {pkg}\n\n"
                                f"Die Texteingabe unten funktioniert trotzdem!",
                                None, None))
                self.listener = None
            except Exception as e_stt:
                print(f"  [GUI] STT nicht geladen: {e_stt}")
                self._status(f"⚠  STT-Fehler (Texteingabe OK)", "warn")
                self._q_ui.put(("bot_msg",
                                f"⚠  Mikrofon nicht geladen: {e_stt}\n"
                                f"Texteingabe funktioniert.",
                                None, None))
                self.listener = None

            # ── Begrüßung ──────────────────────────────────────
            mode = "Sag 'Jarvis' oder tippe" if stt_ok else "Tippe einen Befehl"
            self._status(f"● Bereit  –  {mode}", "ok")
            if stt_ok:
                self._q_ui.put(("bot_msg",
                                f"Hallo {USERNAME}! Ich bin bereit.\n"
                                "Sag 'Jarvis' oder tippe einen Befehl.",
                                None, None))

            # ── Hauptschleife (nur wenn STT verfügbar) ─────────
            if not stt_ok:
                return   # Texteingabe läuft über _process_inline

            while self._running:
                self.orb.set_state("idle")
                self._put_btn_state("idle")
                self.listener.listen_for_wake_word()

                if not self._running:
                    break

                self._status("● Höre zu...", "ok")
                self.orb.set_state("listening")
                self._put_btn_state("listening")
                if self.speaker:
                    self.speaker.say("Ja?")

                cmd = self.listener.listen_command()
                if cmd:
                    self._do_process(cmd)

        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._status(f"⚠  {exc}", "err")

    def _do_process(self, command: str):
        """Befehl verarbeiten (im Backend-Thread)."""
        self.orb.set_state("thinking")
        self._status("● Denkt nach...", "warn")
        automation.update_activity()

        self._q_ui.put(("user_msg", command))

        speak, action = ask_llm(command)
        result = None

        if action:
            result = execute_action(action)

        self._q_ui.put(("bot_msg", speak, action, result))

        if speak and self.speaker:
            self.orb.set_state("speaking")
            self._put_btn_state("speaking")
            reset_stop_event()
            self.speaker.say(speak)

        if result and self.speaker:
            result_str = str(result)
            if len(result_str) < 400:
                self.orb.set_state("speaking")
                self.speaker.say(result_str)

        self._status("● Bereit  –  sag 'Jarvis'", "ok")

    def _process_inline(self, command: str):
        """Inline-Befehl (Texteingabe) im eigenen Thread."""
        threading.Thread(
            target=self._do_process, args=(command,), daemon=True
        ).start()

    # ── Queue-Helpers ────────────────────────────────────────

    def _status(self, text: str, level: str = "ok"):
        self._q_status.put(("status", text, level))

    def _log(self, action_name: str, result: str = ""):
        self._q_status.put(("log", action_name, result))

    def _add_bubble(self, role, text, action, result):
        self._q_ui.put(("bot_msg" if role != "user" else "user_msg",
                        text, action, result) if role != "user"
                       else ("user_msg", text))

    def _put_btn_state(self, state: str):
        self._q_status.put(("btn", state))

    # ── Queue-Polling ────────────────────────────────────────

    def _poll(self):
        # Status
        try:
            while True:
                msg = self._q_status.get_nowait()
                kind = msg[0]
                if kind == "status":
                    _, text, level = msg
                    col = {"ok": C["ok"], "warn": C["warn"],
                           "err": C["err"]}.get(level, C["text"])
                    self._lbl_status.configure(text=text, text_color=col)
                elif kind == "log":
                    _, aname, ares = msg
                    self._add_action_entry(aname, ares)
                elif kind == "btn":
                    self._update_mic_btn(msg[1])
        except queue.Empty:
            pass

        # UI-Nachrichten
        try:
            while True:
                item = self._q_ui.get_nowait()
                if item[0] == "user_msg":
                    self._render_bubble("user", item[1], None, None)
                else:
                    _, speak, action, result = item
                    self._render_bubble("bot", speak or "…", action, result)
                    if action:
                        aname = action.get("action", "?")
                        self._add_action_entry(aname, str(result or ""))
        except queue.Empty:
            pass

        self.after(40, self._poll)

    # ── UI-Updates ───────────────────────────────────────────

    def _render_bubble(self, role, text, action, result):
        pad_l = 6 if role == "bot" else 50
        pad_r = 50 if role == "bot" else 6
        b = Bubble(self._chat, text,
                   "user" if role == "user" else "jarvis",
                   action, str(result) if result else None)
        b.grid(row=self._chat_row, column=0,
               padx=(pad_l, pad_r), pady=3, sticky="ew")
        self._chat_row += 1
        self._chat._parent_canvas.yview_moveto(1.0)

    def _add_action_entry(self, name: str, result: str = ""):
        e = ActionEntry(self._action_frame, name, result)
        e.grid(row=self._action_row, column=0,
               padx=4, pady=2, sticky="ew")
        self._action_row += 1
        self._action_frame._parent_canvas.yview_moveto(1.0)

    def _update_mic_btn(self, state: str):
        cfg = {
            "idle":      ("◉   AUFNEHMEN",  C["accent2"], C["accent"]),
            "listening": ("◉   HÖRE ZU…",   "#004433",    C["ok"]),
            "thinking":  ("◉   DENKT…",     "#330044",    "#aa88ff"),
            "speaking":  ("◉   SPRICHT…",   "#332200",    C["warn"]),
        }.get(state, ("◉   AUFNEHMEN", C["accent2"], C["accent"]))
        self._btn_mic.configure(
            text=cfg[0], fg_color=cfg[1], text_color=cfg[2]
        )

    # ── Events ───────────────────────────────────────────────

    def _manual_trigger(self):
        """Manuell Aufnahme starten (überspringt Wake-Word)."""
        if not self.listener:
            return
        def _listen():
            self.orb.set_state("listening")
            self._put_btn_state("listening")
            self._status("● Höre zu...", "ok")
            cmd = self.listener.listen_command()
            if cmd:
                self._do_process(cmd)
            else:
                self.orb.set_state("idle")
                self._put_btn_state("idle")
                self._status("● Bereit  –  sag 'Jarvis'", "ok")
        threading.Thread(target=_listen, daemon=True).start()

    def _on_stop(self):
        if self.speaker:
            self.speaker.stop()
        self.orb.set_state("idle")

    def _on_send(self):
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        self._q_ui.put(("user_msg", text))
        self._process_inline(text)

    def _on_close(self):
        self._running = False
        if self.speaker:
            self.speaker.stop()
        self.after(100, self.destroy)


# ================================================================
#  ENTRY POINT
# ================================================================

if __name__ == "__main__":
    # Prüfen ob customtkinter installiert ist
    try:
        import customtkinter  # noqa
    except ImportError:
        print("\n  Bitte customtkinter installieren:")
        print("  pip install customtkinter\n")
        sys.exit(1)

    app = JarvisApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
