"""
Wetter-Funktionen fuer Jarvis (open-meteo / wttr.in - kostenlos, kein API-Key).
"""
import json
import datetime
import urllib.request
import urllib.parse


WMO_WEATHER = {
    0: "klarer Himmel", 1: "ueberwiegend klar", 2: "teilweise bewoelkt",
    3: "bedeckt", 45: "neblig", 48: "Reifnebel",
    51: "leichter Nieselregen", 53: "Nieselregen", 55: "starker Nieselregen",
    61: "leichter Regen", 63: "Regen", 65: "starker Regen",
    71: "leichter Schneefall", 73: "Schneefall", 75: "starker Schneefall",
    80: "leichte Regenschauer", 81: "Regenschauer", 82: "starke Regenschauer",
    95: "Gewitter", 96: "Gewitter mit Hagel", 99: "schweres Gewitter mit Hagel",
}


def _fetch_weather(lat, lon, city_name):
    """Holt Wetterdaten fuer gegebene Koordinaten (open-meteo)."""
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,apparent_temperature,weather_code,"
        f"relative_humidity_2m,wind_speed_10m"
        f"&timezone=auto"
    )
    w = json.loads(urllib.request.urlopen(weather_url, timeout=8).read())
    c = w["current"]
    desc = WMO_WEATHER.get(c["weather_code"], "unbekannt")
    return (
        f"In {city_name}: {desc}, {c['temperature_2m']:.0f} Grad, "
        f"gefuehlt {c['apparent_temperature']:.0f} Grad, "
        f"Luftfeuchtigkeit {c['relative_humidity_2m']} Prozent, "
        f"Wind {c['wind_speed_10m']:.0f} Stundenkilometer."
    )


def get_weather(city):
    """Gibt aktuelles Wetter + Tageshoechstwert + Regenprognose zurueck."""
    if not city:
        return "Fuer welche Stadt soll ich das Wetter suchen?"

    try:
        city_safe = urllib.parse.quote(city)
        url = f"https://wttr.in/{city_safe}?format=j1&lang=de"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Aktuelles Wetter
        current = data["current_condition"][0]
        temp    = current["temp_C"]
        desc    = current["lang_de"][0]["value"] if "lang_de" in current else "unbekannt"

        # Tages-Hoechstwert
        today = data["weather"][0]
        max_t = today["maxtempC"]

        # Regen-Check fuer den Rest des Tages
        now_hour  = datetime.datetime.now().hour
        rain_info = "Es soll heute trocken bleiben."
        for h in today["hourly"]:
            hour   = int(h["time"]) // 100
            if hour > now_hour:
                chance = int(h["chanceofrain"])
                if chance > 50:
                    rain_info = (
                        f"Achtung, ab etwa {hour} Uhr wird es voraussichtlich regnen. "
                        f"Die Wahrscheinlichkeit liegt bei {chance} Prozent."
                    )
                    break

        ans  = f"In {city} haben wir aktuell {temp} Grad Celsius, das Wetter ist {desc.lower()}. "
        ans += f"Die Hoechsttemperatur liegt heute bei {max_t} Grad. {rain_info}"
        return ans

    except Exception:
        return "Entschuldigung, ich konnte die detaillierten Wetterdaten gerade nicht abrufen."
