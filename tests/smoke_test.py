"""End-to-end-rök­test utan nätverk: syntetisk PDF -> markdown -> index -> sökning.

Körs med:  .venv/bin/python tests/smoke_test.py
OBS: skriver i data/ — rensa efteråt om du inte vill ha testdatan kvar.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from protokoll import config, convert, extract  # noqa: E402
from protokoll.fetch import save_manifest  # noqa: E402
from make_sample_pdf import make  # noqa: E402

NAME = "barn-och-utbildningsnamnden-2025-04-15"


def main() -> int:
    pdf = make(config.PDF_DIR / f"{NAME}.pdf")
    save_manifest(
        {
            "https://example.test/protokoll.pdf": {
                "fil": pdf.name,
                "namnd": "Barn- och utbildningsnämnden",
                "datum": "2025-04-15",
                "lanktext": "Protokoll 2025-04-15",
            }
        }
    )
    convert.run(force=True)
    extract.run()

    md = (config.MD_DIR / f"{NAME}.md").read_text(encoding="utf-8")
    assert 'namnd: "Barn- och utbildningsnämnden"' in md, "frontmatter saknas"
    assert "Skolskjutsreglemente" in md, "PDF-text saknas i markdown"

    rows = [
        json.loads(line)
        for line in config.ARENDEN_JSONL.read_text(encoding="utf-8").splitlines()
    ]
    assert [r["paragraf"] for r in rows] == [41, 42, 43], f"fel §: {rows}"
    skolskjuts = rows[1]
    assert skolskjuts["dnr"] == "Bun/2025:123", f"dnr: {skolskjuts['dnr']}"
    assert "att anta reviderat skolskjutsreglemente" in (skolskjuts["beslut"] or "")
    budget = rows[2]
    assert "åtgärdsplan" in (budget["beslut"] or ""), f"beslut: {budget['beslut']}"
    assert "Reservation" not in (budget["beslut"] or ""), "beslut tog med reservationen"

    con = sqlite3.connect(config.DB_PATH)
    hits = con.execute(
        "SELECT a.rubrik FROM arenden_fts JOIN arenden a ON a.id = arenden_fts.rowid"
        " WHERE arenden_fts MATCH ? ORDER BY rank",
        ['"skolskjuts"* OR "avståndsgräns"*'],
    ).fetchall()
    con.close()
    assert hits and "Skolskjuts" in hits[0][0], f"FTS-träffar: {hits}"

    print("SMOKE TEST OK: pdf -> md -> jsonl/sqlite -> FTS-sökning fungerar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
