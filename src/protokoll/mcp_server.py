"""Steg 4: MCP-server som gör ärendeindexet sökbart för en AI-assistent.

Körs lokalt med stdio:  protokoll serve
Verktyg: sok_protokoll, hamta_arende, lista_sammantraden, hamta_protokoll.

Designad att kunna kombineras med en Kolada-MCP: sök besluten här, slå
upp nyckeltalen där.
"""

import json
import sqlite3

from mcp.server.fastmcp import FastMCP

from . import config

mcp = FastMCP("jonkoping-protokoll")


def _connect() -> sqlite3.Connection:
    if not config.DB_PATH.exists():
        raise RuntimeError(
            "Sökindexet saknas. Kör 'protokoll index' (eller 'protokoll all') först."
        )
    con = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _fts_query(query: str) -> str:
    """Gör om en fritextfråga till en tolerant FTS5-fråga.

    OR mellan orden och prefixmatchning, så att "skolskjuts" även träffar
    sammansättningar som "skolskjutsreglemente".
    """
    words = [w for w in query.replace('"', " ").split() if w]
    return " OR ".join(f'"{w}"*' for w in words) or '""'


@mcp.tool()
def sok_protokoll(
    fraga: str,
    fran_datum: str = "",
    till_datum: str = "",
    max_traffar: int = 10,
) -> str:
    """Fritextsök bland ärenden i barn- och utbildningsnämndens protokoll.

    Args:
        fraga: Sökord, t.ex. "skolskjuts" eller "budget förskola".
        fran_datum: Valfritt filter, ÅÅÅÅ-MM-DD.
        till_datum: Valfritt filter, ÅÅÅÅ-MM-DD.
        max_traffar: Max antal träffar (standard 10).
    """
    con = _connect()
    sql = (
        "SELECT a.id, a.namnd, a.datum, a.paragraf, a.rubrik, a.dnr, a.beslut,"
        " snippet(arenden_fts, 1, '>>', '<<', ' ... ', 40) AS utdrag"
        " FROM arenden_fts JOIN arenden a ON a.id = arenden_fts.rowid"
        " WHERE arenden_fts MATCH ?"
    )
    params: list = [_fts_query(fraga)]
    if fran_datum:
        sql += " AND a.datum >= ?"
        params.append(fran_datum)
    if till_datum:
        sql += " AND a.datum <= ?"
        params.append(till_datum)
    sql += " ORDER BY rank LIMIT ?"
    params.append(max(1, min(max_traffar, 50)))
    rows = [dict(r) for r in con.execute(sql, params)]
    con.close()
    if not rows:
        return "Inga träffar. Prova andra sökord eller ett vidare datumintervall."
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def hamta_arende(arende_id: int) -> str:
    """Hämta hela texten för ett ärende (id från sok_protokoll)."""
    con = _connect()
    row = con.execute("SELECT * FROM arenden WHERE id = ?", (arende_id,)).fetchone()
    con.close()
    if not row:
        return f"Inget ärende med id {arende_id}."
    return json.dumps(dict(row), ensure_ascii=False, indent=2)


@mcp.tool()
def lista_sammantraden() -> str:
    """Lista alla indexerade sammanträden med datum och antal ärenden."""
    con = _connect()
    rows = [
        dict(r)
        for r in con.execute(
            "SELECT namnd, datum, fil, COUNT(*) AS antal_arenden,"
            " MIN(paragraf) || '-' || MAX(paragraf) AS paragrafer"
            " FROM arenden GROUP BY fil ORDER BY datum"
        )
    ]
    con.close()
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def hamta_protokoll(fil: str) -> str:
    """Hämta ett helt protokoll som markdown (filnamn från lista_sammantraden)."""
    path = config.MD_DIR / fil
    if not path.is_file() or path.suffix != ".md" or path.parent != config.MD_DIR:
        return f"Hittar inte protokollet {fil!r}."
    return path.read_text(encoding="utf-8")


def run() -> int:
    mcp.run()
    return 0
