/**
 * Tema "sandlada": en solig lekpark ovanifrån. Rollerna är runda figurer med
 * googlyögon och en bokstav på magen, pratbubblor, ett serietidningsmoln när
 * det blir bråk och en räknare som ser ut som en arbetsplatsskylt.
 *
 * Scentyper: rubrik, intro, prat, brak, rostning, kor, slut.
 * Gemensamt för alla scener: "texter", "raknare", "ljud" (egna ljudeffekter),
 * "musik" (lekplats-musikens läge, se motor/ljud.py).
 */
(function () {
  const M = window.Motor;
  const W = M.W, H = M.H;
  const LINJE = '#2a1d14';
  const FONT = 'Fredoka';
  const f = (vikt, px) => `${vikt} ${px}px '${FONT}'`;

  const T = {
    typsnitt: [f(700, 60), f(600, 30), "700 50px 'Display'", "700 22px 'Display'"],
  };
  M.teman.sandlada = T;

  let BG = null;        // förrenderad bakgrund
  let ROLLER = {};      // id -> roll
  let ORDNING = [];

  // ---------------------------------------------------------------- förberedelse
  T.forbered = manus => {
    ROLLER = manus.roller;
    ORDNING = Object.keys(ROLLER).filter(k => ROLLER[k].typ !== 'talman');
    BG = document.createElement('canvas');
    BG.width = W; BG.height = H;
    ritaBakgrund(BG.getContext('2d'));
  };

  const LADA = { x0: 26, y0: 540, x1: 1054, y1: 1250, k: 40 };

  function ritaBakgrund(c) {
    const r = M.slump(11);
    // gräs
    c.fillStyle = '#6cbf5b';
    c.fillRect(0, 0, W, H);
    for (let i = 0; i < 2600; i++) {
      const x = r() * W, y = r() * H;
      c.strokeStyle = r() < 0.5 ? '#5aa94b' : '#7fcd6b';
      c.lineWidth = 3;
      c.beginPath(); c.moveTo(x, y); c.lineTo(x + (r() - 0.5) * 8, y - 10 - r() * 10); c.stroke();
    }
    // blommor
    for (let i = 0; i < 40; i++) {
      const x = r() * W, y = r() < 0.5 ? r() * 520 : 1260 + r() * 660;
      const col = ['#fff', '#ffd23f', '#ff7eb6'][Math.floor(r() * 3)];
      for (let k = 0; k < 5; k++) {
        const a = k / 5 * Math.PI * 2;
        c.fillStyle = col;
        c.beginPath(); c.arc(x + Math.cos(a) * 7, y + Math.sin(a) * 7, 6, 0, 7); c.fill();
      }
      c.fillStyle = '#f7a400'; c.beginPath(); c.arc(x, y, 5, 0, 7); c.fill();
    }
    // sandlådans skugga + ram
    const { x0, y0, x1, y1, k } = LADA;
    c.fillStyle = 'rgba(0,0,0,0.18)';
    rundRekt(c, x0 + 10, y0 + 16, x1 - x0, y1 - y0, 18); c.fill();
    c.fillStyle = '#b8773d';
    rundRekt(c, x0, y0, x1 - x0, y1 - y0, 18); c.fill();
    c.lineWidth = 6; c.strokeStyle = LINJE; c.stroke();
    // plankfogar
    c.strokeStyle = 'rgba(60,30,10,0.55)'; c.lineWidth = 3;
    for (let x = x0 + 120; x < x1 - 40; x += 170) { c.beginPath(); c.moveTo(x, y0 + 4); c.lineTo(x, y0 + k - 4); c.moveTo(x + 60, y1 - k + 4); c.lineTo(x + 60, y1 - 4); c.stroke(); }
    for (let y = y0 + 140; y < y1 - 40; y += 190) { c.beginPath(); c.moveTo(x0 + 4, y); c.lineTo(x0 + k - 4, y); c.moveTo(x1 - k + 4, y + 70); c.lineTo(x1 - 4, y + 70); c.stroke(); }
    // sand
    c.fillStyle = '#f2d59b';
    rundRekt(c, x0 + k, y0 + k, x1 - x0 - 2 * k, y1 - y0 - 2 * k, 8); c.fill();
    c.lineWidth = 5; c.strokeStyle = 'rgba(42,29,20,0.6)'; c.stroke();
    c.save();
    rundRekt(c, x0 + k, y0 + k, x1 - x0 - 2 * k, y1 - y0 - 2 * k, 8); c.clip();
    for (let i = 0; i < 5000; i++) {
      c.fillStyle = r() < 0.5 ? 'rgba(190,150,90,0.35)' : 'rgba(255,240,200,0.5)';
      c.fillRect(x0 + r() * (x1 - x0), y0 + r() * (y1 - y0), 3, 3);
    }
    // krattspår
    c.strokeStyle = 'rgba(180,140,80,0.35)'; c.lineWidth = 4;
    for (let i = 0; i < 14; i++) {
      const yy = y0 + 80 + i * 46;
      c.beginPath();
      for (let x = x0 + 40; x < x1 - 40; x += 20) c.lineTo(x, yy + Math.sin(x / 60 + i) * 6);
      c.stroke();
    }
    c.restore();
    // leksaker: hink och spade
    hink(c, 930, 1150, '#ff5a5f');
    spade(c, 120, 1170, '#3aa0ff', -0.5);
    // träd i hörnet
    c.fillStyle = 'rgba(0,0,0,0.15)'; c.beginPath(); c.arc(150, 470, 150, 0, 7); c.fill();
    for (const [dx, dy, rr, col] of [[0, 0, 140, '#3f9a45'], [-60, -40, 90, '#4fae52'], [50, -70, 80, '#4fae52'], [30, 40, 70, '#57b85a']]) {
      c.fillStyle = col; c.beginPath(); c.arc(120 + dx, 420 + dy, rr, 0, 7); c.fill();
      c.lineWidth = 5; c.strokeStyle = 'rgba(42,29,20,0.5)'; c.stroke();
    }
  }

  function rundRekt(c, x, y, w, h, r) {
    c.beginPath();
    c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r);
    c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r);
    c.arcTo(x, y, x + w, y, r);
    c.closePath();
  }

  function hink(c, x, y, col) {
    c.save(); c.translate(x, y);
    c.fillStyle = 'rgba(0,0,0,0.18)'; c.beginPath(); c.ellipse(6, 50, 52, 16, 0, 0, 7); c.fill();
    c.fillStyle = col; c.strokeStyle = LINJE; c.lineWidth = 5;
    c.beginPath(); c.moveTo(-40, -30); c.lineTo(40, -30); c.lineTo(30, 45); c.lineTo(-30, 45); c.closePath(); c.fill(); c.stroke();
    c.beginPath(); c.ellipse(0, -30, 40, 12, 0, 0, 7); c.fillStyle = '#c84448'; c.fill(); c.stroke();
    c.beginPath(); c.arc(0, -30, 44, Math.PI, 0); c.lineWidth = 4; c.stroke();
    c.restore();
  }

  function spade(c, x, y, col, rot) {
    c.save(); c.translate(x, y); c.rotate(rot);
    c.strokeStyle = LINJE; c.lineWidth = 5;
    c.fillStyle = '#f4b942'; c.fillRect(-6, -90, 12, 80); c.strokeRect(-6, -90, 12, 80);
    c.fillStyle = col;
    c.beginPath(); c.moveTo(-28, -12); c.lineTo(28, -12); c.quadraticCurveTo(30, 40, 0, 52); c.quadraticCurveTo(-30, 40, -28, -12); c.fill(); c.stroke();
    c.restore();
  }

  // ---------------------------------------------------------------- figurerna
  /**
   * Ritar en figur. st: {x, y, r, farg, text, textFarg, squash, titta:[dx,dy],
   * mun (0..1 = öppen), humor, blink, skaka, talman, klubba}
   */
  function figur(c, st) {
    const { x, y, r } = st;
    const sq = st.squash || 0;
    c.save();
    c.translate(x + (st.skaka ? (M.hash(st.t, x) - 0.5) * st.skaka : 0), y);
    // skugga
    c.fillStyle = 'rgba(0,0,0,0.2)';
    c.beginPath(); c.ellipse(0, r * 1.0 - (st.lyft || 0) * 0 + 6, r * 0.9, r * 0.25, 0, 0, 7); c.fill();
    c.translate(0, -(st.lyft || 0));
    // fötter
    const steg = st.gar ? Math.sin(st.t * 22) * 10 : 0;
    c.fillStyle = LINJE;
    c.beginPath(); c.ellipse(-r * 0.38, r * 0.92 + steg, r * 0.26, r * 0.14, 0, 0, 7); c.fill();
    c.beginPath(); c.ellipse(r * 0.38, r * 0.92 - steg, r * 0.26, r * 0.14, 0, 0, 7); c.fill();
    // kropp
    const rx = r * (1 + sq), ry = r * (1 - sq);
    c.fillStyle = st.farg;
    c.beginPath(); c.ellipse(0, sq * r * 0.6, rx, ry, 0, 0, 7); c.fill();
    if (st.humor === 'arg') { c.fillStyle = 'rgba(255,0,0,0.18)'; c.fill(); }
    c.lineWidth = 7; c.strokeStyle = LINJE; c.stroke();
    // glans
    c.fillStyle = 'rgba(255,255,255,0.35)';
    c.beginPath(); c.ellipse(-rx * 0.45, -ry * 0.5, rx * 0.22, ry * 0.14, -0.6, 0, 7); c.fill();
    // text på magen
    if (st.text) {
      const fs = r * (st.text.length > 3 ? 0.24 : st.text.length > 1 ? 0.5 : 0.62);
      c.font = f(700, fs);
      c.textAlign = 'center'; c.textBaseline = 'middle';
      c.lineWidth = Math.max(4, fs * 0.16); c.strokeStyle = LINJE; c.lineJoin = 'round';
      c.strokeText(st.text, 0, r * 0.5);
      c.fillStyle = st.textFarg || '#fff';
      c.fillText(st.text, 0, r * 0.5);
    }
    // ögon
    const chock = st.humor === 'chock';
    const er = r * (chock ? 0.27 : 0.22);
    const ey = -r * 0.3;
    const [tx, ty] = st.titta || [0, 0];
    const blink = st.blink;
    for (const s of [-1, 1]) {
      const ex = s * r * 0.33;
      c.fillStyle = '#fff'; c.strokeStyle = LINJE; c.lineWidth = 5;
      if (blink) {
        c.beginPath(); c.moveTo(ex - er, ey); c.lineTo(ex + er, ey); c.lineWidth = 6; c.stroke();
      } else {
        c.beginPath(); c.arc(ex, ey, er, 0, 7); c.fill(); c.stroke();
        const pr = er * (chock ? 0.32 : 0.5);
        c.fillStyle = '#111';
        c.beginPath(); c.arc(ex + tx * er * 0.42, ey + ty * er * 0.42, pr, 0, 7); c.fill();
        c.fillStyle = '#fff';
        c.beginPath(); c.arc(ex + tx * er * 0.42 - pr * 0.35, ey + ty * er * 0.42 - pr * 0.35, pr * 0.3, 0, 7); c.fill();
      }
      if (st.talman) { // glasögon
        c.strokeStyle = LINJE; c.lineWidth = 4;
        c.beginPath(); c.arc(ex, ey, er + 7, 0, 7); c.stroke();
      }
      // ögonbryn
      const h = st.humor;
      if (h === 'arg' || h === 'sur' || h === 'ledsen' || chock) {
        c.strokeStyle = LINJE; c.lineWidth = 8; c.lineCap = 'round';
        const by = ey - er - 10 - (chock ? 10 : 0);
        // inre änden (mot näsan) och yttre änden, uppåt är minus
        const [inre, yttre] = h === 'arg' ? [12, -10] : h === 'ledsen' ? [-12, 6] : h === 'sur' ? [6, 2] : [-6, -6];
        c.beginPath();
        c.moveTo(ex - s * er * 0.9, by + inre);
        c.lineTo(ex + s * er * 0.9, by + yttre);
        c.stroke();
      }
    }
    if (st.talman) { c.beginPath(); c.moveTo(-r * 0.12, ey); c.lineTo(r * 0.12, ey); c.stroke(); }
    // mun
    const my = r * 0.05;
    c.strokeStyle = LINJE; c.lineWidth = 6; c.lineCap = 'round';
    if (st.mun > 0.05 || chock) {
      const oh = chock ? r * 0.16 : r * 0.05 + st.mun * r * 0.14;
      c.fillStyle = '#5a1010';
      c.beginPath(); c.ellipse(0, my + oh * 0.3, chock ? r * 0.11 : r * 0.17, oh, 0, 0, 7); c.fill(); c.stroke();
    } else {
      const h = st.humor;
      c.beginPath();
      if (h === 'glad' || !h || h === 'normal') c.arc(0, my - r * 0.06, r * (h === 'glad' ? 0.2 : 0.12), 0.2, Math.PI - 0.2);
      else if (h === 'sur') { c.moveTo(-r * 0.12, my + 4); c.lineTo(r * 0.12, my); }
      else c.arc(0, my + r * 0.14, r * 0.13, Math.PI + 0.3, -0.3);
      c.stroke();
    }
    if (st.talman) {
      // fluga
      c.fillStyle = '#111';
      c.beginPath(); c.moveTo(0, r * 0.3); c.lineTo(-24, r * 0.2); c.lineTo(-24, r * 0.42); c.closePath(); c.fill();
      c.beginPath(); c.moveTo(0, r * 0.3); c.lineTo(24, r * 0.2); c.lineTo(24, r * 0.42); c.closePath(); c.fill();
      // klubba
      c.save();
      c.translate(r * 0.95, -r * 0.05);
      c.rotate(st.klubba || -1.1);
      c.fillStyle = '#8a5a2b'; c.strokeStyle = LINJE; c.lineWidth = 5;
      c.fillRect(-7, -100, 14, 100); c.strokeRect(-7, -100, 14, 100);
      c.fillStyle = '#6b3f17';
      rundRekt(c, -42, -128, 84, 40, 8); c.fill(); c.stroke();
      c.restore();
    }
    c.restore();
  }

  // ---------------------------------------------------------------- pratbubblor
  function bubbla(c, text, sx, sy, k, opts = {}) {
    if (k <= 0) return;
    const fs = opts.storlek || 52;
    c.save();
    c.font = f(700, fs);
    const rader = M.radbryt(c, text, opts.maxw || 600);
    const w = Math.max(...rader.map(r => c.measureText(r).width)) + 64;
    const h = rader.length * fs * 1.12 + 44;
    let bx = M.clamp(sx - w / 2, 36, (opts.hoger || 1044) - w);
    const by = opts.y != null ? opts.y : sy - h - 34;
    const cx = bx + w / 2, cy = by + h / 2;
    c.translate(cx, by + h);
    c.scale(k, k);
    c.translate(-cx, -(by + h));
    c.globalAlpha = Math.min(1, k * 1.4);
    c.fillStyle = opts.farg || '#fff';
    c.strokeStyle = LINJE; c.lineWidth = 6; c.lineJoin = 'round';
    rundRekt(c, bx, by, w, h, 34);
    c.fill(); c.stroke();
    // svans
    if (!opts.utanSvans) {
      const tx = M.clamp(sx, bx + 40, bx + w - 40);
      c.beginPath();
      c.moveTo(tx - 22, by + h - 3); c.lineTo(sx + (sx - tx) * 0.2, sy - 6); c.lineTo(tx + 22, by + h - 3);
      c.fill(); c.stroke();
      c.fillRect(tx - 19, by + h - 9, 38, 8);
    }
    c.fillStyle = opts.textFarg || '#1c1410';
    c.textAlign = 'center'; c.textBaseline = 'middle';
    rader.forEach((r, i) => c.fillText(r, cx, by + 22 + fs * 0.56 + i * fs * 1.12));
    c.restore();
    void cy;
  }

  // ---------------------------------------------------------------- skylten (räknaren)
  function skylt(c, x, y, skala, t) {
    const v = M.raknare(t);
    if (v == null) return;
    const etikett = M.manus.raknareEtikett || 'ANTAL DAGAR UTAN REGERING';
    const forr = M.raknare(Math.max(0, t - 0.07));
    const sv = String(v).padStart(4, '0').slice(-4), sf = String(forr).padStart(4, '0').slice(-4);
    c.save();
    c.translate(x, y); c.scale(skala, skala);
    c.rotate(-0.025);
    c.fillStyle = 'rgba(0,0,0,0.25)'; rundRekt(c, 10, 14, 620, 236, 22); c.fill();
    // stolpar
    c.fillStyle = '#9aa0a6'; c.strokeStyle = LINJE; c.lineWidth = 5;
    c.fillRect(120, 236, 18, 60); c.strokeRect(120, 236, 18, 60);
    c.fillRect(482, 236, 18, 60); c.strokeRect(482, 236, 18, 60);
    c.fillStyle = '#fdfdf6'; rundRekt(c, 0, 0, 620, 240, 22); c.fill();
    c.lineWidth = 7; c.stroke();
    c.fillStyle = '#1f8a3b'; rundRekt(c, 14, 14, 592, 62, 12); c.fill();
    c.fillStyle = '#fff'; c.font = f(600, 32); c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText(etikett, 310, 46);
    for (let i = 0; i < 4; i++) {
      const bx = 82 + i * 118, byy = 92;
      c.fillStyle = '#23272b'; rundRekt(c, bx, byy, 100, 132, 12); c.fill();
      c.strokeStyle = '#000'; c.lineWidth = 4; c.stroke();
      const flip = sv[i] !== sf[i];
      c.save();
      c.translate(bx + 50, byy + 66);
      if (flip) c.scale(1, 0.35);
      c.fillStyle = '#fff'; c.font = f(700, 110);
      c.fillText(sv[i], 0, 6);
      c.restore();
      c.strokeStyle = 'rgba(0,0,0,0.55)'; c.lineWidth = 3;
      c.beginPath(); c.moveTo(bx + 4, byy + 66); c.lineTo(bx + 96, byy + 66); c.stroke();
    }
    c.restore();
  }

  // ---------------------------------------------------------------- texter
  function undertexter(c, t) {
    for (const x of M.manus.texter) {
      if (t < x.fran || t >= x.till) continue;
      const k = M.fonster(t, x.fran, x.till, 0.18, 0.18);
      const stor = x.stil === 'stor', liten = x.stil === 'liten';
      const fs = stor ? 84 : liten ? 46 : 64;
      const y0 = x.y || (liten ? 1462 : 1300);
      c.save();
      c.font = f(700, fs);
      c.textAlign = 'center'; c.textBaseline = 'middle';
      c.lineJoin = 'round';
      const rader = M.radbryt(c, x.text, 900);
      const sk = 0.85 + 0.15 * M.studs((t - x.fran) / 0.3);
      c.globalAlpha = k;
      rader.forEach((r, i) => {
        const yy = y0 + i * fs * 1.12;
        c.save(); c.translate(540, yy); c.scale(sk, sk);
        c.lineWidth = fs * 0.24; c.strokeStyle = LINJE; c.strokeText(r, 0, 0);
        c.fillStyle = liten ? '#ffe45c' : '#fff'; c.fillText(r, 0, 0);
        c.restore();
      });
      c.restore();
    }
  }

  // ---------------------------------------------------------------- figurernas lägen
  const aktiva = t => M.manus.repliker.filter(r => t >= r.start && t < r.slut);
  const senasteTalare = (t, s) => {
    let best = null;
    for (const r of M.manus.repliker) if (r.scen === s && r.start <= t && (!best || r.start > best.start)) best = r;
    return best;
  };

  function basLage(id, t) {
    const R = ROLLER[id];
    const i = ORDNING.indexOf(id);
    const bl = ((t * 1000 + i * 1777) % 3700) < 120;
    return {
      id, t, x: R.plats[0], y: R.plats[1], r: R.r || 78, farg: R.farg, text: R.text ?? id, textFarg: R.textFarg,
      squash: 0.035 * Math.sin(t * 3.2 + i), titta: [0, 0.2], mun: 0, humor: R.humor || 'normal', blink: bl,
      talman: R.typ === 'talman',
    };
  }

  function rikta(st, mal) {
    const dx = mal[0] - st.x, dy = mal[1] - st.y, d = Math.hypot(dx, dy) || 1;
    st.titta = [dx / d, dy / d];
  }

  /** Talar-effekter: hopp, mun, humör, blick. */
  function talarLage(st, t, s) {
    for (const r of aktiva(t)) {
      if (r.vem !== st.id && !(r.vem === 'ALLA' && !st.talman)) continue;
      const u = t - r.start;
      if (r.hopp !== false) st.lyft = Math.max(st.lyft || 0, 46 * Math.sin(Math.PI * M.clamp(u / 0.32)));
      st.squash += u < 0.32 ? -0.08 * Math.sin(Math.PI * u / 0.32) : 0;
      const pratLen = (r.slut - r.start) * 0.8;
      st.mun = u < pratLen ? 0.5 + 0.5 * Math.sin(u * 30) : 0;
      if (r.humor) st.humor = r.humor;
      if (r.titta && ROLLER[r.titta]) rikta(st, ROLLER[r.titta].plats);
      else if (r.titta === 'kamera') st.titta = [0, 0.1];
      st.skaka = r.humor === 'arg' ? 6 : 0;
      st.talar = true;
    }
    return st;
  }

  // ---------------------------------------------------------------- kameran
  function kamera(c, t) {
    let z = 1, fx = 540, fy = 900;
    for (const r of M.manus.repliker) {
      if (!r.zoom || t < r.start - 0.1 || t > r.slut + 0.3) continue;
      const k = M.fonster(t, r.start - 0.1, r.slut + 0.3, 0.15, 0.3);
      const R = ROLLER[r.vem];
      if (!R) continue;
      z = 1 + (r.zoom === true ? 0.22 : r.zoom) * k;
      fx = 540 + (R.plats[0] - 540) * k;
      fy = 900 + (R.plats[1] - 120 - 900) * k;
    }
    // håll bildutsnittet inom bakgrunden, annars syns svarta kanter
    fx = M.clamp(fx, 540 / z, W - 540 / z);
    fy = M.clamp(fy, 900 / z, H - (H - 900) / z);
    c.translate(540, 900); c.scale(z, z); c.translate(-fx, -fy);
  }

  // ---------------------------------------------------------------- scenerna
  const scen = {};

  scen.rubrik = (c, t, s, lt) => {
    for (const [a, text, storlek] of s.rader || []) {
      if (lt < a) continue;
      const u = lt - a;
      const k = M.studs(u / 0.35);
      const i = s.rader.findIndex(x => x[1] === text);
      const y = (s.y || 760) + i * 150;
      c.save();
      c.translate(540, y); c.rotate((i % 2 ? 2.5 : -2.5) * Math.PI / 180); c.scale(k, k);
      c.font = f(700, storlek || 100);
      c.textAlign = 'center'; c.textBaseline = 'middle'; c.lineJoin = 'round';
      c.lineWidth = 22; c.strokeStyle = LINJE; c.strokeText(text, 0, 0);
      c.fillStyle = i % 2 ? '#ffe45c' : '#fff'; c.fillText(text, 0, 0);
      c.restore();
    }
  };

  /** Figurerna springer in en i taget. */
  function introLage(id, t, s, lt) {
    const st = basLage(id, t);
    const i = ORDNING.indexOf(id);
    const t0 = (s.forsening || 0.25) + i * (s.mellanrum || 0.5);
    const u = (lt - t0) / 0.55;
    if (u < 0) return null;
    if (u < 1) {
      const fran = st.x < 540 ? -120 : W + 120;
      st.x = fran + (st.x - fran) * M.smooth(u);
      st.lyft = Math.abs(Math.sin(u * Math.PI * 3)) * 40;
      st.gar = true;
      st.titta = [st.x < st.x + 1 ? (fran < 0 ? 1 : -1) : 0, 0];
    } else {
      const v = lt - t0 - 0.55;
      st.squash += v < 0.2 ? 0.18 * Math.sin(Math.PI * v / 0.2) : 0;
      st.titta = [0, 0.3];
    }
    return st;
  }

  function figurerVid(t, s, lt) {
    const ut = [];
    const tal = senasteTalare(t, s);
    for (const id of ORDNING) {
      let st;
      if (s.typ === 'intro') st = introLage(id, t, s, lt);
      else st = basLage(id, t);
      if (!st) continue;
      if (s.typ === 'kor') {
        const i = s.rad ? s.rad.indexOf(id) : ORDNING.indexOf(id);
        st.x = 100 + i * 126; st.y = s.radY || 900; st.r = (ROLLER[id].r || 78) * 0.8;
      }
      if (s.humor && s.humor[id]) st.humor = s.humor[id];
      else if (s.allaHumor) st.humor = s.allaHumor;
      for (const [ht, hum] of s.humorVid || []) if (lt >= ht) st.humor = hum;
      if (tal && !tal.ignoreras && tal.vem !== id && ROLLER[tal.vem]) rikta(st, [ROLLER[tal.vem].plats[0], ROLLER[tal.vem].plats[1]]);
      if (s.typ === 'rostning' && ROLLER.TM) rikta(st, ROLLER.TM.plats);
      if (s.titta && s.titta[id]) { const m = s.titta[id]; st.titta = Array.isArray(m) ? m : [0, 0]; }
      talarLage(st, t, s);
      ut.push(st);
    }
    return ut;
  }

  function ritaFigurer(c, list) {
    list.sort((a, b) => a.y - b.y).forEach(st => figur(c, st));
  }

  function ritaBubblor(c, t, s) {
    for (const r of aktiva(t)) {
      if (r.scen !== s || r.vem === 'ALLA' || s.typ === 'brak') continue;
      const R = ROLLER[r.vem];
      if (!R) continue;
      const u = t - r.start, kvar = r.slut - t;
      const k = M.studs(u / 0.22) * M.clamp(kvar / 0.15);
      let [sx, sy] = R.plats;
      if (s.typ === 'kor') { const i = (s.rad || ORDNING).indexOf(r.vem); sx = 100 + i * 126; sy = s.radY || 900; }
      bubbla(c, r.text, sx, sy - (R.r || 78) - 10, k, { storlek: r.storlek || (R.typ === 'talman' ? 46 : 52) });
    }
  }

  scen.intro = (c, t, s, lt) => { ritaFigurer(c, figurerVid(t, s, lt)); ritaBubblor(c, t, s); };
  scen.prat = scen.intro;

  scen.rostning = (c, t, s, lt) => {
    const list = figurerVid(t, s, lt);
    // talmannen
    const TM = ROLLER.TM;
    if (TM) {
      const st = basLage('TM', t);
      st.r = TM.r || 100; st.talman = true; st.text = TM.text || 'TALMAN';
      const inne = M.clamp((lt - 0.0) / 0.5);
      st.y = TM.plats[1] - (1 - M.smooth(inne)) * 700;
      // klubban: lyft och slag inför varje stämpel
      let vinkel = -1.15;
      for (const sp of s.stamplar || []) {
        const d = lt - sp.t;
        if (d > -0.3 && d < 0) vinkel = -1.15 - 0.6 * M.smooth((d + 0.3) / 0.22);
        if (d >= 0 && d < 0.25) vinkel = 0.35 - 1.5 * M.smooth(d / 0.25);
        if (d >= 0 && d < 0.12) st.squash += 0.12;
      }
      st.klubba = vinkel;
      st.titta = [0, 0.3];
      talarLage(st, t, s);
      list.push(st);
    }
    ritaFigurer(c, list);
    // stämplar
    (s.stamplar || []).forEach((sp, i) => {
      const d = lt - sp.t;
      if (d < 0) return;
      const k = 1 + 1.6 * (1 - M.smooth(d / 0.14));
      if (sp.banderoll) {
        const sh = d < 0.5 ? (M.hash(t) - 0.5) * 18 : 0;
        c.save(); c.translate(540 + sh, 1000); c.rotate(-0.06); c.scale(k * 0.9 + 0.1, k * 0.9 + 0.1);
        c.fillStyle = '#ffe45c'; c.strokeStyle = LINJE; c.lineWidth = 9;
        rundRekt(c, -470, -110, 940, 220, 26); c.fill(); c.stroke();
        c.font = f(700, 130); c.textAlign = 'center'; c.textBaseline = 'middle';
        c.fillStyle = '#e8112d'; c.fillText(sp.text, 0, 8);
        c.restore();
        return;
      }
      const pos = [[330, 990, -0.2], [720, 1050, 0.16], [470, 1150, -0.07], [640, 940, 0.1]][i % 4];
      c.save();
      c.translate(pos[0], pos[1]); c.rotate(pos[2]); c.scale(k, k);
      c.globalAlpha = 0.92;
      c.strokeStyle = '#d0021b'; c.lineWidth = 12;
      rundRekt(c, -170, -78, 340, 156, 18); c.stroke();
      c.lineWidth = 4; rundRekt(c, -156, -64, 312, 128, 12); c.stroke();
      c.fillStyle = '#d0021b'; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.font = f(600, 30); c.fillText(sp.rubrik || '', 0, -38);
      c.font = f(700, 92); c.fillText(sp.text || 'NEJ', 0, 18);
      c.restore();
    });
    ritaBubblor(c, t, s);
  };

  scen.kor = (c, t, s, lt) => {
    const list = figurerVid(t, s, lt);
    ritaFigurer(c, list);
    ritaBubblor(c, t, s);
    for (const r of aktiva(t)) {
      if (r.scen !== s || r.vem !== 'ALLA') continue;
      const u = t - r.start, kvar = r.slut - t;
      const k = M.studs(u / 0.25) * M.clamp(kvar / 0.15);
      bubbla(c, r.text, 540, (s.radY || 900) - 120, k, { storlek: r.storlek || 78, maxw: 860, farg: '#ffe45c' });
    }
  };

  scen.brak = (c, t, s, lt) => {
    const mitt = [540, 930];
    const samlas = M.smooth(lt / 0.45);
    const list = figurerVid(t, s, lt).map(st => {
      st.x += (mitt[0] - st.x) * samlas; st.y += (mitt[1] - st.y) * samlas;
      st.humor = 'arg'; st.skaka = 10;
      return st;
    });
    if (lt < 0.45) { ritaFigurer(c, list); }
    const k = M.smooth((lt - 0.3) / 0.2) * (1 - M.smooth((lt - s.len + 0.25) / 0.25));
    if (k <= 0) return;
    const steg = Math.floor(t * 12);
    const r = M.slump(steg * 97 + 3);
    // sand som yr
    for (let i = 0; i < 70; i++) {
      const a = r() * Math.PI * 2, d = 200 + r() * 330;
      c.fillStyle = r() < 0.5 ? '#e3b96d' : '#c99a4e';
      c.beginPath(); c.arc(mitt[0] + Math.cos(a) * d, mitt[1] + Math.sin(a) * d * 0.8, 4 + r() * 8, 0, 7); c.fill();
    }
    c.save();
    c.translate(mitt[0], mitt[1]); c.scale(k, k);
    // armar/ben och figurdelar som sticker ut
    for (let i = 0; i < 9; i++) {
      const a = r() * Math.PI * 2;
      const id = ORDNING[Math.floor(r() * ORDNING.length)];
      const R = ROLLER[id];
      const d = 250;
      c.save();
      c.translate(Math.cos(a) * d, Math.sin(a) * d * 0.8);
      c.rotate(a + Math.PI / 2);
      if (r() < 0.5) {
        c.fillStyle = LINJE; c.beginPath(); c.ellipse(0, 0, 22, 34, 0, 0, 7); c.fill();
      } else {
        figur(c, { x: 0, y: 0, r: 46, farg: R.farg, text: R.text ?? id, textFarg: R.textFarg, humor: 'arg', titta: [0, -1], mun: 0.8, t });
      }
      c.restore();
    }
    // själva molnet
    c.strokeStyle = LINJE; c.lineWidth = 8;
    const moln = [];
    for (let i = 0; i < 16; i++) {
      const a = i / 16 * Math.PI * 2 + r() * 0.3;
      moln.push([Math.cos(a) * (150 + r() * 40), Math.sin(a) * (120 + r() * 40), 90 + r() * 40]);
    }
    for (const [x, y, rr] of moln) { c.beginPath(); c.arc(x, y, rr, 0, 7); c.stroke(); }
    c.fillStyle = '#f7efe0';
    for (const [x, y, rr] of moln) { c.beginPath(); c.arc(x, y, rr, 0, 7); c.fill(); }
    c.beginPath(); c.ellipse(0, 0, 200, 170, 0, 0, 7); c.fill();
    // stjärnor och snurr i molnet
    for (let i = 0; i < 6; i++) {
      const x = (r() - 0.5) * 300, y = (r() - 0.5) * 220;
      stjarna(c, x, y, 26 + r() * 18, '#ffd23f', r() * 6);
    }
    c.restore();
    // serieord: POW! BONK!
    for (const [a, ord] of s.ljudord || []) {
      const d = lt - a;
      if (d < 0 || d > 0.6) continue;
      const kk = M.studs(d / 0.15) * (1 - M.smooth((d - 0.45) / 0.15));
      const rr = M.slump(Math.floor(a * 100));
      const x = 200 + rr() * 680, y = 640 + rr() * 560;
      c.save(); c.translate(x, y); c.rotate((rr() - 0.5) * 0.6); c.scale(kk, kk);
      stjarna(c, 0, 0, 150, '#ffe45c', 0, 14);
      c.font = f(700, 72); c.textAlign = 'center'; c.textBaseline = 'middle';
      c.lineWidth = 10; c.strokeStyle = LINJE; c.lineJoin = 'round';
      c.strokeText(ord, 0, 4); c.fillStyle = '#e8112d'; c.fillText(ord, 0, 4);
      c.restore();
    }
    // repliker ur molnet
    aktiva(t).filter(rp => rp.scen === s).forEach((rp, i) => {
      const u = t - rp.start, kvar = rp.slut - t;
      const kk = M.studs(u / 0.2) * M.clamp(kvar / 0.12);
      const vinkel = [-2.3, -0.8, -1.6, -2.7, -0.4][M.manus.repliker.indexOf(rp) % 5];
      const bx = mitt[0] + Math.cos(vinkel) * 330, by = mitt[1] + Math.sin(vinkel) * 300;
      bubbla(c, rp.text, bx, by, kk, { storlek: 46, maxw: 460 });
      void i;
    });
  };

  function stjarna(c, x, y, r, col, rot = 0, spetsar = 5) {
    c.save(); c.translate(x, y); c.rotate(rot);
    c.beginPath();
    for (let i = 0; i < spetsar * 2; i++) {
      const rr = i % 2 ? r * 0.55 : r;
      const a = i / (spetsar * 2) * Math.PI * 2 - Math.PI / 2;
      c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    c.closePath();
    c.fillStyle = col; c.fill();
    c.strokeStyle = LINJE; c.lineWidth = 6; c.lineJoin = 'round'; c.stroke();
    c.restore();
  }

  scen.slut = (c, t, s, lt) => {
    const list = figurerVid(t, s, lt);
    ritaFigurer(c, list);
    ritaBubblor(c, t, s);
  };

  // ---------------------------------------------------------------- huvudritning
  T.rita = (c, t, s, lt) => {
    c.save();
    kamera(c, t);
    c.drawImage(BG, 0, 0);
    (scen[s.typ] || scen.prat)(c, t, s, lt);
    c.restore();
    // skylten: uppe till vänster, i slutet mitt i bild
    if (s.typ === 'slut') {
      const u = M.smooth(lt / 0.6);
      c.fillStyle = `rgba(20,12,6,${0.45 * u})`; c.fillRect(0, 0, W, H);
      skylt(c, 56 + (540 - 56 - 0.5 * 620 * 1.45) * u, 180 + (600 - 180) * u, 1 + 0.45 * u, t);
    } else if (!s.raknareDold) {
      skylt(c, 56, 180, 1, t);
    }
    undertexter(c, t);
    M.logga(c, { morkt: false });
  };

  // ---------------------------------------------------------------- ljudhändelser
  const vokaler = txt => Math.max(2, (txt.match(/[aeiouyåäöAEIOUYÅÄÖ]/g) || []).length);

  T.handelser = manus => {
    const ut = [];
    for (const s of manus.scener) {
      if (s.typ === 'rubrik') for (const [a] of s.rader || []) ut.push({ t: s.start + a, ljud: 'smack' });
      if (s.typ === 'intro') {
        ORDNING.forEach((id, i) => {
          const t0 = s.start + (s.forsening || 0.25) + i * (s.mellanrum || 0.5);
          ut.push({ t: t0, ljud: 'spring', len: 0.5 });
          ut.push({ t: t0 + 0.55, ljud: 'pop', ton: 1 + i * 0.08 });
        });
      }
      if (s.typ === 'brak') for (const [a] of s.ljudord || []) ut.push({ t: s.start + a, ljud: 'smack' });
      if (s.typ === 'rostning') {
        ut.push({ t: s.start + 0.1, ljud: 'fall' });
        for (const sp of s.stamplar || []) {
          ut.push({ t: s.start + sp.t, ljud: sp.banderoll ? 'gong' : 'klubba' });
          if (!sp.banderoll) ut.push({ t: s.start + sp.t + 0.02, ljud: 'stampel' });
        }
      }
      for (const [a, ljud, extra] of s.ljud || []) ut.push({ t: s.start + a, ljud, ...(extra || {}) });
    }
    for (const r of manus.repliker) {
      const R = manus.roller[r.vem];
      if (r.vem === 'ALLA') { ut.push({ t: r.start, ljud: 'skrik', len: (r.slut - r.start) * 0.7 }); continue; }
      if (r.hopp !== false) ut.push({ t: r.start, ljud: 'boing', ton: R ? (R.rost || 220) / 220 : 1 });
      ut.push({ t: r.start + 0.05, ljud: 'prat', len: (r.slut - r.start) * 0.8, rost: R ? R.rost || 220 : 220, stavelser: vokaler(r.text), seed: Math.floor(r.start * 100) });
    }
    // räknaren: ett klick per ändring (glest när den rusar)
    let sist = -1, sistV = null;
    for (let t = 0; t < manus.total; t += 1 / 30) {
      const v = M.raknare(t);
      if (v !== sistV && sistV !== null && t - sist > 0.06) { ut.push({ t, ljud: 'tick' }); sist = t; }
      sistV = v;
    }
    return ut;
  };
})();
