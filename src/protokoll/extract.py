"""Steg 3: Dela upp protokollen i ärenden (§) och bygg sökindex.

Varje markdownfil delas vid §-rubriker. Per ärende extraheras paragraf-
nummer, rubrik, diarienummer och beslutssats. Resultatet skrivs både som
JSONL (versionshanterbart, läsbart) och som SQLite FTS5-databas som
MCP-servern söker i.
"""

import json
import re
import sqlite3

from . import config

# Ärenderubrik. Tolerant prefix så både gamla mallen ("## § 45 Rubrik",
# "**§ 45** Rubrik") och nya mallen ("## **§ 46**") fångas. Innehålls-
# tabellens rader börjar med "|" och matchas alltså inte (de är inte ärenden).
SECTION_RE = re.compile(r"^[ \t#*]*§[ \t*]*(\d+)\b[ \t*.:-]*(.*)$", re.MULTILINE)
# Barn- och utbildningsnämndens diarienummer: "BUN 2025/123" (gamla) och
# "Bun/2025:172" (nya). Letar inte efter "Dnr"-prefix eftersom nya mallen
# saknar det. BUN-ankaret undviker falska träffar på t.ex. "SOU 2025:8".
DNR_RE = re.compile(r"\bBUN[ /]?(\d{4})[:/](\d+)", re.IGNORECASE)
BESLUT_RE = re.compile(
    r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(?:Beslut|Barn- och utbildningsnämndens beslut|Nämndens beslut)\s*(?:\*\*)?\s*\n(.*?)(?=\n\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(?:Reservation|Protokollsanteckning|Ärende|Sammanfattning|Beslutsmotivering|Skäl|Yrkanden|§)\b|\Z)",
    re.DOTALL,
)


def find_dnr(text: str) -> str | None:
    m = DNR_RE.search(text)
    return f"Bun/{m.group(1)}:{m.group(2)}" if m else None


def parse_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip().strip('"')
            text = text[end + 4 :]
    return meta, text


def clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_arenden(body: str) -> list[dict]:
    matches = list(SECTION_RE.finditer(body))
    arenden = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = clean(body[m.start() : end])
        rubrik = m.group(2).strip().strip("*# ").strip()
        # Rubriken kan ligga på raden efter §-numret.
        if not rubrik:
            for line in text.splitlines()[1:]:
                line = line.strip().strip("*# ").strip()
                if line:
                    rubrik = line
                    break
        # PDF-extraktionen kan slå ihop rubrikraden med Dnr-raden under.
        rubrik = re.sub(r"[,.\s]*\b(?:Dnr|Diarienummer)\b.*$", "", rubrik).strip()
        dnr = find_dnr(text)
        beslut = BESLUT_RE.search(text)
        arenden.append(
            {
                "paragraf": int(m.group(1)),
                "rubrik": rubrik,
                "dnr": dnr,
                "beslut": clean(beslut.group(1))[:2000] if beslut else None,
                "text": text,
            }
        )
    return arenden


def build_db(rows: list[dict]) -> None:
    config.DB_PATH.unlink(missing_ok=True)
    con = sqlite3.connect(config.DB_PATH)
    con.executescript(
        """
        CREATE TABLE arenden (
            id INTEGER PRIMARY KEY,
            namnd TEXT, datum TEXT, paragraf INTEGER, rubrik TEXT,
            dnr TEXT, beslut TEXT, text TEXT, kalla TEXT, fil TEXT
        );
        CREATE VIRTUAL TABLE arenden_fts USING fts5(
            rubrik, text, content='arenden', content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )
    con.executemany(
        "INSERT INTO arenden (id, namnd, datum, paragraf, rubrik, dnr, beslut,"
        " text, kalla, fil) VALUES (:id, :namnd, :datum, :paragraf, :rubrik,"
        " :dnr, :beslut, :text, :kalla, :fil)",
        rows,
    )
    con.execute(
        "INSERT INTO arenden_fts (rowid, rubrik, text)"
        " SELECT id, rubrik, text FROM arenden"
    )
    con.commit()
    con.close()


def run() -> int:
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for md_path in sorted(config.MD_DIR.glob("*.md")):
        meta, body = parse_frontmatter(md_path.read_text(encoding="utf-8"))
        arenden = split_arenden(body)
        if not arenden:
            print(f"VARNING: inga §-ärenden hittade i {md_path.name}")
            continue
        for arende in arenden:
            rows.append(
                {
                    "id": len(rows) + 1,
                    "namnd": meta.get("namnd"),
                    "datum": meta.get("datum"),
                    "kalla": meta.get("kalla"),
                    "fil": md_path.name,
                    **arende,
                }
            )
    with config.ARENDEN_JSONL.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    build_db(rows)
    print(f"Klart: {len(rows)} ärenden indexerade i {config.DB_PATH.name}.")
    return 0
