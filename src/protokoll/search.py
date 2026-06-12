"""Delad FTS5-sökning över ärendeindexet. Används av både CLI (protokoll
search) och MCP-servern, så sökbeteendet är identiskt."""

import sqlite3

from . import config


def connect() -> sqlite3.Connection:
    if not config.DB_PATH.exists():
        raise RuntimeError(
            "Sökindexet saknas. Kör 'protokoll index' (eller 'protokoll all') först."
        )
    con = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def fts_query(query: str) -> str:
    """Tolerant FTS5-fråga: OR mellan orden och prefixmatchning, så att
    "skolskjuts" även träffar "skolskjutsreglemente"."""
    words = [w for w in query.replace('"', " ").split() if w]
    return " OR ".join(f'"{w}"*' for w in words) or '""'


def search(
    fraga: str,
    fran_datum: str = "",
    till_datum: str = "",
    max_traffar: int = 10,
) -> list[dict]:
    con = connect()
    sql = (
        "SELECT a.id, a.namnd, a.datum, a.paragraf, a.rubrik, a.dnr, a.beslut, a.fil,"
        " snippet(arenden_fts, 1, '>>', '<<', ' … ', 40) AS utdrag"
        " FROM arenden_fts JOIN arenden a ON a.id = arenden_fts.rowid"
        " WHERE arenden_fts MATCH ?"
    )
    params: list = [fts_query(fraga)]
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
    return rows
