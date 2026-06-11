"""Steg 2: Konvertera PDF:er till markdown med YAML-frontmatter.

Använder pymupdf4llm för layoutmedveten textextraktion. Varje protokoll
blir en .md-fil i data/md/ med metadata (nämnd, datum, källa) i toppen —
ett format som fungerar bra både för SharePoint/Copilot-grounding och
för det lokala sökindexet.
"""

import sys

import pymupdf
import pymupdf4llm

from . import config
from .fetch import load_manifest


def pdf_to_markdown(pdf_path) -> str:
    return pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)


def has_text_layer(pdf_path) -> bool:
    with pymupdf.open(str(pdf_path)) as doc:
        return any(page.get_text().strip() for page in doc)


def frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ("namnd", "datum", "kalla", "fil"):
        if meta.get(key):
            lines.append(f'{key}: "{meta[key]}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def run(force: bool = False) -> int:
    config.MD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    by_file = {info["fil"]: dict(info, kalla=url) for url, info in manifest.items()}
    converted = skipped = 0
    for pdf_path in sorted(config.PDF_DIR.glob("*.pdf")):
        md_path = config.MD_DIR / (pdf_path.stem + ".md")
        if md_path.exists() and not force:
            skipped += 1
            continue
        if not has_text_layer(pdf_path):
            print(
                f"VARNING: {pdf_path.name} saknar textlager (inskannad?) - "
                "behöver OCR, hoppar över",
                file=sys.stderr,
            )
            continue
        meta = by_file.get(pdf_path.name, {"fil": pdf_path.name})
        body = pdf_to_markdown(pdf_path)
        md_path.write_text(frontmatter(meta) + body)
        converted += 1
        print(f"Konverterade: {md_path.name}")
    print(f"Klart: {converted} konverterade, {skipped} redan klara.")
    return 0
