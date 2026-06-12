"""Exporterar ärendeindexet till en kompakt JSON som Cloudflare-Workern
bäddar in och söker i (korpusen är liten nog för sökning i minnet).

Kör:  protokoll export
Skriver worker/data/arenden.json relativt repo-roten.
"""

import json

from . import config

OUT = config.ROOT / "worker" / "data" / "arenden.json"


def run() -> int:
    if not config.ARENDEN_JSONL.exists():
        raise RuntimeError("Inget index. Kör 'protokoll index' först.")
    with config.ARENDEN_JSONL.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh]
    # Behåll bara fält Workern behöver, i en kompakt array.
    slim = [
        {
            "id": r["id"],
            "namnd": r["namnd"],
            "datum": r["datum"],
            "paragraf": r["paragraf"],
            "rubrik": r["rubrik"],
            "dnr": r["dnr"],
            "beslut": r["beslut"],
            "fil": r["fil"],
            "kalla": r.get("kalla"),
            "text": r["text"],
        }
        for r in rows
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    kb = OUT.stat().st_size / 1024
    print(f"Skrev {len(slim)} ärenden till {OUT.relative_to(config.ROOT)} ({kb:.0f} kB)")
    return 0
