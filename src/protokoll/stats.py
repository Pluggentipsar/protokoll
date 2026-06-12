"""Statistik över det byggda ärendeindexet – mäter extraktionskvaliteten.

Visar hur stor andel ärenden som fått rubrik, diarienummer och beslut,
antal protokoll och datumspann, samt ett par exempelärenden från det
senaste protokollet. Kör:  protokoll stats
"""

import json

from . import config


def _load() -> list[dict]:
    if not config.ARENDEN_JSONL.exists():
        raise RuntimeError("Inget index. Kör 'protokoll index' först.")
    with config.ARENDEN_JSONL.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def _andel(rows: list[dict], faltet: str) -> str:
    n = sum(1 for r in rows if r.get(faltet))
    return f"{n}/{len(rows)} ({100 * n // max(len(rows), 1)} %)"


def run() -> int:
    rows = _load()
    filer = sorted({r["fil"] for r in rows})
    datum = sorted(r["datum"] for r in rows if r.get("datum"))
    print(f"Ärenden:        {len(rows)}")
    print(f"Protokoll:      {len(filer)}")
    if datum:
        print(f"Datumspann:     {datum[0]} – {datum[-1]}")
    print(f"Med rubrik:     {_andel(rows, 'rubrik')}")
    print(f"Med diarienr:   {_andel(rows, 'dnr')}")
    print(f"Med beslut:     {_andel(rows, 'beslut')}")

    # Protokoll med få ärenden kan tyda på misslyckad extraktion.
    per_fil: dict[str, int] = {}
    for r in rows:
        per_fil[r["fil"]] = per_fil.get(r["fil"], 0) + 1
    fa = sorted((n, f) for f, n in per_fil.items() if n < 5)
    if fa:
        print("\nProtokoll med få ärenden (<5):")
        for n, f in fa:
            print(f"  {n:>2}  {f}")

    senaste = max(filer, key=lambda f: next(r["datum"] or "" for r in rows if r["fil"] == f))
    print(f"\nExempelärenden ur {senaste}:")
    for r in [r for r in rows if r["fil"] == senaste][:6]:
        print(f"  § {r['paragraf']:>3}  {r['rubrik']!r}  dnr={r['dnr']}")
        if r["beslut"]:
            print(f"        beslut: {r['beslut'][:80]!r}")
        else:
            print("        beslut: (saknas)")
    return 0
