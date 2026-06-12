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
    "protokoll-pipeline/0.1 (kommunintern sokning av namndprotokoll; "
    "kontakt: utbildningsforvaltningen Jonkopings kommun)"
)

# Nämndens arkivrotsida. fetch crawlar mappträdet (år -> månad -> PDF) under
# denna sökväg. Lägg till fler nämnder här – samma logik gäller alla.
NAMND_ROTSIDOR: dict[str, str] = {
    "Barn- och utbildningsnämnden": (
        "https://www.jonkoping.se/kommun--politik/kommunens-organisation/"
        "politiska-namnder/barn--och-utbildningsnamnden"
    ),
}

# Länktext/filnamn måste matcha detta för att en PDF ska laddas ned.
# Håller hämtningen till protokoll (inte reglemente, kallelser, tjänsteskrivelser).
PROTOKOLL_PATTERN = r"protokoll"

# Skyddsräcken för crawlningen.
MAX_SIDOR = 500
PAUS_SEKUNDER = 0.4
