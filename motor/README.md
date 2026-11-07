# Filmmotorn

En film är ett **manus** (`films/<nr>-<namn>/manus.json`) och ett **tema** (`motor/teman/*.js`). Ny film betyder nytt manus, inte ny kod.

```bash
node motor/rendera.mjs films/02-sandladan/manus.json                       # hela filmen, ~35 s
node motor/rendera.mjs films/02-sandladan/manus.json --stillbild 5,20,40   # snabba stillbilder
node motor/rendera.mjs films/02-sandladan/manus.json --forhandsvisa        # spela upp i webbläsaren
```

Resultat: `films/<film>/output/<namn>_tiktok.mp4` (1080×1920, 30 fps).

## Så fungerar det

Upplägget är detsamma som i `loven-stats-backend/film`:

1. `motor.html` laddar manuset och temat. Hela filmen är en funktion av tiden, `window.render(t)`.
2. `rendera.mjs` öppnar sidan i Playwright. Fyra flikar renderar var sin del parallellt, och bildrutorna går som JPEG rakt in i ffmpeg.
3. `ljud.py` syntetiserar musik och ljudeffekter från samma tidslinje (`window.HANDELSER`).
4. ffmpeg sätter ihop delarna med ljudet.

## Manus

```jsonc
{
  "tema": "sandlada",                       // vilken grafik
  "musik": { "stil": "lekplats", "tempo": 136, "tonart": "F", "seed": 7 },
  "roller": { "S": { "farg": "#E8112D", "plats": [330, 820], "rost": 200 } },
  "scener": [
    { "typ": "prat", "len": 8.0, "raknare": [4, 31], "musik": "spela",
      "repliker": [{ "t": 0.2, "vem": "S", "text": "Hej!", "len": 1.6, "humor": "arg", "zoom": true }],
      "texter":   [[0.0, 2.0, "Undertext", "normal"]],
      "ljud":     [[1.0, "boing"]] }
  ]
}
```

Tider inne i en scen är relativa till scenens start.

**Räknare mot verkligheten:** med `"raknareFran": "2026-09-13"` slutar räknaren på det faktiska antalet dagar fram till renderingsdagen, och scenernas `raknare`-värden skalas om så att tempot behålls. Rendera om filmen så stämmer siffran igen. Med `"raknareIdag"` låser du ett datum.

## Musik

Välj stil med `musik.stil`. Ett nytt `seed` ger en ny melodi. Varje scen styr läget med `musik`: `spela`, `kaos`, `spanning` (trumvirvel), `stopp` eller `start`.

| Stil | Känsla |
|---|---|
| `lekplats` | Humppa/cirkus: tuba, kazoo, komp. Humor och satir. |
| `noir` | Mörk synthpad i Vangelis-anda. Dystopi. |
| `lofi` | Lugnt elpiano och trumloop. Förklarande. |

Ljudeffekter: `smack pop boing spring prat tick fall klubba stampel gong skrik trombon vissla`.

## Teman

| Tema | Scentyper |
|---|---|
| `sandlada` | `rubrik intro prat brak rostning kor slut` |
| `noir` | (kommer när GNISTAN flyttas in) |

Loggan (`common/brand.json`) ritas automatiskt i alla teman.
