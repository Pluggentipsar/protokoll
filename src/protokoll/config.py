"""Gemensam konfiguration för pipelinen."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PDF_DIR = ROOT / "data" / "pdf"
MD_DIR = ROOT / "data" / "md"
INDEX_DIR = ROOT / "data" / "index"
MANIFEST = PDF_DIR / "manifest.json"
DB_PATH = INDEX_DIR / "protokoll.db"
ARENDEN_JSONL = INDEX_DIR / "arenden.jsonl"

USER_AGENT = (
    "protokoll-pipeline/0.1 (kommunintern sökning av nämndprotokoll; "
    "kontakt: utbildningsförvaltningen Jönköpings kommun)"
)

# Sidor som genomsöks efter protokoll-PDF:er. Lägg till fler nämnder här.
SEEDS: dict[str, list[str]] = {
    "Barn- och utbildningsnämnden": [
        "https://www.jonkoping.se/kommun--politik/kommunens-organisation/"
        "politiska-namnder/barn--och-utbildningsnamnden",
        "https://www.jonkoping.se/kommun--politik/anslagstavla-for-jonkopings-kommun",
    ],
}

# Länktext/filnamn måste matcha detta för att laddas ned.
PROTOKOLL_PATTERN = r"protokoll"
