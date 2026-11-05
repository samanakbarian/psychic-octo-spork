"""Renderar film 01 "GNISTAN" som 1080x1920 rå-bildrutor till ffmpeg.

Användning:
    python render_video.py                 # hela filmen -> output/video_only.mp4
    python render_video.py --preview 26.5  # en stillbild -> output/preview_26.5.png
"""
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import timeline as TL

W, H, FPS = 1080, 1920, TL.FPS
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/jetbrains-mono"]


def font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


F_HUGE = font("InterDisplay-Black.otf", 210)
F_BIG = font("InterDisplay-Black.otf", 150)
F_CAP = font("InterDisplay-Bold.otf", 64)
F_SMALL = font("InterDisplay-Medium.otf", 42)
F_YEAR = font("JetBrainsMono-ExtraBold.ttf", 128)
F_MODEL = font("JetBrainsMono-Bold.ttf", 46)
F_STAT = font("JetBrainsMono-Medium.ttf", 27)
F_LABEL = font("JetBrainsMono-Regular.ttf", 24)
F_TERM = font("JetBrainsMono-Medium.ttf", 40)
F_LOG = font("JetBrainsMono-Regular.ttf", 25)

CYAN = (90, 220, 255)
AMBER = (255, 160, 60)
RED = (255, 40, 30)

CX, CY = 540, 800  # visuellt centrum (ovanför textytan, utanför TikTok-UI)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return smooth((t - a) / (b - a)) if b != a else float(t >= a)


def window(t, a, b, fi=0.3, fo=0.3):
    return ramp(t, a, a + fi) * (1 - ramp(t, b - fo, b))


# ---------------------------------------------------------------- förberäkning
class Assets:
    def __init__(self):
        rng = np.random.default_rng(7)
        random.seed(7)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]

        # Himmel: nästan svart topp -> smutsigt orange dis vid horisonten
        top = np.array([3, 6, 11], np.float32) / 255
        mid = np.array([14, 20, 30], np.float32) / 255
        hor = np.array([78, 38, 16], np.float32) / 255
        a = np.clip(yy / 0.62, 0, 1)[..., None]
        b = np.clip((yy - 0.62) / 0.2, 0, 1)[..., None]
        sky = top * (1 - a) + mid * a
        sky = sky * (1 - b) + hor * b
        self.sky = np.broadcast_to(sky, (H, W, 3)).astype(np.float32).copy()

        # Smog-textur som driver i sidled
        small = Image.fromarray((rng.random((24, 40)) * 255).astype(np.uint8))
        smog = np.asarray(small.resize((W * 2, H), Image.BICUBIC), np.float32) / 255
        self.smog = 0.7 + 0.6 * smog

        # Skyline: två lager byggnader + fönsterljus
        self.mask = np.zeros((H, W), np.float32)
        self.bcol = np.zeros((H, W, 3), np.float32)
        lights = Image.new("RGB", (W, H))
        ld = ImageDraw.Draw(lights)
        mimg = Image.new("L", (W, H))
        md = ImageDraw.Draw(mimg)
        far = Image.new("L", (W, H))
        fd = ImageDraw.Draw(far)

        def building(draw_mask, x0, x1, top_y, lit_p, dim):
            draw_mask.rectangle([x0, top_y, x1, H], fill=255)
            if random.random() < 0.3:  # antenn
                ax = (x0 + x1) // 2
                draw_mask.rectangle([ax - 2, top_y - random.randint(40, 140), ax + 2, top_y], fill=255)
            for wy in range(top_y + 14, H, 22):
                for wx in range(x0 + 8, x1 - 8, 16):
                    if random.random() < lit_p:
                        c = random.choice([AMBER, AMBER, (255, 200, 120), CYAN, (255, 90, 150)])
                        c = tuple(int(v * dim * random.uniform(0.4, 1.0)) for v in c)
                        ld.rectangle([wx, wy, wx + 6, wy + 9], fill=c)

        x = -30
        while x < W:  # bortre lager
            w = random.randint(50, 140)
            building(fd, x, x + w, random.randint(1000, 1320), 0.10, 0.45)
            x += w + random.randint(-10, 20)
        x = -20
        while x < W:  # närmre lager
            w = random.randint(70, 190)
            ty = random.randint(1150, 1560)
            if random.random() < 0.12:
                ty = random.randint(620, 900)  # megatorn
            building(md, x, x + w, ty, 0.22, 1.0)
            x += w + random.randint(0, 30)

        farm = np.asarray(far, np.float32) / 255
        nearm = np.asarray(mimg, np.float32) / 255
        farcol = np.array([22, 16, 16], np.float32) / 255
        nearcol = np.array([4, 5, 7], np.float32) / 255
        self.mask = np.clip(farm + nearm, 0, 1)
        self.bcol = (farcol * farm[..., None] * (1 - nearm[..., None]) + nearcol * nearm[..., None])
        self.lights = np.asarray(lights, np.float32) / 255
        self.lights_lum = self.lights.max(axis=2)

        # Neonskyltar (vertikala band) – flimrar
        self.signs = [(random.randint(60, W - 80), random.randint(1080, 1350), random.randint(90, 220),
                       random.choice([CYAN, (255, 60, 160), AMBER])) for _ in range(5)]

        # Regn
        n = 520
        self.rx = rng.uniform(-100, W + 100, n)
        self.ry = rng.uniform(0, H, n)
        self.rs = rng.uniform(1700, 2600, n)
        self.rl = rng.uniform(25, 75, n)

        # Efterbehandling
        yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xv - W / 2) / (W * 0.62)) ** 2 + ((yv - H / 2) / (H * 0.62)) ** 2)
        self.vig = np.clip(1.15 - d ** 2 * 0.75, 0.15, 1)[..., None].astype(np.float32)
        self.scan = (1 - 0.07 * ((np.arange(H) % 3) == 0)).astype(np.float32)[:, None, None]
        self.grain = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]

        # Neurala nätet (3D-punktmoln, sorterat inifrån och ut)
        N = 430
        pts = rng.normal(0, 1, (N, 3))
        pts /= np.linalg.norm(pts, axis=1, keepdims=True)
        pts *= rng.uniform(0.05, 1.0, (N, 1)) ** 0.6
        pts[0] = 0
        order = np.argsort(np.linalg.norm(pts, axis=1))
        self.gp = pts[order] * 340
        self.ge = []
        for i in range(1, N):
            dd = np.linalg.norm(self.gp[:i] - self.gp[i], axis=1)
            for j in np.argsort(dd)[:2]:
                self.ge.append((i, int(j)))

        # Dendriter för gnistan
        self.dend = []
        for k in range(9):
            ang = k / 9 * 2 * math.pi + random.uniform(-0.3, 0.3)
            p = [(0.0, 0.0)]
            for s in range(26):
                ang += random.uniform(-0.35, 0.35)
                p.append((p[-1][0] + math.cos(ang) * 9, p[-1][1] + math.sin(ang) * 9))
            self.dend.append(p)

        # Iris-textur för ögat
        R = 380
        yv, xv = np.mgrid[-R:R, -R:R].astype(np.float32)
        r = np.sqrt(xv ** 2 + yv ** 2) / R
        th = np.arctan2(yv, xv)
        fib = 0.55 + 0.45 * np.sin(th * 140 + 6 * np.sin(th * 13) + r * 9) * np.sin(th * 37 + r * 20)
        base = (np.array([30, 110, 130], np.float32) / 255)[None, None] * (1 - r[..., None]) * 1.2 \
            + (np.array([10, 40, 60], np.float32) / 255)[None, None]
        inner = np.clip(1 - (r - 0.3) / 0.25, 0, 1)[..., None]
        base = base * (1 - inner) + (np.array([200, 110, 40], np.float32) / 255) * inner
        iris = base * fib[..., None]
        iris *= np.clip((1 - r) / 0.06, 0, 1)[..., None]   # mörk limbusring
        iris *= (0.35 + 0.65 * np.clip((0.97 - r) / 0.2, 0, 1))[..., None]
        self.iris = iris.astype(np.float32)
        self.iris_r = r
        self.iris_R = R

        # Tanketräd (resonerande modeller)
        self.tree = []
        self.best = set()

        def grow(x, y, ang, depth, t0, idx_parent, alive):
            if depth > 7:
                return
            for k in range(2 if depth < 6 else 1):
                a2 = ang + random.uniform(-0.75, 0.75)
                L = random.uniform(55, 110) * (0.92 ** depth)
                x2, y2 = x + math.cos(a2) * L, y + math.sin(a2) * L
                dead = alive and random.random() < 0.22
                self.tree.append((x, y, x2, y2, t0, depth, dead, idx_parent))
                me = len(self.tree) - 1
                if not dead:
                    grow(x2, y2, a2, depth + 1, t0 + random.uniform(0.25, 0.45), me, True)

        for k in range(7):
            grow(0, 0, k / 7 * 2 * math.pi, 0, 0.0, -1, True)
        # välj en "vinnande" väg: djupaste levande bladet
        deepest = max(range(len(self.tree)), key=lambda i: (self.tree[i][5], -self.tree[i][6]))
        i = deepest
        while i >= 0:
            self.best.add(i)
            i = self.tree[i][7]

        # Agenter som rör sig längs ett rutnät
        self.agents = self._sim_agents(rng)

        # Logg-rader
        self.logs = [
            "agent_0417 » bokar flyg ............ ✓",
            "agent_1102 » skriver kod ........... ✓",
            "agent_0093 » förhandlar avtal ...... ✓",
            "agent_3381 » svarar kund #88 120 ... ✓",
            "agent_0731 » granskar agent_0417 .. ✓",
            "agent_5520 » optimerar sig själv .. ✓",
            "agent_2210 » startar agent_2211 ... ✓",
            "agent_2211 » startar agent_2212 ... ✓",
            "agent_2212 » startar agent_2213 ... ✓",
            "agent_2213 » behöver inte godkännande",
            "agent_9999 » ...",
        ]

    def _sim_agents(self, rng):
        n, g = 170, 60
        steps = int(5.0 * FPS) + 10
        pos = np.zeros((steps, n, 2), np.float32)
        p = np.stack([rng.integers(1, W // g, n) * g, rng.integers(7, 26, n) * g], 1).astype(np.float32)
        d = rng.integers(0, 4, n)
        sp = rng.uniform(260, 620, n) / FPS
        dirs = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]], np.float32)
        for s in range(steps):
            pos[s] = p
            p = p + dirs[d] * sp[:, None]
            on = (np.abs(p[:, 0] / g - np.round(p[:, 0] / g)) * g < sp) & \
                 (np.abs(p[:, 1] / g - np.round(p[:, 1] / g)) * g < sp)
            turn = on & (rng.random(n) < 0.35)
            p[turn] = np.round(p[turn] / g) * g
            d[turn] = rng.integers(0, 4, turn.sum())
            out = (p[:, 0] < 0) | (p[:, 0] > W) | (p[:, 1] < 380) | (p[:, 1] > 1560)
            d[out & (p[:, 0] < 0)] = 0
            d[out & (p[:, 0] > W)] = 1
            d[out & (p[:, 1] < 380)] = 2
            d[out & (p[:, 1] > 1560)] = 3
        return pos


A = None


def init():
    global A
    A = Assets()


# ---------------------------------------------------------------- hjälpare
def glow_dot(d, x, y, r, col, rings=10, k=1.0):
    for i in range(rings, -1, -1):
        rr = r * (1 + i * 0.7)
        f = k * (1 - i / (rings + 1)) ** 2.2
        c = tuple(int(v * f) for v in col)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c)


def scale_col(c, f):
    return tuple(int(clamp(v * f / 255) * 255) for v in c)


def mix_col(a, b, k):
    return tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))


def shift_rows(arr, off):
    if off <= 0:
        return arr
    out = np.zeros_like(arr)
    out[off:] = arr[:H - off]
    return out


# ---------------------------------------------------------------- scenbild
def compose(t, depth=0):
    """Returnerar float-bild (H,W,3) av själva världen, utan HUD/texter."""
    name, s0, s1 = TL.scene_at(t)
    bt = TL.beat(t)
    back = Image.new("RGB", (W, H))   # ljus bakom skylinen
    front = Image.new("RGB", (W, H))  # ljus framför
    bd, fd = ImageDraw.Draw(back), ImageDraw.Draw(front)

    sky_k = 0.25
    city_rise = 1.0     # 0 = gömd under bild, 1 = på plats
    lights_k = 0.0
    red_k = 0.0
    white = 0.0
    rain_k = 1.0
    eye = None

    # ----- GNISTAN: en ensam neuron (GPT-1 + outro)
    if name in ("gpt1", "outro") or (name == "hook" and t > 2.3):
        city_rise = 0.0
        sky_k = 0.18
        k = ramp(t, 3.0, 4.2) if name == "gpt1" else (ramp(t, 52.4, 53.2) if name == "outro" else 0.25)
        r = 7 + 9 * bt
        glow_dot(fd, CX, CY, r, (200, 245, 255), rings=12, k=k)
        if name == "gpt1":
            g = ramp(t, 4.5, 8.8)
            for p in A.dend:
                m = max(2, int(len(p) * g))
                pts = [(CX + x, CY + y) for x, y in p[:m]]
                fd.line(pts, fill=scale_col(CYAN, 120 * k), width=2)
                if m > 2:
                    ex, ey = pts[-1]
                    glow_dot(fd, ex, ey, 2, CYAN, rings=3, k=0.6 * k)
        if name == "outro":
            rain_k = 0.5

    # ----- NÄTET växer (GPT-2, GPT-3)
    if name in ("gpt2", "gpt3"):
        sky_k = 0.22
        if name == "gpt2":
            n = int(2 + 70 * ramp(t, 9.0, 14.0) ** 1.3)
            city_rise = 0.0
            scale, cy, fade = 1.0, CY, 1.0
        else:
            n = int(72 + 358 * ramp(t, 14.0, 17.2))
            city_rise = ramp(t, 15.8, 18.8)
            pull = ramp(t, 16.3, 19.0)
            scale, cy, fade = 1.0 - 0.45 * pull, CY - 260 * pull, 1.0
        ang = t * 0.28
        ca, sa = math.cos(ang), math.sin(ang)
        P = A.gp[:n]
        x = P[:, 0] * ca + P[:, 2] * sa
        z = -P[:, 0] * sa + P[:, 2] * ca
        y = P[:, 1] * math.cos(0.3) - z * math.sin(0.3)
        persp = 900 / (900 + z)
        sx = CX + x * persp * scale
        sy = cy + y * persp * scale
        pulse = 0.6 + 0.4 * bt
        for i, j in A.ge:
            if i < n and j < n:
                fd.line([(sx[i], sy[i]), (sx[j], sy[j])], fill=scale_col((50, 150, 190), 255 * 0.55 * fade), width=1)
        for i in range(n):
            br = clamp(persp[i] * 0.8) * fade * pulse
            r = 2.2 * persp[i] + (6 if i == 0 else 0)
            glow_dot(fd, sx[i], sy[i], r, (190, 240, 255), rings=3, k=br)
        lights_k = city_rise * 0.6

    # ----- CHATGPT: staden tänds
    if name == "chatgpt":
        sky_k = 0.3
        lights_k = 0.6 + 0.5 * ramp(t, 21.8, 24.8)

    # ----- GPT-4: ögat
    if name == "gpt4":
        sky_k = 0.28
        lights_k = 0.9
        eye = t

    # ----- RESONERANDE: tanketrädet
    if name == "reason":
        sky_k = 0.26
        lights_k = 0.85
        lt = t - 30.0
        conv = ramp(t, 33.3, 34.2)
        fade = 1 - ramp(t, 34.4, 35.0)
        glow_dot(fd, CX, CY, 6 + 6 * bt, (255, 255, 255), rings=8, k=fade)
        for idx, (x0, y0, x1, y1, t0, dep, dead, par) in enumerate(A.tree):
            g = clamp((lt - t0 * 0.95) / 0.3)
            if g <= 0:
                continue
            xe, ye = x0 + (x1 - x0) * g, y0 + (y1 - y0) * g
            if idx in A.best:
                col, k = (220, 250, 255), 1.0
            elif dead:
                col, k = (255, 60, 40), 0.75 * (1 - conv)
            else:
                col, k = CYAN, (0.75 - 0.15 * dep / 7) * (1 - 0.85 * conv)
            k *= fade
            w = 3 if idx in A.best and conv > 0 else 2
            fd.line([(CX + x0, CY + y0), (CX + xe, CY + ye)], fill=scale_col(col, 255 * k), width=w)
            if dead and g >= 1:
                fd.text((CX + x1 - 6, CY + y1 - 12), "×", font=F_LOG, fill=scale_col(col, 255 * k))

    # ----- AGENTER
    if name == "agents":
        sky_k = 0.3
        lights_k = 1.0
        f = int((t - 35.0) * FPS)
        f = min(f, len(A.agents) - 1)
        act = ramp(t, 35.0, 36.0)
        for tr in range(8, 0, -1):
            a0 = A.agents[max(0, f - tr)]
            a1 = A.agents[max(0, f - tr + 1)]
            k = (1 - tr / 9) * act
            col = scale_col(AMBER, 200 * k)
            for i in range(len(a0)):
                if abs(a0[i, 0] - a1[i, 0]) + abs(a0[i, 1] - a1[i, 1]) < 60:
                    fd.line([tuple(a0[i]), tuple(a1[i])], fill=col, width=2)
        for i, (x, y) in enumerate(A.agents[f]):
            glow_dot(fd, x, y, 2.5, (255, 200, 140) if i % 9 else (255, 70, 50), rings=3, k=act)

    # ----- NU: strömavbrott
    if name == "now":
        sky_k = 0.12
        lights_k = 0.0
        if t > 41.3:  # tänds igen – i rött
            fl = 1.0 if (int(t * 22) % 3) else 0.2
            lights_k = fl * ramp(t, 41.3, 41.9)
            red_k = 1.0

    # ----- AGI / ASI: sfären stiger
    if name in ("agi", "asi"):
        red_k = 1.0
        sky_k = 0.3 + 0.2 * bt
        lights_k = 0.6 + 0.8 * TL.beat(t, 4.0)
        if name == "agi":
            rad = 520
            cy = 1750 - 900 * smooth((t - 42.0) / 5.0)
            bri = 0.8 + 0.4 * bt
        else:
            u = (t - 47.5) / 4.5
            rad = 520 + 1900 * u ** 2.2
            cy = 850 - 50 * u
            bri = 1.0 + 1.5 * u
            white = ramp(t, 50.4, 51.95) ** 2
        rot = t * 0.35
        col = mix_col(RED, (255, 230, 220), clamp((t - 47.5) / 4))
        lay = back if (name == "agi" and t < 45.5) else front
        ld = ImageDraw.Draw(lay)
        nlat, nlon, seg = 13, 22, 48
        for li in range(1, nlat):
            phi = -math.pi / 2 + li * math.pi / nlat
            pts, vis = [], []
            for k in range(seg + 1):
                th = k / seg * 2 * math.pi + rot
                x, y, z = math.cos(phi) * math.cos(th), math.sin(phi), math.cos(phi) * math.sin(th)
                pts.append((CX + x * rad, cy + (y * 0.95 - z * 0.25) * rad))
                vis.append(z > -0.1)
            for k in range(seg):
                kk = 1.0 if vis[k] else 0.25
                ld.line([pts[k], pts[k + 1]], fill=scale_col(col, 255 * 0.7 * bri * kk), width=2)
        for lo in range(nlon):
            th = lo / nlon * 2 * math.pi + rot
            pts, vis = [], []
            for k in range(seg + 1):
                phi = -math.pi / 2 + k / seg * math.pi
                x, y, z = math.cos(phi) * math.cos(th), math.sin(phi), math.cos(phi) * math.sin(th)
                pts.append((CX + x * rad, cy + (y * 0.95 - z * 0.25) * rad))
                vis.append(z > -0.1)
            for k in range(seg):
                kk = 1.0 if vis[k] else 0.25
                ld.line([pts[k], pts[k + 1]], fill=scale_col(col, 255 * 0.7 * bri * kk), width=2)
        glow_dot(ld, CX, cy, 30 + 30 * bt, col, rings=10, k=0.9 * bri)

    # ---------------------------------------------- sammansättning
    sm_off = int(t * 18) % W
    img = A.sky * (sky_k / 0.25) * A.smog[:, sm_off:sm_off + W, None]
    if red_k:
        img = img * (1 - 0.6 * red_k) + img.mean(axis=2, keepdims=True) * np.array([2.0, 0.35, 0.3], np.float32) * 0.6 * red_k

    off = int((1 - city_rise) * 1100)
    mask = shift_rows(A.mask, off)[..., None]
    backn = np.asarray(back, np.float32) / 255
    img = img + backn * (1 - mask)
    img = img * (1 - mask) + shift_rows(A.bcol, off)

    emit = np.asarray(front, np.float32) / 255 + backn * (1 - mask) * 0.5
    if lights_k > 0 and city_rise > 0:
        if red_k:
            L = shift_rows(A.lights_lum, off)[..., None] * np.array([1.0, 0.13, 0.08], np.float32)
        else:
            L = shift_rows(A.lights, off)
        emit = emit + L * lights_k
        ld = None
        for (sx, sy, sh, sc) in A.signs:
            fl = 0.15 if math.sin(t * 13 + sx) > 0.93 else 1.0
            y0 = sy + off
            if y0 < H:
                c = np.array(sc if not red_k else RED, np.float32) / 255
                emit[y0:min(H, y0 + sh), sx:sx + 7] += c * 0.9 * fl * lights_k

    if eye is not None:
        img, emit = draw_eye(img, emit, eye)

    # Bloom
    e8 = Image.fromarray((np.clip(emit, 0, 1) * 255).astype(np.uint8))
    sm = e8.resize((W // 4, H // 4), Image.BILINEAR)
    b1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR), np.float32) / 255
    b2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR), np.float32) / 255
    img = img + emit + b1 * 1.1 + b2 * 1.3

    # Regn
    if rain_k > 0:
        rimg = Image.new("L", (W, H))
        rd = ImageDraw.Draw(rimg)
        ys = (A.ry + A.rs * t) % (H + 100) - 50
        for x, y, l in zip(A.rx, ys, A.rl):
            xx = x - 0.13 * (y)
            xx = (xx % (W + 200)) - 100
            rd.line([(xx, y), (xx + l * 0.13, y + l)], fill=90, width=1)
        rn = np.asarray(rimg, np.float32)[..., None] / 255
        img = img + rn * np.array([0.55, 0.65, 0.8], np.float32) * 0.45 * rain_k

    if white > 0:
        img = img * (1 - white) + white * 1.4
    return img


def draw_eye(img, emit, t):
    o = ramp(t, 25.3, 26.4) * (1 - ramp(t, 29.5, 30.2))
    blink = 1 - 0.95 * math.exp(-((t - 28.3) / 0.07) ** 2)
    o *= blink
    if o <= 0.01:
        return img, emit
    ew, eh = 470, 230 * o
    x0, x1 = CX - ew, CX + ew
    y0, y1 = int(CY - 240), int(CY + 240)
    yv, xv = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    nx = (xv - CX) / ew
    ny = (yv - CY) / max(eh, 1)
    lens = np.clip((1 - nx ** 2) - np.abs(ny) * 1.0, 0, 1)
    m = np.clip(lens * 18, 0, 1)[..., None]
    sclera = np.array([34, 38, 46], np.float32) / 255 * (0.25 + 0.75 * lens[..., None] ** 0.7)
    # iris med små saccader + pupill som vidgas
    sx = 40 * math.sin(t * 1.3) + (25 if (t % 1.7) > 0.85 else -10)
    sy = 8 * math.sin(t * 2.1)
    R = A.iris_R
    scale = 230 / R
    ix0 = int(CX + sx - R * scale)
    iy0 = int(CY + sy - R * scale)
    size = int(2 * R * scale)
    iris = np.asarray(Image.fromarray((A.iris * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255
    rr = np.asarray(Image.fromarray((np.clip(A.iris_r, 0, 2) * 100).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 100
    pup = 0.24 + 0.08 * ramp(t, 26.5, 28.0) + 0.05 * TL.beat(t)
    ia = np.clip((1 - rr) / 0.02, 0, 1)[..., None]
    pm = np.clip((rr - pup) / 0.02, 0, 1)[..., None]
    iris = iris * pm
    region = sclera.copy()
    ys0, xs0 = iy0 - y0, ix0 - x0
    a0, b0 = max(0, ys0), max(0, xs0)
    a1, b1 = min(region.shape[0], ys0 + size), min(region.shape[1], xs0 + size)
    sub_ia = ia[a0 - ys0:a1 - ys0, b0 - xs0:b1 - xs0]
    region[a0:a1, b0:b1] = region[a0:a1, b0:b1] * (1 - sub_ia) + iris[a0 - ys0:a1 - ys0, b0 - xs0:b1 - xs0] * sub_ia
    # reflex av staden
    hx, hy = int(CX + sx - 70 - x0), int(CY + sy - 70 - y0)
    region[hy:hy + 14, hx:hx + 40] += np.array([1.0, 0.7, 0.4], np.float32) * 0.8
    region[hy + 22:hy + 28, hx + 10:hx + 28] += 0.4
    k = ramp(t, 25.3, 26.0)
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m * 0.95) + region * m * k
    emit[y0:y1, x0:x1] += region * m * k * 0.12
    return img, emit


# ---------------------------------------------------------------- texter/HUD
def text_layer(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    name, s0, s1 = TL.scene_at(t)
    dark_text = name == "asi" and t > 50.0

    # HUD – årsräknaren
    if name in TL.HUD:
        year, model, stat = TL.HUD[name]
        if name == "agents" and t >= TL.AGENTS_2026_AT:
            year, s0 = "2026", TL.AGENTS_2026_AT
        rnd = random.Random(int(t * FPS))
        if t - s0 < 0.4 or name in ("agi", "asi"):
            if name in ("agi", "asi") and rnd.random() < 0.6 and t - s0 >= 0.4:
                year = "20" + "".join(rnd.choice("0123456789?") for _ in range(2)) if name == "agi" else \
                    "".join(rnd.choice("0123456789?∞") for _ in range(4))
            elif t - s0 < 0.4:
                year = "".join(rnd.choice("0123456789") for _ in range(4))
        k = ramp(t, s0, s0 + 0.15) if name != "gpt1" else ramp(t, 3.0, 3.3)
        col = (20, 20, 20) if dark_text else (235, 240, 245)
        x, y = 70, 230
        a = int(255 * k)
        d.text((x, y), "● REC   ÅR", font=F_LABEL, fill=(255, 60, 50, a if int(t * 2) % 2 else a // 3))
        d.text((x - 6, y + 28), year, font=F_YEAR, fill=col + (a,))
        mc = (120, 20, 10) if dark_text else ((255, 70, 50) if name in ("agi", "asi") else CYAN)
        d.text((x, y + 172), model, font=F_MODEL, fill=mc + (a,))
        d.text((x, y + 232), stat, font=F_STAT, fill=((60, 40, 30) if dark_text else AMBER) + (int(a * 0.85),))

    # ChatGPT-terminal
    if name == "chatgpt":
        k = ramp(t, 19.2, 19.6) * (1 - ramp(t, 24.6, 25.0))
        bx0, by0, bx1, by1 = 110, 600, 970, 960
        d.rectangle([bx0, by0, bx1, by1], fill=(4, 8, 12, int(200 * k)), outline=CYAN + (int(255 * k),), width=2)
        d.text((bx0 + 24, by0 + 16), "TERMINAL // 2022-11-30", font=F_LABEL, fill=CYAN + (int(140 * k),))
        yy = by0 + 80
        for (s, e, txt) in TL.TYPING:
            if t >= s:
                n = int(len(txt) * clamp((t - s) / (e - s)))
                shown = txt[:n]
                lines = wrap(d, shown, F_TERM, bx1 - bx0 - 60)
                for ln in lines:
                    d.text((bx0 + 30, yy), ln, font=F_TERM, fill=(220, 245, 255, int(255 * k)))
                    yy += 56
                if t < e or (s, e, txt) == TL.TYPING[-1]:
                    if int(t * 3) % 2 == 0:
                        lw = d.textlength(lines[-1] if lines else "", font=F_TERM)
                        d.rectangle([bx0 + 34 + lw, yy - 52, bx0 + 56 + lw, yy - 10], fill=CYAN + (int(255 * k),))
                yy += 22
        u = ramp(t, 21.8, 24.6) ** 3
        users = int(100_000_000 * u)
        s = f"{users:,}".replace(",", " ")
        d.text((bx0 + 24, by1 - 60), f"ANVÄNDARE: {s}", font=F_TERM, fill=AMBER + (int(255 * k * ramp(t, 21.6, 21.9)),))

    # Agentloggar
    if name == "agents" and t > 36.3:
        n = int((t - 36.3) ** 1.6 * 4)
        shown = A.logs[:min(n, len(A.logs))]
        y = 560
        for i, ln in enumerate(shown[-9:]):
            red = "startar" in ln or "godkännande" in ln or "själv" in ln
            d.text((70, y), ln, font=F_LOG, fill=((255, 80, 60) if red else (255, 190, 120)) + (210,))
            y += 40

    # Stora slag-texter
    if name == "hook":
        for st, txt in TL.HOOK_LINES:
            if t >= st and t < 2.4:
                big = F_HUGE if txt == "8 ÅR." else F_BIG
                y = 700 if txt != "8 ÅR." else 880
                centered(d, txt, big, y, (255, 255, 255, 255))
        if t >= 1.3 and t < 2.4:
            centered(d, "GPT-1  →  AGENTER  →  ?", F_STAT, 1150, AMBER + (230,))
    if name == "now":
        for st, txt in TL.NOW_LINES:
            if t >= st:
                y = 700 if txt == "HÄR." else 920
                centered(d, txt, F_HUGE if txt == "HÄR." else F_BIG, y, (255, 255, 255, 255))
        if t > 40.8:
            centered(d, "2026", F_STAT, 1130, AMBER + (int(255 * ramp(t, 40.8, 41.1)),))

    # Undertexter
    for (a, b, txt, style) in TL.CAPTIONS:
        if a <= t < b:
            k = window(t, a, b, 0.25, 0.25)
            dy = int((1 - ramp(t, a, a + 0.35)) * 20)
            f = F_CAP if style == "cap" else F_SMALL
            y = 1270 if style == "cap" else 1380
            col = (10, 10, 10) if dark_text else (255, 255, 255)
            for i, ln in enumerate(wrap(d, txt, f, 820)):
                centered(d, ln, f, y + dy + i * int(f.size * 1.18), col + (int(255 * k),))
    return layer


def centered(d, txt, f, y, fill):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=fill)


def wrap(d, txt, f, maxw):
    if "\n" in txt:
        return [l for part in txt.split("\n") for l in wrap(d, part, f, maxw)]
    words, lines, cur = txt.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return [l for l in lines if l] or [""]


# ---------------------------------------------------------------- hela bildrutan
def glitch_amount(t):
    g = 0.0
    for name, s, e in TL.SCENES[1:]:
        g = max(g, math.exp(-abs(t - s) * 14))
    if t < 2.4:
        g = max(g, 0.35)
    if 42 < t < 52:
        g = max(g, 0.15 + 0.4 * clamp((t - 46) / 6))
    for h in TL.HITS:
        if h <= t < h + 0.25:
            g = max(g, 1.0)
    return g


HOOK_FLASH = [(0.0, 26.8), (0.35, 45.6), (0.7, 37.6), (1.05, 16.8), (1.4, 50.0), (1.75, 32.5), (2.05, 44.0)]


def render(fi):
    t = fi / FPS
    rnd = random.Random(fi * 7919)
    name, _, _ = TL.scene_at(t)

    if name == "hook" and t < 2.3:
        # snabba glimtar av framtiden bakom krok-texten
        src = None
        for st, tt in HOOK_FLASH:
            if st <= t < st + 0.22:
                src = tt + (t - st)
        img = compose(src) * 0.42 if src is not None else np.zeros((H, W, 3), np.float32) + 0.01
    else:
        img = compose(t)

    if name == "now" and t < 41.3:
        img *= 0.6

    # text: skugga + text + glöd
    tl = text_layer(t)
    ta = np.asarray(tl, np.float32) / 255
    alpha = ta[..., 3:4]
    sh = np.asarray(tl.getchannel("A").resize((W // 4, H // 4), Image.BILINEAR)
                    .filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255
    dark_text = name == "asi" and t > 50.0
    if not dark_text:
        img = img * (1 - np.clip(sh * 1.4, 0, 0.75))
    img = img * (1 - alpha) + ta[..., :3] * alpha
    if not dark_text:
        img = img + sh * ta[..., :3].max(axis=2, keepdims=True) * 0.0 + sh * 0.06

    # skakning på slag
    sk = TL.beat(t, 12) * (6 if name in ("agi", "asi", "now") else 2)
    if sk > 0.5:
        img = np.roll(img, (rnd.randint(-int(sk), int(sk)), rnd.randint(-int(sk), int(sk))), axis=(0, 1))

    # glitch: förskjutna band
    g = glitch_amount(t)
    if g > 0.05:
        for _ in range(int(g * 9)):
            if rnd.random() < g:
                y0 = rnd.randint(0, H - 40)
                hgt = rnd.randint(6, int(20 + 140 * g))
                img[y0:y0 + hgt] = np.roll(img[y0:y0 + hgt], rnd.randint(-int(80 * g), int(80 * g)), axis=1)

    # kromatisk aberration
    ca = int(2 + 14 * g)
    img[..., 0] = np.roll(img[..., 0], ca, axis=1)
    img[..., 2] = np.roll(img[..., 2], -ca, axis=1)

    # färggradering: teal skuggor, orange högdagrar
    lum = img.mean(axis=2, keepdims=True)
    img = img + (1 - np.clip(lum * 3, 0, 1)) * np.array([0.0, 0.012, 0.02], np.float32)
    img = img * A.vig * A.scan
    gr = A.grain[fi % len(A.grain)]
    gr = np.repeat(np.repeat(gr, 2, 0), 2, 1)[..., None]
    img = img + gr * 0.03

    # tonmappning
    img = 1 - np.exp(-img * 1.6)
    img = img / (1 - math.exp(-1.6))
    return (np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        init()
        for a in sys.argv[sys.argv.index("--preview") + 1:]:
            t = float(a)
            fr = np.frombuffer(render(int(t * FPS)), np.uint8).reshape(H, W, 3)
            p = os.path.join(OUT, f"preview_{t}.png")
            Image.fromarray(fr).save(p)
            print(p)
        return
    n = int(TL.DURATION * FPS)
    dst = os.path.join(OUT, "video_only.mp4")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", dst,
    ], stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init) as pool:
        for i, fr in enumerate(pool.imap(render, range(n), chunksize=4)):
            ff.stdin.write(fr)
            if i % 60 == 0:
                print(f"  bildruta {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print(dst)


if __name__ == "__main__":
    main()
