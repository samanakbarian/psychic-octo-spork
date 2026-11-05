"""Originalsoundtrack för film 01 – syntat i numpy, synkat mot timeline.py.

Mörk Vangelis-aktig pad, regn, ett hjärtslag som accelererar genom AI-historien,
tangentklick i terminalen, stora smällar på "HÄR. JUST NU.", en maskinell AGI-puls
och en riser som vitnar ut i ASI – sedan tystnad, regn och ett ensamt hjärta.

    python render_audio.py   -> output/soundtrack.wav
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

import timeline as TL

SR = 44100
N = int(TL.DURATION * SR)
rng = np.random.default_rng(3)
HERE = os.path.dirname(os.path.abspath(__file__))


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def put(buf, t, sig, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def saw(f, n, detune=0.0, phase=0.0):
    ph = (np.arange(n) * f * (1 + detune) / SR + phase) % 1.0
    return 2 * ph - 1


def note(name):
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    oct_ = int(name[-1])
    semi = names[name[0]] + (1 if "#" in name else 0) + (-1 if "b" in name[1:-1] else 0)
    return 440.0 * 2 ** ((semi + 12 * (oct_ - 4)) / 12)


L = np.zeros(N)
R = np.zeros(N)
REV = np.zeros(N)  # send till reverb

# ---------------------------------------------------------------- regn
noise = rng.normal(0, 1, N)
rain = bp(noise, 900, 7000) * 0.05 + lp(np.cumsum(rng.normal(0, 1, N)) * 0.002, 180) * 0.6
rain = hp(rain, 30)  # ta bort DC-drift
t_ax = np.arange(N) / SR
rain_g = 0.6 + 0.4 * ((t_ax > 39.5) & (t_ax < 42)) + 0.5 * (t_ax > 52)
rain_g *= 1 - 0.9 * ((t_ax > 47.5) & (t_ax < 52))
L += rain * rain_g
R += np.roll(rain, 2205) * rain_g

# ---------------------------------------------------------------- pad (CS-80-känsla)
CHORDS = [  # (start, slut, toner, filter-cutoff)
    (0.0, 3.0, ["A2", "E3", "C4"], 500),
    (3.0, 9.0, ["A1", "A2", "E3"], 380),
    (9.0, 14.0, ["F1", "F2", "C3", "A3"], 600),
    (14.0, 19.0, ["C2", "G2", "E3", "G3"], 900),
    (19.0, 25.0, ["G1", "D3", "G3", "B3"], 1100),
    (25.0, 30.0, ["A1", "E3", "A3", "C4"], 1300),
    (30.0, 35.0, ["D2", "A2", "F3", "A3"], 1500),
    (35.0, 39.5, ["E2", "B2", "G#3", "E4"], 1900),
    (42.0, 47.5, ["A1", "A2", "C3", "D#3"], 1100),   # tritonus – obehag
    (47.5, 52.0, ["A1", "E2", "A2", "D#3", "A3"], 2400),
    (52.6, 58.0, ["A2", "E3", "C4"], 420),
]
for s, e, notes, cut in CHORDS:
    a, r = (0.6, 1.2) if s > 0 else (0.05, 1.2)
    n = int((e - s + r) * SR)
    for k, nm in enumerate(notes):
        f = note(nm)
        for side, buf in ((-1, L), (1, R)):
            v = saw(f, n, 0.004 * side, rng.random()) + saw(f, n, -0.002 * side, rng.random()) * 0.7
            v = lp(v, cut, 2)
            v *= env(n, a, r) * (0.05 if f < 100 else 0.035)
            put(buf, s, v)
            put(REV, s, v, 0.5)

# ---------------------------------------------------------------- kick / hjärtslag
def kick(f0=110, f1=42, dur=0.45, click=0.3):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    k = np.sin(ph) * np.exp(-tt * 7)
    k[:200] += rng.normal(0, 1, 200) * click * np.linspace(1, 0, 200)
    return np.tanh(k * 1.6)


K = kick()
for t, bpm in TL.KICKS:
    if t < 39.5:
        g = 0.55 + 0.35 * (t - 3) / 36
        put(L, t, K, g)
        put(R, t, K, g)
        if bpm < 105:  # "lub-dub"
            put(L, t + 0.2, K, g * 0.45)
            put(R, t + 0.2, K, g * 0.45)
        if t > 14:  # hi-hat-tick på efterslag – data som flödar
            hh = hp(rng.normal(0, 1, 2200), 7000) * np.exp(-np.arange(2200) / 300)
            put(L, t + 30 / bpm, hh, 0.09)
            put(R, t + 30 / bpm, hh, 0.09)
    elif t < 52:  # AGI/ASI – tung, distad
        kk = kick(90, 36, 0.6, 0.6)
        put(L, t, kk, 0.85)
        put(R, t, kk, 0.85)
        put(REV, t, kk, 0.15)
    else:  # outro – ensamt, dovt hjärta
        kk = lp(kick(80, 40, 0.5, 0.0), 300)
        put(L, t, kk, 0.6)
        put(R, t, kk, 0.6)
        put(L, t + 0.22, kk, 0.3)
        put(R, t + 0.22, kk, 0.3)

# ---------------------------------------------------------------- sub-bas som följer ackorden
for s, e, notes, _ in CHORDS[1:8]:
    f = note(notes[0]) if note(notes[0]) < 70 else note(notes[0]) / 2
    n = int((e - s) * SR)
    b = np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.3, 0.3) * 0.12
    put(L, s, b)
    put(R, s, b)

# ---------------------------------------------------------------- tangentklick i terminalen
for t in TL.char_times():
    c = bp(rng.normal(0, 1, 900), 1500, 6000) * np.exp(-np.arange(900) / 120)
    pan = rng.uniform(0.6, 1.0)
    put(L, t, c, 0.22 * pan)
    put(R, t, c, 0.22 * (1.6 - pan))

# ---------------------------------------------------------------- glitch-bursts vid scenbyten
for name, s, e in TL.SCENES[1:]:
    n = int(0.16 * SR)
    g = rng.normal(0, 1, n)
    g = np.round(g * 3) / 3  # bitcrush
    g = np.repeat(g[::8], 8)[:n]
    g = bp(g, 400, 5000) * env(n, 0.005, 0.08)
    put(L, s - 0.04, g, 0.12)
    put(R, s - 0.02, g, 0.12)

# ---------------------------------------------------------------- "HÄR." / "JUST NU."
# riser in mot första smällen
n = int(1.6 * SR)
tt = np.arange(n) / SR
sw = bp(rng.normal(0, 1, n), 300, 6000) * (tt / tt[-1]) ** 3
put(L, 37.9, sw, 0.3)
put(R, 37.9, sw, 0.3)
for h, g in [(TL.HOOK_LINES[0][0], 0.75), (TL.HOOK_LINES[1][0], 0.95)] + list(zip(TL.HITS, (0.75, 0.7))):
    n = int(3.0 * SR)
    tt = np.arange(n) / SR
    boom = np.tanh((np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-tt * 9)) / SR) * np.exp(-tt * 1.4)) * 2.5)
    boom += lp(rng.normal(0, 1, n), 1800) * np.exp(-tt * 6) * 0.5
    put(L, h, boom, g * 0.9)
    put(R, h, boom, g * 0.9)
    put(REV, h, boom, 0.5)
# tinnitus-ton i tystnaden
n = int(2.3 * SR)
tin = np.sin(2 * np.pi * 6200 * np.arange(n) / SR) * env(n, 0.4, 1.0) * 0.012
put(L, 39.6, tin)
put(R, 39.6, tin)

# ---------------------------------------------------------------- AGI "BRAAAM"
for s in (42.0, 44.75):
    n = int(2.8 * SR)
    tt = np.arange(n) / SR
    v = sum(saw(note(nm), n, d) for nm in ("A1", "A2", "E2") for d in (-0.003, 0.0, 0.004))
    c = np.minimum(tt / 0.5, 1) * np.exp(-tt * 0.8)  # filtret öppnas och stängs
    out = lp(v, 220) * (1 - c) + lp(v, 2800) * c
    out = np.tanh(out * 0.7) * env(n, 0.03, 1.4) * 0.35
    put(L, s, out)
    put(R, s, out)
    put(REV, s, out, 0.4)

# ---------------------------------------------------------------- ASI-riser (Shepard-aktig)
s, e = 46.5, 52.0
n = int((e - s) * SR)
tt = np.arange(n) / SR
u = tt / tt[-1]
ris = np.zeros(n)
for k in range(6):
    f = 55 * 2 ** (k + u * 1.8)
    w = np.exp(-((np.log2(f / 440)) ** 2) / 2.5)
    ris += np.sin(2 * np.pi * np.cumsum(f) / SR) * w
ris += bp(rng.normal(0, 1, n), 800, 9000) * u ** 2 * 1.2
ris *= u ** 1.6 * 0.3
put(L, s, ris)
put(R, s, np.roll(ris, 300))
put(REV, s, ris, 0.3)

# Hård cut till tystnad vid 52.0 (bara regn kvar)
cut_i = int(52.0 * SR)
fade = int(0.01 * SR)
for buf in (L, R, REV):
    seg = buf[cut_i:]
    keep = np.zeros_like(seg)
    buf[cut_i:cut_i + fade] *= np.linspace(1, 0, fade)
    buf[cut_i + fade:] = 0
# lägg tillbaka regn + outro-hjärta efter cut
L[cut_i:] += (rain * rain_g)[cut_i:]
R[cut_i:] += (np.roll(rain, 2205) * rain_g)[cut_i:]
for t, bpm in TL.KICKS:
    if t >= 52:
        kk = lp(kick(80, 40, 0.5, 0.0), 300)
        for buf in (L, R):
            put(buf, t, kk, 0.6)
            put(buf, t + 0.22, kk, 0.3)
# två ensamma toner i outro
for t, nm in ((53.0, "A4"), (55.0, "E5")):
    n = int(4.0 * SR)
    tt = np.arange(n) / SR
    f = note(nm)
    tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 1.1) * 0.08
    put(L, t, tone)
    put(R, t, tone)
    put(REV, t, tone, 1.0)
# outro-pad (efter cut)
n = int(5.4 * SR)
for nm in ("A2", "E3", "C4"):
    v = lp(saw(note(nm), n) + saw(note(nm), n, 0.003), 420) * env(n, 1.5, 1.5) * 0.03
    put(L, 52.6, v)
    put(R, 52.6, v)
    put(REV, 52.6, v, 0.6)

# ---------------------------------------------------------------- reverb (stor hall)
def ir(seed, sec=3.2):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt = np.arange(n) / SR
    return lp(r.normal(0, 1, n), 5000) * np.exp(-tt * 2.2) * 0.02


L += fftconvolve(REV, ir(1))[:N]
R += fftconvolve(REV, ir(2))[:N]

# ---------------------------------------------------------------- master
mix = np.stack([L, R], 1)
mix = hp(mix.T, 25).T
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
mix /= np.abs(mix).max() / 0.89
fo = int(0.4 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
dst = os.path.join(HERE, "output", "soundtrack.wav")
wavfile.write(dst, SR, (mix * 32767).astype(np.int16))
print(dst)
