/**
 * Filmmotorn. En film = ett manus (JSON) + ett tema (teman/*.js).
 *
 * Hela filmen är en funktion av tiden: render(t) ritar bildrutan vid t
 * sekunder. Därför går den både att spela upp i webbläsaren och att rendera
 * ruta för ruta (rendera.mjs) – samma manus ger alltid samma film.
 *
 * Manuset beskriver scener med längd; tidpunkter inne i en scen är relativa.
 * Motorn räknar ut absoluta tider, undertexter, räknaren och ljudhändelser.
 * Temat ritar allt som syns och listar sina ljudhändelser.
 */
(function () {
  const W = 1080, H = 1920;
  const M = { W, H, teman: {} };
  window.Motor = M;

  // ------------------------------------------------------------ hjälpare
  M.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  M.smooth = x => { x = M.clamp(x); return x * x * (3 - 2 * x); };
  M.ramp = (t, a, b) => (b === a ? (t >= a ? 1 : 0) : M.smooth((t - a) / (b - a)));
  M.fonster = (t, a, b, fi = 0.25, fo = 0.25) => M.ramp(t, a, a + fi) * (1 - M.ramp(t, b - fo, b));
  /** Studs: 0 -> överskjut -> 1. */
  M.studs = x => { x = M.clamp(x); return 1 + 2.7 * Math.pow(x - 1, 3) + 1.7 * Math.pow(x - 1, 2); };
  M.slump = seed => {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  M.hash = (...v) => { const r = M.slump(v.reduce((h, x) => (h * 31 + Math.floor(x * 1000)) | 0, 7)); return r(); };

  /** Radbryter text till en maxbredd. "\n" ger tvingad radbrytning. */
  M.radbryt = (ctx, text, maxw) => {
    const ut = [];
    for (const del of String(text).split('\n')) {
      let rad = '';
      for (const ord of del.split(' ')) {
        const prov = rad ? rad + ' ' + ord : ord;
        if (ctx.measureText(prov).width <= maxw || !rad) rad = prov;
        else { ut.push(rad); rad = ord; }
      }
      ut.push(rad);
    }
    return ut;
  };

  // ------------------------------------------------------------ manus -> tidslinje
  function bygg(manus) {
    let t = 0;
    const texter = [], repliker = [];
    manus.scener.forEach((s, i) => {
      s.index = i;
      s.start = t;
      s.slut = t + s.len;
      t = s.slut;
      for (const x of s.texter || []) {
        const [a, b, text, stil, y] = x;
        texter.push({ fran: s.start + a, till: s.start + b, text, stil: stil || 'normal', y });
      }
      for (const r of s.repliker || []) {
        r.start = s.start + r.t;
        r.slut = r.start + (r.len || 1.8);
        r.scen = s;
        repliker.push(r);
      }
    });
    manus.total = t;
    manus.texter = texter;
    manus.repliker = repliker;
    return manus;
  }

  M.scenVid = t => {
    const sc = M.manus.scener;
    for (const s of sc) if (t >= s.start && t < s.slut) return s;
    return sc[sc.length - 1];
  };

  /** Räknarens värde vid t: scenens "raknare" är ett tal eller [från, till]. */
  M.raknare = t => {
    const s = M.scenVid(t);
    const r = s.raknare;
    if (r == null) return null;
    const skala = M.raknareSkala || 1;
    if (typeof r === 'string') return r;
    if (typeof r === 'number') return Math.floor(r * skala);
    const u = M.clamp((t - s.start) / (s.len * (s.raknareAndel || 1)));
    const k = s.raknareKurva === 'linjar' ? u : M.smooth(u);
    return Math.floor((r[0] + (r[1] - r[0]) * k) * skala + 1e-6);
  };

  // ------------------------------------------------------------ loggan
  M.logga = (ctx, { morkt = false, hoger = 1010, topp = 200, alfa = 0.92 } = {}) => {
    const B = M.brand;
    ctx.save();
    ctx.globalAlpha = alfa;
    const fg = morkt ? '#141418' : '#f5f5f8';
    ctx.textBaseline = 'top';
    ctx.font = "700 50px 'Display'";
    if ('letterSpacing' in ctx) ctx.letterSpacing = '2px';
    const wb = ctx.measureText(B.botten).width;
    ctx.font = "700 22px 'Display'";
    if ('letterSpacing' in ctx) ctx.letterSpacing = '9px';
    const wt = ctx.measureText(B.topp).width;
    const w = Math.max(wb, wt) + 36, x0 = hoger - w;
    ctx.strokeStyle = fg; ctx.lineWidth = 3;
    ctx.strokeRect(x0 + 1.5, topp + 1.5, w - 3, 97);
    ctx.fillStyle = B.accent; ctx.fillRect(x0, topp, 10, 100);
    ctx.fillStyle = fg;
    ctx.fillText(B.topp, x0 + 10 + (w - 10 - wt) / 2 + 4, topp + 12);
    ctx.font = "700 50px 'Display'";
    if ('letterSpacing' in ctx) ctx.letterSpacing = '2px';
    ctx.fillText(B.botten, x0 + 10 + (w - 10 - wb) / 2, topp + 38);
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
    ctx.restore();
  };

  // ------------------------------------------------------------ rita en bildruta
  function render(t) {
    const ctx = M.ctx;
    const s = M.scenVid(t);
    const lt = t - s.start;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    M.tema.rita(ctx, t, s, lt);
    ctx.restore();
  }

  // ------------------------------------------------------------ start
  M.start = async () => {
    const q = new URLSearchParams(location.search);
    const manus = window.MANUS || await (await fetch(q.get('manus'), { cache: 'no-store' })).json();
    M.brand = window.BRAND || await (await fetch('/common/brand.json', { cache: 'no-store' })).json();
    M.manus = bygg(manus);
    // "raknareFran": ett datum. Räknaren slutar då på antal dagar fram till i dag
    // (eller "raknareIdag"), och manusets värden skalas om så tempot behålls.
    if (manus.raknareFran) {
      const idag = manus.raknareIdag ? new Date(manus.raknareIdag) : new Date();
      const dagar = Math.floor((idag - new Date(manus.raknareFran)) / 86400000);
      const max = Math.max(...manus.scener.flatMap(s => (Array.isArray(s.raknare) ? s.raknare : typeof s.raknare === 'number' ? [s.raknare] : [])));
      M.raknareSkala = max > 0 ? dagar / max : 1;
      M.raknareDagar = dagar;
    }
    M.tema = M.teman[manus.tema];
    if (!M.tema) throw new Error('Okänt tema: ' + manus.tema);
    M.ctx = document.getElementById('duk').getContext('2d');
    await Promise.all((M.tema.typsnitt || []).map(f => document.fonts.load(f)));
    await document.fonts.ready;
    if (M.tema.forbered) await M.tema.forbered(M.manus);

    window.render = render;
    window.TIDER = { total: M.manus.total, fps: manus.fps || 30, scener: M.manus.scener.map(s => ({ typ: s.typ, start: s.start, slut: s.slut, musik: s.musik || null })) };
    window.HANDELSER = (M.tema.handelser ? M.tema.handelser(M.manus) : []).sort((a, b) => a.t - b.t);
    render(Number(q.get('t') || 0));
    window.KLAR = true;
    if (!q.get('rendera')) forhandsvisning();
  };

  /** Uppspelning i webbläsaren: play/paus, dra i tidslinjen, mellanslag. */
  function forhandsvisning() {
    document.body.classList.add('forhand');
    const knapp = document.getElementById('spela');
    const reg = document.getElementById('tid');
    const txt = document.getElementById('tidtext');
    const total = M.manus.total;
    reg.max = total;
    let t = 0, spelar = false, sist = 0;
    const visa = () => { render(t); reg.value = t; txt.textContent = `${t.toFixed(1)} / ${total.toFixed(1)} s`; };
    const slinga = nu => {
      if (spelar) { t += (nu - sist) / 1000; if (t >= total) t = 0; sist = nu; visa(); requestAnimationFrame(slinga); }
    };
    const vaxla = () => { spelar = !spelar; knapp.textContent = spelar ? '❚❚' : '▶'; if (spelar) { sist = performance.now(); requestAnimationFrame(slinga); } };
    knapp.onclick = vaxla;
    reg.oninput = () => { t = Number(reg.value); visa(); };
    document.addEventListener('keydown', e => { if (e.code === 'Space') { e.preventDefault(); vaxla(); } });
    visa();
  }
})();
