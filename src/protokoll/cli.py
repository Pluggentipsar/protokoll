"""Kommandoradsgränssnitt: protokoll fetch|convert|index|all|serve"""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="protokoll",
        description="Pipeline för sökbara nämndprotokoll (Jönköpings kommun).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Ladda ned nya protokoll-PDF:er")
    sub.add_parser("diagnose", help="Visa vad fetch ser på seedsidorna (felsökning)")
    p_convert = sub.add_parser("convert", help="Konvertera PDF:er till markdown")
    p_convert.add_argument("--force", action="store_true", help="Konvertera om allt")
    sub.add_parser("index", help="Bygg ärendeindex (JSONL + SQLite FTS)")
    sub.add_parser("all", help="fetch + convert + index")
    sub.add_parser("serve", help="Starta MCP-servern (stdio)")
    args = parser.parse_args()

    if args.cmd == "fetch":
        from . import fetch

        return fetch.run()
    if args.cmd == "diagnose":
        from . import diagnose

        return diagnose.run()
    if args.cmd == "convert":
        from . import convert

        return convert.run(force=args.force)
    if args.cmd == "index":
        from . import extract

        return extract.run()
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
