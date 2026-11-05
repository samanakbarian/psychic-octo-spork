# Film 01 – GNISTAN

**AI:s evolution från GPT-1 till ASI på 58 sekunder.** Mörk, dystopisk, Blade Runner-estetik.

**Inspiration:** Fatboy Slims *Right Here, Right Now* (regi Hammer & Tongs), där evolutionen spelas upp i en enda obruten svit med en räknare i hörnet och slutar i "nuet". Vi lånar *formen* men inte musiken eller bilderna:

| Fatboy Slim-videon | GNISTAN |
|---|---|
| En encellig organism | En ensam glödande neuron (GPT-1) |
| Tidsräknare i bild | Årsräknare som tickar `2018 → 2026 → 20?? → ????` |
| Evolutionen accelererar | Ett hjärtslag som går från 50 till 150 BPM |
| Slutar på "right here, right now" | **"HÄR. JUST NU."**, och sedan *fortsätter räknaren* in i AGI/ASI |

Skillnaden ligger i vändningen. Fatboy Slim stannar i nuet, men här rullar räknaren vidare in i det okända. Filmen slutar där den började, med en ensam gnista, så att den loopar sömlöst på TikTok.

## Specifikationer

- Loggan **MISTER PRESS** ligger i övre högra hörnet under hela filmen och kommer från `common/brand.py`, som delas av alla filmer.
- Modellnamnen (GPT-1, ChatGPT, o1, AI-AGENTER, AGI, ASI) visas som stora rubriker som smäller in vid varje scenbyte, med en förklarande rad under.
- En tidslinje med markeringen "VI ÄR HÄR" (mellan agenter och AGI) visas vid klimaxen och i slutet.

- 1080×1920, 30 fps, 58 s, H.264 + AAC
- All text ligger inom TikToks säkra zon, alltså ovanför bottentexten och till vänster om ikonerna till höger
- Originalmusiken är syntad i kod och därmed fri från upphovsrätt. Byt gärna till ett ljud från TikToks eget bibliotek.

## Manus och storyboard

| Tid | Scen | Räknare | Bild | Text | Ljud |
|---|---|---|---|---|---|
| 0–3 | **KROK** | – | Glitchade glimtar av framtiden: ögat, sfären, agenterna | **DET HÄR TOG / 8 ÅR.** | Två smällar |
| 3–9 | GPT-1 | 2018 · 117 M | En ensam neuron i tomrummet, dendriter växer ut | *Det började med en gnista. / Den kunde knappt skriva en mening.* | Hjärtslag 50 BPM, regn |
| 9–14 | GPT-2 | 2019 · 1,5 md | Neuronen förgrenar sig till ett roterande nät | *"För farlig för att släppas."* | |
| 14–19 | GPT-3 | 2020 · 175 md | Nätet exploderar, kameran drar ut och staden reser sig | *Sen lärde den sig låta som oss.* | Hi-hats: data börjar flöda |
| 19–25 | ChatGPT | 2022 | Terminal: `> hej. vem är du?` och en användarräknare som rusar till 100 000 000 | *Vi släppte in den. / 100 miljoner av oss. På två månader.* | Tangentklick synkat mot varje tecken |
| 25–30 | GPT-4 | 2023 | Ett gigantiskt öga öppnas över staden med neon i irisen | *Den lärde sig se.* | |
| 30–35 | o1 (resonerande) | 2024 | Ett tanketräd förgrenar sig, döda grenar blir röda och en väg vinner | *Den lärde sig tänka efter.* | |
| 35–39,5 | Agenter | 2025 → 2026 | Hundratals agenter rusar genom stadens rutnät. Loggen: `agent_2210 » startar agent_2211…` | *Nu jobbar den. Utan oss.* | 150 BPM, riser |
| 39,5–42 | **NU** | 2026 | Strömavbrott. Svart. Regn. Tidslinje: GPT-1 → … → **● VI ÄR HÄR** → AGI? → ASI? | **HÄR. / JUST NU.** | Två jättesmällar, tinnitus |
| 42–47,5 | AGI | 20?? | Staden tänds i rött. En trådsfär reser sig bakom skylinen. | *Snart: lika smart som vi. / I allt.* | "BRAAAM", tung maskinpuls |
| 47,5–52 | ASI | ???? | Sfären sväller över hela bilden och vitnar ut | *Sen smartare än alla oss. / Tillsammans.* | Shepard-riser och hård cut |
| 52–58 | OUTRO | – | Svart, regn, en ensam gnista och tidslinjen igen (loopar till början) | *Vi är här. Just nu. / Frågan är vad vi gör med tiden som är kvar.* | Ett ensamt hjärta |

### Faktakoll
- GPT-1 (juni 2018): 117 M parametrar
- GPT-2 (feb 2019): 1,5 md parametrar. OpenAI släppte den stegvis med hänvisning till risken för missbruk ("too dangerous to release" i pressen).
- GPT-3 (maj 2020): 175 md parametrar
- ChatGPT (30 nov 2022): cirka 100 M användare på ungefär två månader
- GPT-4 (mars 2023): multimodal, antalet parametrar är inte officiellt
- 2024: resonerande modeller som "tänker" innan de svarar
- 2025–2026: autonoma agenter som arbetar själva i långa sessioner
- AGI/ASI: spekulativt, och därför visar räknaren `20??` / `????`

## Bygg filmen

```bash
pip install -r ../../requirements.txt
./build.sh            # -> output/gnistan_tiktok.mp4
python3 render_video.py --preview 26.5 44   # snabba stillbilder för att testa
```

Allt synkas från `timeline.py`, som innehåller scener, texter, räknare och slag. Ändra en tid där så följer både bild och ljud med.

## Uppgradera med AI-video (valfritt)

Den kodgenererade versionen är färdig att lägga upp. Vill du ha fotorealism kan du generera varje scen i Sora, Veo, Runway eller Kling (9:16, 5–6 s per klipp) och lägga texter och räknare ovanpå. Gemensam stilsträng som du klistrar in i början av varje prompt:

> *Cinematic 9:16, neo-noir cyberpunk, 1982 sci-fi film look, heavy rain, volumetric fog, teal shadows and sodium-orange highlights, anamorphic lens flares, 35mm film grain, slow continuous dolly, no text.*

1. **Gnistan:** a single glowing neuron floating in infinite black void, faint rain falling through the darkness, it pulses like a heartbeat
2. **Nätet:** the neuron splits and branches into a growing 3D web of glowing nodes, slowly rotating, camera slowly pulls back
3. **Staden:** the neural web rises into the night sky as a megacity skyline emerges from fog below, thousands of windows lighting up
4. **Terminalen:** close-up of an old CRT terminal in a dark rain-streaked apartment, green cursor blinking, reflection of neon city on the glass
5. **Ögat:** extreme close-up of a giant human eye opening, the iris reflects a burning neon megacity, pupils dilate
6. **Tanketrädet:** lightning-like branching filaments of light spreading through darkness, some branches die and turn red, one path glows white
7. **Agenterna:** top-down view of a rain-soaked megacity grid at night, hundreds of small amber lights racing through streets autonomously
8. **Mörkläggningen:** the whole city blacks out at once, only rain and silence, then every window flickers back on in blood red
9. **AGI:** a colossal red wireframe sphere slowly rises behind the skyline like a second moon, the city pulses red in sync with it
10. **ASI:** the sphere expands until it fills the sky, light turns blinding white, everything dissolves into overexposure
11. **Slutet:** pitch black, rain, a single tiny spark of light remains

## Publicering

**Bildtext:** `8 år. Från en gnista till… det här. Vad gör vi med tiden som är kvar? 🕯️`

**Hashtags:** `#AI #AGI #ChatGPT #framtiden #bladerunner #cyberpunk #tech #fyp #svenska`

**Tips:** Fäst en kommentar med frågan *"Hur långt bort tror du AGI är?"* för att få igång engagemanget. Klippet loopar sömlöst, och det höjer tittartiden.
