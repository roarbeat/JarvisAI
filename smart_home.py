"""
Home-Assistant-Integration fuer Jarvis (Smart-Home-Steuerung).
"""
import json
import urllib.request

from config import HA_URL, HA_TOKEN


def control_smart_home(device_name, action_state):
    """Schaltet ein Smart-Home-Geraet ueber Home Assistant ein oder aus."""
    if not HA_TOKEN or "DEIN_KOPIERTER_TOKEN" in HA_TOKEN:
        return "Bitte trage zuerst den Home Assistant Token im Code ein."

    try:
        req = urllib.request.Request(
            f"{HA_URL}/api/states",
            headers={"Authorization": f"Bearer {HA_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            states = json.loads(response.read().decode("utf-8"))

        entity_id = None
        domain     = None

        such_begriff = device_name.lower()

        # Menschliche Sprache -> HA-Begriffe
        such_begriff = such_begriff.replace("heizung", "thermostat")

        # Umlaute glaettbuegeln – echte Umlaute zuerst, dann Digraphen
        umlaute = [("ä","a"), ("ö","o"), ("ü","u"), ("ß","ss"), ("ae","a"), ("oe","o"), ("ue","u")]
        for a, b in umlaute:
            such_begriff = such_begriff.replace(a, b)

        # Zusammengeschriebene Woerter trennen
        if "licht" in such_begriff and such_begriff != "licht":
            such_begriff = such_begriff.replace("licht", " licht ")
        if "lampe" in such_begriff and such_begriff != "lampe":
            such_begriff = such_begriff.replace("lampe", " lampe ")

        search_words = such_begriff.split()
        print(f"  [Smart Home] Jarvis sucht nach: {search_words}")

        # Gefaehrliche Unter-Schalter ausschliessen
        exclude_words = [
            "child lock", "window detection", "boost", "ueberblenden",
            "loudness", "statusleuchte", "crossfade", "permit join"
        ]

        entity_current_state = None
        for state in states:
            f_name = state.get("attributes", {}).get("friendly_name", "").lower()
            e_id   = state.get("entity_id", "").lower()

            if any(ex in f_name or ex in e_id for ex in exclude_words):
                continue

            f_clean = f_name
            e_clean = e_id
            for a, b in umlaute:
                f_clean = f_clean.replace(a, b)
                e_clean = e_clean.replace(a, b)

            if all(word in f_clean or word in e_clean for word in search_words):
                dom = e_id.split(".")[0]
                if dom in ["light", "switch", "media_player", "climate", "scene"]:
                    entity_id            = e_id
                    domain               = dom
                    entity_current_state = state.get("state", "")
                    print(f"  [Smart Home] TREFFER! Geraet gefunden: {f_name} ({e_id}) [Status: {entity_current_state}]")
                    break

        if not entity_id:
            return "Ich konnte im Home Assistant kein passendes Geraet finden."

        if entity_current_state == "unavailable":
            return "Das Geraet ist gerade nicht erreichbar (unavailable). Bitte pruefe die Verbindung in Home Assistant."

        # Befehl senden
        service = "turn_on" if action_state == "on" else "turn_off"

        if domain == "climate":
            service = "set_hvac_mode"
            data = json.dumps({
                "entity_id": entity_id,
                "hvac_mode": "heat" if action_state == "on" else "off"
            }).encode("utf-8")
        else:
            data = json.dumps({"entity_id": entity_id}).encode("utf-8")

        api_url  = f"{HA_URL}/api/services/{domain}/{service}"
        post_req = urllib.request.Request(
            api_url, data=data,
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(post_req, timeout=5) as post_res:
            response_body = json.loads(post_res.read().decode("utf-8"))

        changed_entities = (
            [s.get("entity_id", "") for s in response_body]
            if isinstance(response_body, list) else []
        )
        if entity_id not in changed_entities:
            print("  [Smart Home] WARNUNG: HA hat den Befehl akzeptiert, aber der Zustand hat sich nicht geaendert!")
            return "Befehl gesendet, aber das Geraet hat nicht reagiert. Moeglicherweise ist es offline oder ausser Reichweite."

        return "Erledigt."

    except Exception as e:
        return f"Fehler bei Home Assistant: {e}"
