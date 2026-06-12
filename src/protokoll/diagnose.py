"""Diagnoskommando: visa vad fetch faktiskt ser på seedsidorna.

Hjälper att felsöka när 'protokoll fetch' hittar 0 protokoll. Skriver ut
HTTP-status, sidstorlek, antal länkar totalt, och alla länkar som pekar på
PDF/download — oavsett nämndfilter — med deras länktext.
"""

import sys
from urllib.parse import unquote, urljoin

import httpx
from bs4 import BeautifulSoup

from . import config


def run() -> int:
    client = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30
    )
    for namnd, seeds in config.SEEDS.items():
        for seed in seeds:
            print(f"\n=== {namnd} ===\n{seed}")
            try:
                resp = client.get(seed)
            except httpx.HTTPError as exc:
                print(f"  FEL vid hämtning: {exc}")
                continue
            print(f"  HTTP {resp.status_code}, {len(resp.text)} tecken HTML")
            if resp.status_code != 200:
                print(f"  (sidan svarade inte 200 - första 300 tecken:)")
                print("  " + resp.text[:300].replace("\n", " "))
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            all_links = soup.find_all("a", href=True)
            candidates = []
            for a in all_links:
                href = urljoin(seed, a["href"])
                low = href.lower().split("?")[0]
                if low.endswith(".pdf") or "/download/" in href:
                    text = " ".join(a.get_text(" ", strip=True).split())
                    candidates.append((href, text))
            print(f"  {len(all_links)} länkar totalt, {len(candidates)} PDF/download-länkar")
            for href, text in candidates[:40]:
                print(f"    - text: {text!r}")
                print(f"      url : {unquote(href)}")
            if len(candidates) > 40:
                print(f"    ... och {len(candidates) - 40} till")
    return 0
