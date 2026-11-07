# TikTok-filmer

Kodgenererade kortfilmer för TikTok (1080×1920, vertikalt). Nya filmer görs med **filmmotorn** i `motor/`: skriv en `manus.json`, välj tema och musikstil och rendera på under en minut. Se [motor/README.md](motor/README.md).

| # | Film | Längd | Tema |
|---|---|---|---|
| 01 | [GNISTAN](films/01-gnistan/) | 58 s | AI:s evolution från GPT-1 till agenter, AGI och ASI. Mörkt, Blade Runner, inspirerat av *Right Here, Right Now*. (Äldre Python-pipeline.) |
| 02 | [SANDLÅDAN](films/02-sandladan/) | 53 s | Regeringsbildningen som barnprogram. Alla partier i en sandlåda. Lekfull grafik, humppa-musik. |

## Varumärke

Loggan (**MISTER PRESS**) definieras i `common/brand.py` och ritas automatiskt i alla filmer.

## Kom igång

```bash
pip install -r requirements.txt     # numpy, scipy (ljud), pillow
npm install                          # playwright
node motor/rendera.mjs films/02-sandladan/manus.json
```
