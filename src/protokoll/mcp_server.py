"""Steg 4: MCP-server som gör ärendeindexet sökbart för en AI-assistent.

Körs lokalt med stdio:  protokoll serve
Verktyg: sok_protokoll, hamta_arende, lista_sammantraden, hamta_protokoll.

Designad att kunna kombineras med en Kolada-MCP: sök besluten här, slå
upp nyckeltalen där.
"""

import json

from mcp.server.fastmcp import FastMCP

from . import config
from .search import connect, search

mcp = FastMCP("jonkoping-protokoll")


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
    rows = search(fraga, fran_datum, till_datum, max_traffar)
    if not rows:
        return "Inga träffar. Prova andra sökord eller ett vidare datumintervall."
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def hamta_arende(arende_id: int) -> str:
    """Hämta hela texten för ett ärende (id från sok_protokoll)."""
    con = connect()
    row = con.execute("SELECT * FROM arenden WHERE id = ?", (arende_id,)).fetchone()
    con.close()
    if not row:
        return f"Inget ärende med id {arende_id}."
    return json.dumps(dict(row), ensure_ascii=False, indent=2)


@mcp.tool()
def lista_sammantraden() -> str:
    """Lista alla indexerade sammanträden med datum och antal ärenden."""
    con = connect()
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
