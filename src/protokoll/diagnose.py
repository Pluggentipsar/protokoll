"""Diagnoskommando: visa vad fetch faktiskt ser på en sida.

Hjälper att felsöka när 'protokoll fetch' hittar 0 protokoll. Skriver ut
HTTP-status, sidstorlek, alla länkar (text -> url), och iframes (vars
innehåll ofta är ett separat möteshandlingssystem).

Använd standardseedsen:        protokoll diagnose
Eller peka på en valfri sida:  protokoll diagnose <url> [<url> ...]
"""

import sys
from urllib.parse import unquote, urljoin

import httpx
from bs4 import BeautifulSoup

from . import config


def _inspect(client: httpx.Client, url: str) -> None:
    print(f"\n=== {url} ===")
    try:
        resp = client.get(url)
    except httpx.HTTPError as exc:
        print(f"  FEL vid hämtning: {exc}")
        return
    print(f"  HTTP {resp.status_code}, {len(resp.text)} tecken HTML")
    if resp.status_code != 200:
        print("  (första 300 tecken:) " + resp.text[:300].replace("\n", " "))
        return
    soup = BeautifulSoup(resp.text, "html.parser")

    iframes = soup.find_all("iframe", src=True)
    if iframes:
        print(f"  {len(iframes)} iframe(s):")
        for f in iframes:
            print(f"    iframe src: {urljoin(url, f['src'])}")

    links = soup.find_all("a", href=True)
    pdfs = [a for a in links if a["href"].lower().split("?")[0].endswith(".pdf") or "/download/" in a["href"]]
    print(f"  {len(links)} länkar totalt, varav {len(pdfs)} PDF/download.")
    print("  --- alla länkar (text -> url) ---")
    for a in links:
        text = " ".join(a.get_text(" ", strip=True).split()) or "(ingen text)"
        href = urljoin(url, a["href"])
        marker = "  [PDF]" if a in pdfs else ""
        print(f"    {text[:70]!r}{marker}")
        print(f"        -> {unquote(href)}")


def run(urls: list[str] | None = None) -> int:
    targets = urls or [s for seeds in config.SEEDS.values() for s in seeds]
    client = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30
    )
    for url in targets:
        _inspect(client, url)
    return 0
