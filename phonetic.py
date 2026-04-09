"""
Phonetik-Korrekturen fuer den deutschen TTS (englische Woerter korrekt aussprechen).
"""
import re

PHONETIC = [
    # Name
    (r"\bJarvis\b",         "Dscharwiss"),
    (r"\bRobin\b",          "Robbinn"),
    # Browser & Co
    (r"\bBrave\b",          "Brejw"),
    (r"\bChrome\b",         "Krohm"),
    (r"\bFirefox\b",        "Feier-Focks"),
    (r"\bEdge\b",           "Etsch"),
    # Social / Messaging
    (r"\bSpotify\b",        "Spotti-Fei"),
    (r"\bYouTube\b",        "Juh-Tjuub"),
    (r"\bDiscord\b",        "Diss-Kohrd"),
    (r"\bSteam\b",          "Stiem"),
    (r"\bNetflix\b",        "Nett-Flicks"),
    (r"\bWhatsApp\b",       "Wotts-Epp"),
    (r"\bInstagram\b",      "Insta-Gramm"),
    (r"\bTikTok\b",         "Tick-Tock"),
    (r"\bTwitter\b",        "Twitt-er"),
    (r"\bFacebook\b",       "Fejss-Buck"),
    (r"\bTwitch\b",         "Twitsch"),
    (r"\bReddit\b",         "Reddit"),
    (r"\bLinkedIn\b",       "Linkt-Inn"),
    (r"\bSlack\b",          "Slaeck"),
    (r"\bZoom\b",           "Suhm"),
    (r"\bSkype\b",          "Skeip"),
    (r"\bTelegram\b",       "Tele-Gramm"),
    # Big Tech
    (r"\bMicrosoft\b",      "Meikro-Soft"),
    (r"\bWindows\b",        "Winndoos"),
    (r"\bGoogle\b",         "Guhgel"),
    (r"\bAmazon\b",         "Amason"),
    (r"\bApple\b",          "Eppel"),
    (r"\bNvidia\b",         "Enn-Widia"),
    # Office
    (r"\bOutlook\b",        "Aut-Luck"),
    (r"\bTeams\b",          "Tiems"),
    (r"\bOneDrive\b",       "Wann-Dreif"),
    (r"\bPowerPoint\b",     "Pauer-Point"),
    (r"\bExcel\b",          "Eck-Sell"),
    (r"\bWord\b",           "Wörd"),
    (r"\bOffice\b",         "Offiss"),
    # Dev
    (r"\bVSCode\b",         "Wie-Ess-Kohd"),
    (r"\bVS Code\b",        "Wie-Ess-Kohd"),
    (r"\bGitHub\b",         "Gitt-Habb"),
    (r"\bCopilot\b",        "Ko-Peilot"),
    (r"\bChatGPT\b",        "Tschaet Geh-Peh-Teh"),
    (r"\bOpenAI\b",         "Ohpen Ej-Ei"),
    (r"\bClaude\b",         "Klohd"),
    # Sonstiges
    (r"\bPayPal\b",         "Pej-Pael"),
    (r"\beBay\b",           "Ie-Bej"),
    (r"\bDropbox\b",        "Dropp-Bocks"),
    (r"\bBlender\b",        "Blenn-der"),
    # Abkuerzungen
    (r"\bPC\b",             "Peh Zeh"),
    (r"\bAI\b",             "Ej Ei"),
    (r"\bAPI\b",            "Ah Peh Ih"),
    (r"\bCPU\b",            "Zeh Peh Uh"),
    (r"\bGPU\b",            "Geh Peh Uh"),
    (r"\bRAM\b",            "Raemm"),
    (r"\bSSD\b",            "Ess Ess Deh"),
    (r"\bUSB\b",            "Uh Ess Beh"),
    (r"\bHDMI\b",           "Ha Deh Emm Ih"),
    (r"\bWLAN\b",           "Weh-Lann"),
    (r"\bWiFi\b",           "Wai-Fai"),
    (r"\bURL\b",            "Uh Err Ell"),
    (r"\bOK\b",             "Okej"),
    (r"\bScreenshot\b",     "Skrienschott"),
    (r"\bDownload\b",       "Daun-Lohd"),
    (r"\bUpload\b",         "App-Lohd"),
    (r"\bUpdate\b",         "App-Dejt"),
    (r"\bBug\b",            "Bagg"),
    (r"\bFile\b",           "Feil"),
    (r"\bFolder\b",         "Fohl-der"),
    (r"\bDesktop\b",        "Desk-Topp"),
    (r"\bBrowser\b",        "Brauser"),
    (r"\bStreaming\b",      "Strieming"),
    (r"\bPodcast\b",        "Podd-Kaest"),
    (r"\bPlaylist\b",       "Plej-List"),
    (r"\bAccount\b",        "Eh-Kaunt"),
    (r"\bPassword\b",       "Pass-Wörd"),
    (r"\bLogin\b",          "Logg-Inn"),
    (r"\bLogout\b",         "Logg-Aut"),
    (r"\bCloud\b",          "Klaud"),
    (r"\bServer\b",         "Sörwer"),
]


def phonetic_fix(text):
    """Ersetzt englische Begriffe durch phonetisch korrekte deutsche Aussprache."""
    for pat, repl in PHONETIC:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text
