"""Ljudmotorn: musik + ljudeffekter ur manus och filmens händelser.

    python3 motor/ljud.py <manus.json> <handelser.json> <ut.wav>

Allt syntetiseras (inga samplingar, ingen upphovsrättsskyddad musik).

Musiken väljs i manuset: "musik": {"stil": ..., "tempo": ..., "tonart": ..., "seed": ...}.
Varje scen anger musikens läge med "musik": spela | kaos | spanning | stopp | start.
Samma stil med annat seed ger en ny melodi, så filmer inte låter likadant.

Stilar:
  lekplats  – humppa/cirkus: tuba, kazoo-melodi, komp på efterslag, bråk-läge
  noir      – mörk synthpad i Vangelis-anda med pulserande bas
  lofi      – lugn, varm trumloop med elpiano (för förklarande filmer)

Ljudeffekter (händelser från temat eller manusets "ljud"):
  smack pop boing spring prat tick fall klubba stampel gong skrik trombon vissla
"""
import json
import math
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100


# ---------------------------------------------------------------- byggstenar
def lp(x, f, o=2):
    return sosfilt(butter(o, min(f, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, min(hi, SR / 2 - 100)], "band", fs=SR, output="sos"), x)


def tid(n):
    return np.arange(n) / SR


def adsr(n, a=0.005, d=0.05, s=0.7, r=0.05):
    e = np.full(n, s, dtype=float)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na)
    e[na:na + nd] = np.linspace(1, s, nd)
    nr = min(nr, n)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def saw_f(freq, n, ph=0.0):
    """Sågtand med varierande frekvens (array eller tal)."""
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    p = (np.cumsum(f) / SR + ph) % 1.0
    return 2 * p - 1


def sin_f(freq, n):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def sq_f(freq, n, duty=0.5):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    p = (np.cumsum(f) / SR) % 1.0
    return np.where(p < duty, 1.0, -1.0)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


TONARTER = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71, "Bb": 70, "Eb": 63, "Ab": 68}
DUR = [0, 2, 4, 5, 7, 9, 11]
MOLL = [0, 2, 3, 5, 7, 8, 10]


class Mix:
    def __init__(self, n):
        self.n = n
        self.L = np.zeros(n)
        self.R = np.zeros(n)
        self.rev = np.zeros(n)

    def put(self, t, sig, g=1.0, pan=0.0, rev=0.0):
        i = int(t * SR)
        if i >= self.n or i + len(sig) <= 0:
            return
        a = max(0, -i)
        j = min(self.n, i + len(sig))
        s = sig[a:j - i] * g
        self.L[i + a:j] += s * math.sqrt((1 - pan) / 2)
        self.R[i + a:j] += s * math.sqrt((1 + pan) / 2)
        if rev:
            self.rev[i + a:j] += s * rev


# ---------------------------------------------------------------- instrument
def kazoo(f, dur, rng):
    n = int(dur * SR)
    t = tid(n)
    vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.15, 0, 1)
    scoop = 1 - 0.06 * np.exp(-t * 30)
    x = saw_f(f * vib * scoop, n)
    buzz = 1 + 0.5 * rng.normal(0, 1, n)
    x = bp(x * buzz, 500, 3200) + 0.4 * bp(x, 1100, 1600)
    return x * adsr(n, 0.02, 0.06, 0.8, 0.04) * 0.5


def glock(f, dur):
    n = int(min(dur + 0.6, 1.2) * SR)
    t = tid(n)
    x = np.sin(2 * np.pi * f * 2 * t) + 0.4 * np.sin(2 * np.pi * f * 2 * 2.76 * t) + 0.15 * np.sin(2 * np.pi * f * 2 * 5.4 * t)
    return x * np.exp(-t * 5) * 0.25


def tuba(f, dur):
    n = int(dur * SR)
    t = tid(n)
    x = saw_f(f * (1 - 0.03 * np.exp(-t * 40)), n)
    x = lp(x, 900)
    return np.tanh(x * 1.8) * adsr(n, 0.01, 0.08, 0.55, 0.06) * 0.6


def komp(freqs, dur):
    n = int(dur * SR)
    t = tid(n)
    x = sum(saw_f(f, n) + 0.5 * sq_f(f * 1.003, n) for f in freqs)
    return lp(x, 2400) * np.exp(-t * 18) * 0.18


def kick(g=1.0):
    n = int(0.3 * SR)
    t = tid(n)
    return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 12) * g


def snare(rng, g=1.0, len_=0.14):
    n = int(len_ * SR)
    t = tid(n)
    return (bp(rng.normal(0, 1, n), 900, 6000) * 0.7 + np.sin(2 * np.pi * 190 * t) * 0.5) * np.exp(-t * 28) * g


def hihat(rng, g=1.0):
    n = int(0.05 * SR)
    return hp(rng.normal(0, 1, n), 7000) * np.exp(-tid(n) * 80) * g


def crash(rng, g=1.0):
    n = int(1.6 * SR)
    t = tid(n)
    return hp(rng.normal(0, 1, n), 4000) * np.exp(-t * 2.5) * g


def pad(freqs, dur, cut=900):
    n = int(dur * SR)
    x = sum(saw_f(f * d, n) for f in freqs for d in (0.997, 1.0, 1.004))
    return lp(x, cut) * adsr(n, 0.6, 0.2, 0.9, 0.8) * 0.06


def epiano(f, dur):
    n = int((dur + 0.5) * SR)
    t = tid(n)
    x = np.sin(2 * np.pi * f * t + 1.2 * np.sin(2 * np.pi * f * t) * np.exp(-t * 6))
    return x * np.exp(-t * 2.2) * 0.22


# ---------------------------------------------------------------- melodi
def gor_melodi(rng, steg_i_skala, takter=2):
    """Ett motiv: lista av (start_i_slag, längd_i_slag, skalsteg)."""
    rytmer = [[1, 1, 1, 1], [0.5, 0.5, 1, 0.5, 0.5, 1], [1.5, 0.5, 1, 1], [0.5, 0.5, 0.5, 0.5, 2], [1, 0.5, 0.5, 2], [0.5, 1, 0.5, 1, 1]]
    ut = []
    pos = 0.0
    steg = rng.choice([0, 2, 4])
    for _ in range(takter):
        for d in rytmer[rng.integers(len(rytmer))]:
            ut.append((pos, d, int(steg)))
            pos += d
            steg += rng.choice([-2, -1, -1, 1, 1, 2, 0, 3])
            steg = int(np.clip(steg, -2, 9))
    return ut


# ---------------------------------------------------------------- musikstilar
def lagen(tider, total):
    """Musikens läge per tidpunkt ur scenerna."""
    sc = [(s["start"], s["slut"], s.get("musik") or "spela") for s in tider["scener"]]

    def lage(t):
        for a, b, m in sc:
            if a <= t < b:
                return m
        return sc[-1][2]
    return lage


def musik_lekplats(mix, cfg, tider, handelser, total):
    rng = np.random.default_rng(cfg.get("seed", 1))
    bpm = cfg.get("tempo", 132)
    slag = 60 / bpm
    rot = TONARTER.get(cfg.get("tonart", "F"), 65)
    skala = DUR
    lage = lagen(tider, total)
    prog = [0, 4, 0, 3, 0, 4, 3, 0]

    def ton(steg, okt=0):
        o, s = divmod(steg, 7)
        return midi(rot + 12 * (o + okt) + skala[s])

    A, B = gor_melodi(rng, skala), gor_melodi(rng, skala)
    A2 = [(p, d, s + (1 if i == len(A) - 1 else 0)) for i, (p, d, s) in enumerate(A)]
    form = [A, A2, B, A]
    # spänningstrumvirvel: nollställs vid klubba/gong
    slag_ev = sorted(h["t"] for h in handelser if h["ljud"] in ("klubba", "gong", "stampel"))

    takt = 0
    t = 0.0
    while t < total:
        m = lage(t + 0.01)
        grad = prog[takt % len(prog)]
        ack = [grad, grad + 2, grad + 4]
        if m in ("spela", "start"):
            for b in range(4):
                tb = t + b * slag
                if lage(tb + 0.01) not in ("spela", "start"):
                    continue
                if b in (0, 2):
                    f = ton(ack[0] if b == 0 else ack[2], -2)
                    mix.put(tb, tuba(f, slag * 0.9), 0.75)
                    mix.put(tb, kick(0.5), 1.0)
                else:
                    mix.put(tb, komp([ton(s, -1) for s in ack], slag * 0.5), 1.0, pan=0.3)
                    mix.put(tb, snare(rng, 0.25), 1.0, pan=-0.1)
                mix.put(tb + slag / 2, hihat(rng, 0.12), 1.0, pan=0.4)
            fras = form[(takt // 2) % 4]
            for p, d, s in fras:
                bar_off = (takt % 2) * 4
                if not (bar_off <= p < bar_off + 4):
                    continue
                tn = t + (p - bar_off) * slag
                if tn >= total or lage(tn + 0.01) not in ("spela", "start"):
                    continue
                if float(p).is_integer():  # på slaget: närmaste ackordton
                    s = min((a + 7 * o for a in ack for o in (-1, 0, 1)), key=lambda c: abs(c - s))
                f = ton(s)
                mix.put(tn, kazoo(f, d * slag * 0.92, rng), 0.55, pan=-0.15, rev=0.2)
                if (takt // 8) % 2 == 1:
                    mix.put(tn, glock(f, d * slag), 0.5, pan=0.25, rev=0.3)
        elif m == "kaos":
            for b in range(8):
                tb = t + b * slag / 2
                if lage(tb + 0.01) != "kaos":
                    continue
                kr = rot - 24 + [0, 1, 3, 1, 6, 5, 3, 1][b]
                mix.put(tb, tuba(midi(kr), slag * 0.45), 0.7)
                mix.put(tb, snare(rng, 0.45 if b % 2 else 0.25), 1.0, pan=0.2)
                if b % 2 == 0:
                    mix.put(tb, kick(0.6), 1.0)
                for k in range(2):
                    tn = tb + k * slag / 4
                    f = midi(rot + 12 + int(rng.integers(0, 14)))
                    mix.put(tn, kazoo(f, slag / 4 * 0.9, rng), 0.35, pan=0.3 * (k * 2 - 1))
            if lage(t + 0.01) == "kaos":
                mix.put(t, crash(rng, 0.25), 1.0, pan=0.5)
        elif m == "spanning":
            # trumvirvel som växer mellan slagen
            n_sub = 16
            for b in range(n_sub):
                tb = t + b * slag * 4 / n_sub
                if lage(tb + 0.01) != "spanning":
                    continue
                forr = max([x for x in slag_ev if x <= tb] + [t - 4])
                nasta = min([x for x in slag_ev if x > tb] + [tb + 4])
                if nasta - tb < 0.06:
                    continue
                u = np.clip((tb - forr) / max(0.3, nasta - forr), 0, 1)
                for k in range(2):
                    mix.put(tb + k * slag * 2 / n_sub, snare(rng, 0.08 + 0.35 * u, 0.08), 1.0, pan=0.1)
            if lage(t + 0.01) == "spanning":
                mix.put(t, tuba(ton(0, -2), slag * 1.5), 0.4)
        takt += 1
        t += 4 * slag
    # avslutande ackord där musiken tystnar efter spela
    return mix


def musik_noir(mix, cfg, tider, handelser, total):
    rng = np.random.default_rng(cfg.get("seed", 1))
    rot = TONARTER.get(cfg.get("tonart", "A"), 69) - 24
    lage = lagen(tider, total)
    prog = [0, 5, 3, 4] if rng.random() < 0.5 else [0, 3, 5, 4]
    bpm = cfg.get("tempo", 90)
    slag = 60 / bpm
    t, i = 0.0, 0
    while t < total:
        m = lage(t + 0.01)
        if m != "stopp":
            g = prog[i % len(prog)]
            o, s = divmod(g, 7)
            r = rot + MOLL[s] + 12 * o
            fr = [midi(r), midi(r + 7), midi(r + 12 + (3 if s in (0, 3, 4) else 4)), midi(r + 19)]
            cut = 700 if m == "spela" else 1600
            dur = 8 * slag
            mix.put(t, pad(fr, dur + 1.0, cut), 1.0, rev=0.6)
            for b in range(8):
                tb = t + b * slag
                if lage(tb + 0.01) in ("spela", "kaos", "spanning"):
                    mix.put(tb, kick(0.7 if m != "spela" else 0.45), 1.0)
                    mix.put(tb + slag / 2, tuba(midi(r - 12), slag * 0.4) * 0.6, 0.7)
        i += 1
        t += 8 * slag
    return mix


def musik_lofi(mix, cfg, tider, handelser, total):
    rng = np.random.default_rng(cfg.get("seed", 1))
    rot = TONARTER.get(cfg.get("tonart", "D"), 62)
    lage = lagen(tider, total)
    bpm = cfg.get("tempo", 84)
    slag = 60 / bpm
    prog = [[0, 4, 7, 11], [5, 9, 12, 16], [2, 5, 9, 12], [7, 11, 14, 17]]
    t, i = 0.0, 0
    while t < total:
        if lage(t + 0.01) != "stopp":
            ack = prog[i % 4]
            for k, s in enumerate(ack):
                mix.put(t + k * 0.03, epiano(midi(rot - 12 + s), 4 * slag), 0.8, pan=-0.2 + k * 0.13, rev=0.4)
            for b in range(4):
                tb = t + b * slag
                if b in (0, 2):
                    mix.put(tb + (0.03 if b == 2 else 0), kick(0.6), 1.0)
                else:
                    mix.put(tb, snare(rng, 0.25), 1.0)
                mix.put(tb + slag * 0.55, hihat(rng, 0.1), 1.0, pan=0.3)
        i += 1
        t += 4 * slag
    return mix


STILAR = {"lekplats": musik_lekplats, "noir": musik_noir, "lofi": musik_lofi}


# ---------------------------------------------------------------- ljudeffekter
def sfx(h, rng):
    l = h["ljud"]
    ton = h.get("ton", 1.0)
    if l == "smack":
        n = int(0.35 * SR)
        t = tid(n)
        k = np.pad(kick(1.0), (0, n - int(0.3 * SR)))
        return 0.9 * k + bp(rng.normal(0, 1, n), 700, 5000) * np.exp(-t * 22) * 0.8
    if l == "pop":
        n = int(0.12 * SR)
        t = tid(n)
        return sin_f(np.linspace(380 * ton, 1300 * ton, n), n) * np.exp(-t * 30) * 0.6
    if l == "boing":
        n = int(0.45 * SR)
        t = tid(n)
        f = (170 + 260 * t / t[-1]) * ton + 60 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 6)
        return sin_f(f, n) * np.exp(-t * 7) * 0.35
    if l == "spring":
        out = np.zeros(int(0.6 * SR))
        for k in range(7):
            n = int(0.03 * SR)
            b = sin_f(900 + 200 * (k % 2), n) * np.exp(-tid(n) * 90)
            i = int(k * 0.07 * SR)
            out[i:i + n] += b * 0.25
        return out
    if l == "prat":
        dur = h.get("len", 1.0)
        ns = max(2, int(h.get("stavelser", 6)))
        r = np.random.default_rng(h.get("seed", 0))
        out = np.zeros(int((dur + 0.2) * SR))
        sl = dur / ns
        base = h.get("rost", 220)
        for k in range(ns):
            n = int(sl * 0.78 * SR)
            if n < 10:
                continue
            f = base * 2 ** (r.integers(-3, 6) / 12)
            t = tid(n)
            x = sq_f(f * (1 + 0.06 * np.sin(2 * np.pi * 7 * t)), n, 0.35) + 0.5 * saw_f(f * 2, n)
            x = bp(x, 400, 2800) * adsr(n, 0.008, 0.03, 0.7, 0.03)
            i = int(k * sl * SR)
            out[i:i + n] += x * 0.22
        return out
    if l == "tick":
        n = int(0.015 * SR)
        return hp(rng.normal(0, 1, n), 3000) * np.exp(-tid(n) * 300) * 0.25
    if l == "fall":
        n = int(0.7 * SR)
        t = tid(n)
        return sin_f(np.linspace(1700, 380, n), n) * adsr(n, 0.02, 0.1, 0.8, 0.1) * 0.25
    if l == "vissla":
        n = int(0.6 * SR)
        t = tid(n)
        return sin_f(2600 * (1 + 0.04 * np.sign(np.sin(2 * np.pi * 28 * t))), n) * adsr(n, 0.01, 0.05, 0.8, 0.08) * 0.25
    if l == "klubba":
        n = int(0.25 * SR)
        t = tid(n)
        return (np.sin(2 * np.pi * 210 * t) + 0.6 * np.sin(2 * np.pi * 470 * t)) * np.exp(-t * 35) * 0.9 + \
            bp(rng.normal(0, 1, n), 1500, 5000) * np.exp(-t * 120) * 0.6
    if l == "stampel":
        n = int(0.3 * SR)
        t = tid(n)
        return np.sin(2 * np.pi * np.cumsum(60 + 80 * np.exp(-t * 40)) / SR) * np.exp(-t * 14) * 0.9 + \
            bp(rng.normal(0, 1, n), 1200, 4000) * np.exp(-t * 40) * 0.4
    if l == "gong":
        n = int(2.5 * SR)
        t = tid(n)
        x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((98, 1), (157, 0.7), (231, 0.5), (318, 0.35), (447, 0.25)))
        k = np.pad(kick(1.2), (0, n - int(0.3 * SR)))
        return x * np.exp(-t * 1.4) * 0.35 + hp(rng.normal(0, 1, n), 2500) * np.exp(-t * 3) * 0.3 + k
    if l == "skrik":
        dur = h.get("len", 1.0)
        n = int((dur + 0.3) * SR)
        t = tid(n)
        x = np.zeros(n)
        for k in range(9):
            f = rng.uniform(170, 460)
            x += saw_f(f * (1 + 0.03 * np.sin(2 * np.pi * rng.uniform(5, 8) * t)), n)
        x = bp(x, 600, 2600) + bp(rng.normal(0, 1, n), 1000, 4000) * 0.6
        return x * adsr(n, 0.05, 0.1, 0.9, 0.25) * 0.12
    if l == "trombon":
        noter = [(62, 0.5), (61, 0.5), (60, 0.5), (59, 1.6)]
        out = np.zeros(int(3.4 * SR))
        pos = 0.0
        for k, (m, d) in enumerate(noter):
            n = int(d * SR)
            t = tid(n)
            vib = 1 + (0.02 * np.sin(2 * np.pi * 5 * t) if k == 3 else 0)
            x = saw_f(midi(m - 12) * vib, n) + 0.6 * sq_f(midi(m - 12) * vib * 1.002, n)
            wah = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(t / min(d, 0.5), 0, 1))
            lo = lp(x, 500) * (1 - wah) + lp(x, 2200) * wah
            i = int(pos * SR)
            out[i:i + n] += lo * adsr(n, 0.03, 0.05, 0.85, 0.08) * 0.45
            pos += d
        return out
    return np.zeros(1)


# ---------------------------------------------------------------- main
def main():
    manus = json.load(open(sys.argv[1], encoding="utf-8"))
    hd = json.load(open(sys.argv[2], encoding="utf-8"))
    ut = sys.argv[3]
    tider, handelser = hd["tider"], hd["handelser"]
    total = tider["total"]
    n = int(total * SR)
    musik = Mix(n)
    effekt = Mix(n)
    cfg = manus.get("musik", {})
    STILAR.get(cfg.get("stil", "lekplats"), musik_lekplats)(musik, cfg, tider, handelser, total)

    rng = np.random.default_rng(5)
    for h in handelser:
        s = sfx(h, rng)
        pan = {"prat": 0.0, "pop": rng.uniform(-0.5, 0.5)}.get(h["ljud"], 0.0)
        effekt.put(h["t"], s, h.get("styrka", 1.0), pan=pan, rev=0.1)

    # musiken duckar när någon pratar
    duck = np.ones(n)
    for h in handelser:
        if h["ljud"] in ("prat", "skrik"):
            a, b = int(h["t"] * SR), int((h["t"] + h.get("len", 1)) * SR)
            duck[a:b] = 0.55
    duck = lp(duck, 8)
    g_m = cfg.get("volym", 0.55)
    L = musik.L * duck * g_m + effekt.L
    R = musik.R * duck * g_m + effekt.R
    rv = musik.rev * g_m + effekt.rev
    if np.any(rv):
        ir_n = int(1.8 * SR)
        ir = lp(np.random.default_rng(1).normal(0, 1, ir_n), 5000) * np.exp(-tid(ir_n) * 3.0) * 0.015
        from scipy.signal import fftconvolve
        L += fftconvolve(rv, ir)[:n]
        R += fftconvolve(rv, np.roll(ir, 441))[:n]
    mix = np.stack([L, R], 1)
    mix = hp(mix.T, 30).T
    mix /= max(1e-9, np.abs(mix).max())
    mix = np.tanh(mix * 2.2) / np.tanh(2.2)  # mjuk limiter: jämnare och högre nivå
    mix /= max(1e-9, np.abs(mix).max()) / 0.9
    fo = int(0.3 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wavfile.write(ut, SR, (mix * 32767).astype(np.int16))
    print(ut)


if __name__ == "__main__":
    main()
