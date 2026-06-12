"""Steg 1: Hitta och ladda ned protokoll-PDF:er från jonkoping.se.

Nämndens protokoll ligger i ett SiteVision-mappträd: nämndsidan länkar till
årsmappar (2016–), varje årsmapp till månadsmappar, och i månadsmapparna
ligger protokoll-PDF:erna. Sidorna är server-renderade, så vi crawlar trädet
rekursivt: följ alla ?folder=-länkar inom nämndens sökväg och samla alla
PDF:er vars namn innehåller "protokoll".

Nedladdade filer bokförs i data/pdf/manifest.json så att samma fil inte
hämtas igen.
"""

import json
import re
import sys
import time
import unicodedata
from urllib.parse import parse_qs, unquote, urljoin, urlparse, urlsplit

import httpx
from bs4 import BeautifulSoup

from . import config

DATE_RE = re.compile(r"(20\d{2})[-_. ]?(\d{2})[-_. ]?(\d{2})")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text


def folder_id(url: str) -> str | None:
    """SiteVision-mappens id, t.ex. '19.5d10a33b...' ur ?folder=..."""
    values = parse_qs(urlparse(url).query).get("folder")
    return values[0] if values else None


def base_path(url: str) -> str:
    """Sökväg utan ;jsessionid=... så att samma sida normaliseras lika."""
    path = urlsplit(url).path
    return path.split(";", 1)[0]


def is_pdf_link(href: str) -> bool:
    low = href.lower().split("?")[0]
    return low.endswith(".pdf") or "/download/" in href


def extract_date(url: str, text: str) -> str | None:
    m = DATE_RE.search(unquote(url)) or DATE_RE.search(text)
    return "-".join(m.groups()) if m else None


def crawl(client: httpx.Client, namnd: str, root_url: str) -> dict[str, str]:
    """Returnerar {pdf_url: länktext} för protokoll under nämndens rotsida."""
    root_path = base_path(root_url)
    seen_folders: set[str] = set()
    queue: list[str] = [root_url]
    pdfs: dict[str, str] = {}
    sidor = 0

    while queue and sidor < config.MAX_SIDOR:
        url = queue.pop()
        sidor += 1
        try:
            resp = client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"VARNING: kunde inte hämta {url}: {exc}", file=sys.stderr)
            continue
        time.sleep(config.PAUS_SEKUNDER)

        for a in BeautifulSoup(resp.text, "html.parser").find_all("a", href=True):
            href = urljoin(url, a["href"])
            text = " ".join(a.get_text(" ", strip=True).split())
            if is_pdf_link(href):
                haystack = (unquote(href) + " " + text).lower()
                if re.search(config.PROTOKOLL_PATTERN, haystack):
                    pdfs.setdefault(href, text or unquote(href).rsplit("/", 1)[-1])
                continue
            fid = folder_id(href)
            # Följ bara mappar inom nämndens egen sökväg, en gång var.
            if fid and fid not in seen_folders and base_path(href) == root_path:
                seen_folders.add(fid)
                queue.append(href)

    print(f"  {namnd}: {sidor} sidor genomsökta, {len(pdfs)} protokoll-PDF:er.")
    return pdfs


def load_manifest() -> dict:
    if config.MANIFEST.exists():
        return json.loads(config.MANIFEST.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def unique_name(namnd: str, datum: str | None, text: str, taken: set[str]) -> str:
    base = f"{slugify(namnd)}-{datum or slugify(text)[:50] or 'protokoll'}"
    name = f"{base}.pdf"
    n = 2
    while name in taken:
        name = f"{base}-{n}.pdf"
        n += 1
    return name


def run() -> int:
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    taken = {info["fil"] for info in manifest.values()}
    new_count = 0
    client = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30
    )
    for namnd, root_url in config.NAMND_ROTSIDOR.items():
        for url, text in crawl(client, namnd, root_url).items():
            if url in manifest:
                continue
            datum = extract_date(url, text)
            name = unique_name(namnd, datum, text, taken)
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"VARNING: kunde inte hämta {url}: {exc}", file=sys.stderr)
                continue
            if not resp.content.startswith(b"%PDF"):
                print(f"VARNING: {url} är ingen PDF, hoppar över", file=sys.stderr)
                continue
            (config.PDF_DIR / name).write_bytes(resp.content)
            taken.add(name)
            manifest[url] = {
                "fil": name,
                "namnd": namnd,
                "datum": datum,
                "lanktext": text,
            }
            new_count += 1
            print(f"Hämtade: {name}")
            time.sleep(config.PAUS_SEKUNDER)
    save_manifest(manifest)
    print(f"Klart: {new_count} nya protokoll, {len(manifest)} totalt i manifestet.")
    return 0
