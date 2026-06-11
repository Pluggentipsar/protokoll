# protokoll — sökbara nämndprotokoll för Jönköpings kommun

Gör [barn- och utbildningsnämndens protokoll](https://www.jonkoping.se/kommun--politik/kommunens-organisation/politiska-namnder/barn--och-utbildningsnamnden)
sökbara för en AI-assistent (Copilot, Claude m.fl.), i fyra steg:

```
1. fetch    PDF:er hämtas från jonkoping.se        -> data/pdf/  (+ manifest.json)
2. convert  PDF -> markdown med YAML-frontmatter   -> data/md/
3. index    markdown delas per ärende (§) och      -> data/index/arenden.jsonl
            indexeras med SQLite FTS5                 data/index/protokoll.db
4. serve    MCP-server exponerar sökningen för en AI-assistent
```

Markdownfilerna i `data/md/` är samtidigt redo att läggas i ett
SharePoint-bibliotek för en Copilot-agent — formatet är medvetet
front-end-oberoende.

## Kom igång

```bash
uv venv .venv && uv pip install -p .venv/bin/python -e .
.venv/bin/protokoll all      # hämta + konvertera + indexera
.venv/bin/protokoll serve    # starta MCP-servern (stdio)
```

Testa utan nätverk (syntetiskt protokoll genom hela kedjan):

```bash
.venv/bin/python tests/smoke_test.py
```

## MCP-verktyg

| Verktyg | Gör |
|---|---|
| `sok_protokoll(fraga, fran_datum?, till_datum?)` | Fritextsökning per ärende, med beslutssats och utdrag. Prefixmatchning så "skolskjuts" träffar "skolskjutsreglemente". |
| `hamta_arende(id)` | Hela texten för ett ärende. |
| `lista_sammantraden()` | Alla indexerade sammanträden med §-intervall. |
| `hamta_protokoll(fil)` | Ett helt protokoll som markdown. |

Exempel på klientkonfiguration (Claude Desktop/Code):

```json
{
  "mcpServers": {
    "jonkoping-protokoll": {
      "command": "/sökväg/till/protokoll/.venv/bin/protokoll",
      "args": ["serve"]
    }
  }
}
```

Tanken är att kombinera med en Kolada-MCP: besluten söks här, nyckeltalen
(kostnad per elev, behörighet, personaltäthet …) hämtas där.

## Automatisk uppdatering

`.github/workflows/uppdatera-protokoll.yml` kör pipelinen varje vecka på
GitHub Actions och committar nya protokoll. Nämnden sammanträder ungefär
en gång i månaden.

## Per ärende extraheras

- `paragraf` — §-nummer
- `rubrik` — ärenderubrik
- `dnr` — diarienummer (t.ex. `BUN 2025/123`)
- `beslut` — beslutssatsen ("Barn- och utbildningsnämnden beslutar att …")
- `text` — hela ärendetexten
- `namnd`, `datum`, `kalla` — från manifestet/frontmattern

## Kända begränsningar

- Inskannade PDF:er utan textlager hoppas över med varning (kräver OCR,
  t.ex. `ocrmypdf` — inte inkopplat ännu).
- Regexarna för §/Dnr/Beslut är skrivna mot strukturen i kommunens
  protokoll men bör stämmas av mot ett antal riktiga protokoll och
  justeras vid behov (`src/protokoll/extract.py`).
- Protokollen är allmänna handlingar men kan innehålla personuppgifter —
  håll åtkomsten intern tills en GDPR-bedömning är gjord.

## Fler nämnder

Lägg till seedsidor i `SEEDS` i `src/protokoll/config.py`.
