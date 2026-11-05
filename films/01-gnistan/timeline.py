"""Gemensam tidslinje för bild och ljud – allt synkas härifrån.

Film 01: "GNISTAN" – AI:s evolution från GPT-1 till ASI.
Format inspirerat av evolutionsräknaren i Fatboy Slims "Right Here, Right Now"-video:
en enda obruten resa, ett årtal som tickar i hörnet, och en klimax i "nuet".
"""
import bisect

DURATION = 58.0
FPS = 30

# (namn, start, slut)
SCENES = [
    ("hook",    0.0,  3.0),
    ("gpt1",    3.0,  9.0),
    ("gpt2",    9.0, 14.0),
    ("gpt3",   14.0, 19.0),
    ("chatgpt", 19.0, 25.0),
    ("gpt4",   25.0, 30.0),
    ("reason", 30.0, 35.0),
    ("agents", 35.0, 39.5),
    ("now",    39.5, 42.0),
    ("agi",    42.0, 47.5),
    ("asi",    47.5, 52.0),
    ("outro",  52.0, DURATION),
]

# HUD – "räknaren" i hörnet. (år, modell, faktarad)
HUD = {
    "gpt1":    ("2018", "GPT-1",   "117 MILJONER PARAMETRAR"),
    "gpt2":    ("2019", "GPT-2",   "1,5 MILJARDER PARAMETRAR"),
    "gpt3":    ("2020", "GPT-3",   "175 MILJARDER PARAMETRAR"),
    "chatgpt": ("2022", "CHATGPT", "100 MILJONER ANVÄNDARE / 2 MÅN"),
    "gpt4":    ("2023", "GPT-4",   "SER. LÄSER. HÖR."),
    "reason":  ("2024", "RESONERANDE MODELLER", "TÄNKER INNAN DEN SVARAR"),
    "agents":  ("2025", "AGENTER", "AUTONOMA. DYGNET RUNT."),
    "agi":     ("20??", "AGI",     "ARTIFICIELL GENERELL INTELLIGENS"),
    "asi":     ("????", "ASI",     "ARTIFICIELL SUPERINTELLIGENS"),
}
AGENTS_2026_AT = 37.4  # årtalet slår om till 2026 mitt i agent-scenen

# Undertexter: (start, slut, text, stil)
CAPTIONS = [
    (3.5,  6.2,  "Det började med en gnista.", "cap"),
    (6.2,  8.8,  "Den kunde knappt skriva en mening.", "cap"),
    (9.4,  13.8, "”För farlig för att släppas.”", "cap"),
    (14.4, 18.8, "Sen lärde den sig låta som oss.", "cap"),
    (19.3, 21.6, "Vi släppte in den.", "cap"),
    (21.8, 24.8, "100 miljoner av oss.\nPå två månader.", "cap"),
    (25.4, 29.8, "Den lärde sig se.", "cap"),
    (30.4, 34.8, "Den lärde sig tänka efter.", "cap"),
    (35.4, 39.3, "Nu jobbar den. Utan oss.", "cap"),
    (42.4, 44.8, "Snart: lika smart som vi.", "cap"),
    (44.9, 47.4, "I allt.", "cap"),
    (47.8, 50.0, "Sen smartare än alla oss.", "cap"),
    (50.1, 51.9, "Tillsammans.", "cap"),
    (53.0, 57.6, "Vi är här. Just nu.", "cap"),
    (55.0, 57.6, "Frågan är vad vi gör\nmed tiden som är kvar.", "small"),
]

# Stora slag-texter
HOOK_LINES = [(0.15, "DET HÄR TOG"), (0.85, "8 ÅR.")]
NOW_LINES = [(39.5, "HÄR."), (40.3, "JUST NU.")]

# ChatGPT-terminalen: (start, slut, text)
TYPING = [
    (19.6, 20.9, "> hej. vem är du?"),
    (21.3, 23.1, "Jag är här för att hjälpa dig."),
]


def char_times():
    """Tidpunkter då varje tecken skrivs (används för tangentljud)."""
    out = []
    for s, e, txt in TYPING:
        n = len(txt)
        for i in range(n):
            if txt[i] != " ":
                out.append(s + (e - s) * i / n)
    return out


def _kicks():
    k = []
    # Hjärtslaget accelererar genom hela historien: 50 -> 150 BPM
    t = 3.0
    while t < 39.3:
        bpm = 50 * (150 / 50) ** ((t - 3.0) / 36.5)
        k.append((t, bpm))
        t += 60.0 / bpm
    # AGI: tungt, långsamt, maskinellt
    t = 42.0
    while t < 47.5:
        k.append((t, 84))
        t += 60 / 84
    # ASI: rullar ihop mot vitt
    t = 47.5
    bpm = 84
    while t < 51.9:
        k.append((t, bpm))
        t += 60.0 / bpm
        bpm *= 1.09
    # Outro: ett ensamt hjärta
    for t in (52.9, 54.1, 55.3, 56.5, 57.7):
        k.append((t, 50))
    return k


KICKS = _kicks()
KICK_T = [k for k, _ in KICKS]
HITS = [39.5, 40.3]  # stora smällar


def beat(t, decay=7.0):
    """0..1 puls som toppar på varje slag."""
    import math
    i = bisect.bisect_right(KICK_T, t) - 1
    v = 0.0
    if i >= 0:
        v = math.exp(-(t - KICK_T[i]) * decay)
    for h in HITS:
        if h <= t < h + 1.5:
            v = max(v, math.exp(-(t - h) * 3.0))
    return v


def scene_at(t):
    for name, s, e in SCENES:
        if s <= t < e:
            return name, s, e
    return SCENES[-1]
