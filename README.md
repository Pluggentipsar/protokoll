# protokoll — sökbara nämndprotokoll för Jönköpings kommun

Gör [barn- och utbildningsnämndens protokoll](https://www.jonkoping.se/kommun--politik/kommunens-organisation/politiska-namnder/barn--och-utbildningsnamnden)
sökbara för utbildningsdirektören. En pipeline hämtar tio års protokoll,
gör om dem från PDF till strukturerad text, och paketerar dem för leverans
via **SharePoint + Copilot** (primär väg) eller en MCP-server (upgrade-spår).

```
fetch    PDF:er hämtas (rekursiv crawl av nämndens mappträd)  -> data/pdf/
convert  PDF -> markdown med YAML-frontmatter (UTF-8)          -> data/md/
index    markdown delas per ärende (§), extraherar diarienr    -> data/index/
         och beslutssats, bygger SQLite FTS5 + JSONL

Leverans:
sharepoint  ett Word-dokument per sammanträde   -> sharepoint/   (SharePoint + Copilot)
export      kompakt JSON för Cloudflare-Workern  -> worker/data/  (MCP, valfritt)
serve       lokal MCP-server (stdio) för Claude Desktop
search      provsök i terminalen
stats       kvalitetskoll av indexet
```

## Kom igång

```bash
uv venv .venv && uv pip install -p .venv/bin/python -e .
.venv/bin/protokoll all          # fetch + convert + index
.venv/bin/protokoll sharepoint   # generera Word-dokument
```

På Windows: `.venv\Scripts\protokoll`. Testa utan nätverk:
`.venv/bin/python tests/smoke_test.py`.

## Leverans till direktören: SharePoint + Copilot

1. `protokoll sharepoint` skapar `sharepoint/` med en `.docx` per sammanträde
   (titel, källa, och per § rubrik/diarienummer/beslut/ärendetext). Word
   indexeras tillförlitligt av Microsoft 365 Copilot, och den strukturerade
   datan ger bättre grounding än råa PDF:er.
2. Skapa ett SharePoint-dokumentbibliotek och ladda upp mappen.
3. I Copilot Studio: lägg till biblioteket som **Knowledge** i agenten (samma
   agent som t.ex. Kolada, eller en egen protokoll-agent).
4. Lägg en rad i agentinstruktionen: använd protokoll-kunskapen för frågor om
   nämndens beslut, och ange alltid källa.

Personuppgifterna stannar inom kommunens tenant — bättre dataskyddsläge än ett
öppet API. Protokollen är allmänna handlingar men kan innehålla personuppgifter;
håll åtkomsten intern och stäm av med dataskyddsombud innan bredare spridning.

## MCP-server (valfritt upgrade-spår)

För strukturerad, exakt sökning som ett *verktyg* bredvid t.ex. Kolada i samma
samtal. Lokalt (Claude Desktop, stdio): `protokoll serve`. Som remote HTTP för
Copilot Studio finns en påbörjad Cloudflare Worker i `worker/` (söklogik klar i
`worker/src/protokoll.ts`; transport-kopplingen färdigställs vid behov).
`protokoll export` skapar datafilen Workern bäddar in.

MCP-verktyg: `sok_protokoll`, `hamta_arende`, `lista_sammantraden`, `hamta_protokoll`.

## Automatisk uppdatering

`.github/workflows/uppdatera-protokoll.yml` kör pipelinen veckovis och committar
nya protokoll. Nämnden sammanträder ungefär en gång i månaden.

## Per ärende extraheras

`paragraf` (§-nummer), `rubrik`, `dnr` (t.ex. `Bun/2025:172`), `beslut`
(beslutssatsen), `text` (hela ärendet), samt `namnd`/`datum`/`kalla`.

## Kända begränsningar

- Inskannade PDF:er utan textlager hoppas över (kräver OCR, ej inkopplat). Tre
  gamla protokoll (2016–2018) saknar §-tecken i texten och indexeras inte.
- §/Dnr/Beslut-regexarna stödjer kommunens gamla och nya (2024→) protokollmall;
  stäm av vid mallbyten (`src/protokoll/extract.py`).

## Fler nämnder

Lägg till nämndens rotsida i `NAMND_ROTSIDOR` i `src/protokoll/config.py`.
