"""Steg 1: Hitta och ladda ned protokoll-PDF:er från jonkoping.se.

Genomsöker seedsidorna efter länkar till /download/-PDF:er vars länktext
eller filnamn innehåller "protokoll" och nämndens namn. Nedladdade filer
bokförs i data/pdf/manifest.json så att samma fil inte hämtas igen.
"""

import json
import re
import sys
import unicodedata
from urllib.parse import unquote, urljoin

import httpx
from bs4 import BeautifulSoup

from . import config

DATE_RE = re.compile(r"(20\d{2})[-_. ]?(\d{2})[-_. ]?(\d{2})")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text


def find_pdf_links(html: str, base_url: str, namnd: str) -> dict[str, str]:
    """Returnerar {url: länktext} för protokoll-PDF:er som hör till nämnden."""
    soup = BeautifulSoup(html, "html.parser")
    namnd_words = [w for w in re.split(r"\W+", namnd.lower()) if len(w) > 3]
    links: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = " ".join(a.get_text(" ", strip=True).split())
        haystack = (unquote(href) + " " + text).lower()
        if not href.lower().split("?")[0].endswith(".pdf") and "/download/" not in href:
            continue
        if not re.search(config.PROTOKOLL_PATTERN, haystack):
            continue
        # På samlingssidor (t.ex. anslagstavlan) blandas alla nämnder; kräv
        # att åtminstone ett ord ur nämndnamnet förekommer.
        if not any(w in haystack for w in namnd_words):
            continue
        links[href] = text or unquote(href).rsplit("/", 1)[-1]
    return links


def extract_date(url: str, text: str) -> str | None:
    m = DATE_RE.search(unquote(url)) or DATE_RE.search(text)
    return "-".join(m.groups()) if m else None


def load_manifest() -> dict:
    if config.MANIFEST.exists():
        return json.loads(config.MANIFEST.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def run() -> int:
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    new_count = 0
    client = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30
    )
    for namnd, seeds in config.SEEDS.items():
        for seed in seeds:
            try:
                page = client.get(seed)
                page.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"VARNING: kunde inte hämta {seed}: {exc}", file=sys.stderr)
                continue
            for url, text in find_pdf_links(page.text, seed, namnd).items():
                if url in manifest:
                    continue
                datum = extract_date(url, text)
                name = f"{slugify(namnd)}-{datum or slugify(text)[:60]}.pdf"
                dest = config.PDF_DIR / name
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    print(f"VARNING: kunde inte hämta {url}: {exc}", file=sys.stderr)
                    continue
                if not resp.content.startswith(b"%PDF"):
                    print(f"VARNING: {url} är ingen PDF, hoppar över", file=sys.stderr)
                    continue
                dest.write_bytes(resp.content)
                manifest[url] = {
                    "fil": name,
                    "namnd": namnd,
                    "datum": datum,
                    "lanktext": text,
                }
                new_count += 1
                print(f"Hämtade: {name}")
    save_manifest(manifest)
    print(f"Klart: {new_count} nya protokoll, {len(manifest)} totalt i manifestet.")
    return 0
