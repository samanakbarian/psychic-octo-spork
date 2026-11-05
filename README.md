# TikTok-filmer

Kodgenererade kortfilmer för TikTok (1080×1920, vertikalt). Varje film ligger i en egen mapp under `films/` med manus, storyboard, AI-promptar och en renderpipeline (Python + ffmpeg) som bygger både bild och originalljud.

| # | Film | Längd | Tema |
|---|---|---|---|
| 01 | [GNISTAN](films/01-gnistan/) | 58 s | AI:s evolution från GPT-1 till agenter, AGI och ASI. Mörkt, Blade Runner, inspirerat av *Right Here, Right Now*. |

## Varumärke

Loggan (**MISTER PRESS**) definieras i `common/brand.py` och ritas automatiskt i alla filmer.

## Kom igång

```bash
pip install -r requirements.txt
films/01-gnistan/build.sh
```

Färdig film: `films/01-gnistan/output/gnistan_tiktok.mp4`
