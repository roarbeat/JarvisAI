"""
System-Monitoring fuer Jarvis.
CPU, RAM, GPU, Speicher, Prozesse, Netzwerk, Windows-Updates.
"""
import os
import subprocess
import time

import psutil


# ============================================================
#  CPU / RAM / GPU
# ============================================================

def get_system_stats(detail="all"):
    """CPU, RAM und GPU-Auslastung auslesen."""
    parts = []
    detail = detail.lower()

    try:
        if detail in ("all", "cpu"):
            cpu    = psutil.cpu_percent(interval=1)
            cores  = psutil.cpu_count(logical=False)
            lcores = psutil.cpu_count(logical=True)
            parts.append(f"CPU: {cpu:.0f}% ({cores} Kerne / {lcores} logisch)")
    except Exception:
        pass

    try:
        if detail in ("all", "ram", "speicher"):
            vm = psutil.virtual_memory()
            parts.append(
                f"RAM: {vm.percent:.0f}% belegt "
                f"({vm.used / 1e9:.1f} GB von {vm.total / 1e9:.1f} GB)"
            )
    except Exception:
        pass

    try:
        if detail in ("all", "gpu"):
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                for gpu in gpus[:2]:
                    parts.append(
                        f"GPU '{gpu.name}': {gpu.load * 100:.0f}% Auslastung, "
                        f"{gpu.memoryUsed:.0f}/{gpu.memoryTotal:.0f} MB VRAM, "
                        f"{gpu.temperature:.0f}°C"
                    )
            else:
                # WMI Fallback
                r = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_VideoController | "
                     "Select-Object -ExpandProperty Name | Select-Object -First 2"],
                    capture_output=True, text=True, timeout=5
                )
                if r.stdout.strip():
                    parts.append(f"GPU: {r.stdout.strip().splitlines()[0]}")
    except ImportError:
        try:
            r = subprocess.run(
                ["powershell", "-Command",
                 "(Get-Counter '\\GPU Engine(*engtype_3D)\\Utilization Percentage').CounterSamples.CookedValue "
                 "| Measure-Object -Sum | Select-Object -ExpandProperty Sum"],
                capture_output=True, text=True, timeout=5
            )
            val = r.stdout.strip()
            if val:
                parts.append(f"GPU-Auslastung: ca. {float(val):.0f}%")
        except Exception:
            pass
    except Exception:
        pass

    return " | ".join(parts) if parts else "System-Daten konnten nicht gelesen werden."


def get_cpu():
    return get_system_stats("cpu")


def get_ram():
    return get_system_stats("ram")


def get_gpu():
    return get_system_stats("gpu")


# ============================================================
#  FESTPLATTEN-SPEICHER
# ============================================================

def get_disk_space(drive=None):
    """Freien Speicherplatz auf Laufwerken abfragen."""
    try:
        if drive:
            # Bestimmtes Laufwerk
            drives = [drive.upper().rstrip("\\") + "\\"]
        else:
            drives = [p.mountpoint for p in psutil.disk_partitions(all=False)
                      if p.fstype and os.path.exists(p.mountpoint)]

        parts = []
        for d in drives[:5]:
            try:
                usage = psutil.disk_usage(d)
                parts.append(
                    f"{d}: {usage.free / 1e9:.1f} GB frei / "
                    f"{usage.total / 1e9:.1f} GB gesamt ({usage.percent:.0f}% belegt)"
                )
            except Exception:
                pass
        return " | ".join(parts) if parts else "Keine Laufwerke gefunden."
    except Exception as e:
        return f"Fehler beim Speicher-Check: {e}"


# ============================================================
#  PROZESSE
# ============================================================

def list_processes(top=10, sort_by="cpu"):
    """Die ressourcenintensivsten Prozesse auflisten."""
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except Exception:
                pass

        sort_key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
        procs.sort(key=lambda x: x.get(sort_key, 0) or 0, reverse=True)
        top_procs = procs[:top]
        lines = [
            f"{p['name']} (PID {p['pid']}): CPU {p.get('cpu_percent', 0):.1f}%, "
            f"RAM {p.get('memory_percent', 0):.1f}%"
            for p in top_procs
        ]
        return "Top-Prozesse: " + " | ".join(lines[:5])
    except Exception as e:
        return f"Fehler: {e}"


def kill_process(name_or_pid):
    """Prozess beenden."""
    try:
        killed = []
        if str(name_or_pid).isdigit():
            p = psutil.Process(int(name_or_pid))
            p.terminate()
            killed.append(str(name_or_pid))
        else:
            for p in psutil.process_iter(["pid", "name"]):
                if name_or_pid.lower() in p.info["name"].lower():
                    p.terminate()
                    killed.append(p.info["name"])

        if killed:
            return f"Beendet: {', '.join(killed)}"
        return f"Prozess '{name_or_pid}' nicht gefunden."
    except Exception as e:
        return f"Fehler beim Beenden: {e}"


def find_process(name):
    """Prueft ob ein Prozess laeuft."""
    try:
        for p in psutil.process_iter(["name"]):
            if name.lower() in p.info["name"].lower():
                return f"'{name}' laeuft (PID {p.pid})."
        return f"'{name}' laeuft nicht."
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================
#  NETZWERKGESCHWINDIGKEIT
# ============================================================

def get_network_speed():
    """Netzwerk-Traffic messen (Bytes/s ueber 1 Sekunde)."""
    try:
        before = psutil.net_io_counters()
        time.sleep(1)
        after  = psutil.net_io_counters()

        recv_s = (after.bytes_recv - before.bytes_recv) / 1024  # KB/s
        sent_s = (after.bytes_sent - before.bytes_sent) / 1024  # KB/s

        def fmt(kbs):
            if kbs >= 1024:
                return f"{kbs / 1024:.1f} MB/s"
            return f"{kbs:.0f} KB/s"

        return f"Download: {fmt(recv_s)} | Upload: {fmt(sent_s)}"
    except Exception as e:
        return f"Netzwerk-Fehler: {e}"


def ping(host="8.8.8.8"):
    """Ping zu einem Host."""
    try:
        r = subprocess.run(
            ["ping", "-n", "3", host],
            capture_output=True, text=True, timeout=10
        )
        lines = r.stdout.splitlines()
        # Letzte Zeile mit Durchschnitt
        for line in reversed(lines):
            if "durchschn" in line.lower() or "avg" in line.lower() or "average" in line.lower():
                return f"Ping zu {host}: {line.strip()}"
        return f"Ping zu {host}: {'Erfolgreich' if r.returncode == 0 else 'Fehlgeschlagen'}"
    except Exception as e:
        return f"Ping-Fehler: {e}"


def get_network_info():
    """IP-Adresse und Verbindungsinfos."""
    try:
        addrs = psutil.net_if_addrs()
        parts = []
        for iface, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family.name == "AF_INET" and not addr.address.startswith("127."):
                    parts.append(f"{iface}: {addr.address}")
        return "Netzwerk: " + " | ".join(parts[:3]) if parts else "Keine Netzwerkverbindung."
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================
#  WINDOWS-UPDATES
# ============================================================

def check_windows_updates():
    """Windows-Updates pruefen und ggf. starten."""
    try:
        os.startfile("ms-settings:windowsupdate")
        # Im Hintergrund pruefen (powershell)
        subprocess.Popen(
            ["powershell", "-Command",
             "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher()"
             ".Search('IsInstalled=0').Updates.Count"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return "Windows-Update-Einstellungen geoeffnet."
    except Exception as e:
        return f"Update-Fehler: {e}"


def trigger_windows_update():
    """Windows-Updates im Hintergrund starten."""
    try:
        script = (
            "Install-Module PSWindowsUpdate -Force -Scope CurrentUser; "
            "Get-WindowsUpdate -AcceptAll -AutoReboot"
        )
        subprocess.Popen(
            ["powershell", "-Command", script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return "Windows-Update-Prozess gestartet (laeuft im Hintergrund)."
    except Exception as e:
        return f"Update-Fehler: {e}"


# ============================================================
#  SYSTEM-ZUSAMMENFASSUNG
# ============================================================

def system_summary():
    """Kurze Systemzusammenfassung (CPU + RAM + Festplatte)."""
    cpu  = psutil.cpu_percent(interval=0.5)
    vm   = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\") if os.path.exists("C:\\") else None

    parts = [f"CPU: {cpu:.0f}%", f"RAM: {vm.percent:.0f}%"]
    if disk:
        parts.append(f"C: {disk.percent:.0f}% voll")
    return " | ".join(parts)
