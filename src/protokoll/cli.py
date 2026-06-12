"""Kommandoradsgränssnitt: protokoll fetch|convert|index|stats|search|all|serve"""

import argparse


def _print_traffar(rows: list[dict]) -> None:
    if not rows:
        print("Inga träffar. Prova andra sökord eller ett vidare datumintervall.")
        return
    for r in rows:
        print(f"\n§ {r['paragraf']} – {r['rubrik']}  ({r['datum']})")
        if r["dnr"]:
            print(f"  Diarienr: {r['dnr']}")
        if r["beslut"]:
            print(f"  Beslut: {r['beslut'][:200]}")
        print(f"  Utdrag: {r['utdrag']}")
        print(f"  [id {r['id']}, {r.get('fil', '')}]")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="protokoll",
        description="Pipeline för sökbara nämndprotokoll (Jönköpings kommun).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Ladda ned nya protokoll-PDF:er")
    p_diag = sub.add_parser(
        "diagnose", help="Visa vad fetch ser på en sida (felsökning)"
    )
    p_diag.add_argument("url", nargs="*", help="Valfria URL:er; annars seedsidorna")
    p_convert = sub.add_parser("convert", help="Konvertera PDF:er till markdown")
    p_convert.add_argument("--force", action="store_true", help="Konvertera om allt")
    sub.add_parser("index", help="Bygg ärendeindex (JSONL + SQLite FTS)")
    sub.add_parser("stats", help="Visa statistik över ärendeindexet (kvalitetskoll)")
    sub.add_parser("export", help="Exportera index till worker/data/arenden.json")
    sub.add_parser(
        "sharepoint", help="Generera Word-dokument per protokoll (sharepoint/)"
    )
    p_search = sub.add_parser("search", help="Sök i protokollen från terminalen")
    p_search.add_argument("fraga", nargs="+", help="Sökord")
    p_search.add_argument("--from", dest="fran", default="", help="Fr.o.m. ÅÅÅÅ-MM-DD")
    p_search.add_argument("--to", dest="till", default="", help="T.o.m. ÅÅÅÅ-MM-DD")
    p_search.add_argument("-n", type=int, default=10, help="Max antal träffar")
    sub.add_parser("all", help="fetch + convert + index")
    sub.add_parser("serve", help="Starta MCP-servern (stdio)")
    args = parser.parse_args()

    if args.cmd == "fetch":
        from . import fetch

        return fetch.run()
    if args.cmd == "diagnose":
        from . import diagnose

        return diagnose.run(args.url or None)
    if args.cmd == "convert":
        from . import convert

        return convert.run(force=args.force)
    if args.cmd == "index":
        from . import extract

        return extract.run()
    if args.cmd == "stats":
        from . import stats

        return stats.run()
    if args.cmd == "export":
        from . import export

        return export.run()
    if args.cmd == "sharepoint":
        from . import sharepoint

        return sharepoint.run()
    if args.cmd == "search":
        from . import search

        _print_traffar(search.search(" ".join(args.fraga), args.fran, args.till, args.n))
        return 0
    if args.cmd == "all":
        from . import convert, extract, fetch

        fetch.run()
        convert.run()
        return extract.run()
    if args.cmd == "serve":
        from . import mcp_server

        return mcp_server.run()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
