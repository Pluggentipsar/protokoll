"""Skapar ett syntetiskt sammanträdesprotokoll som PDF för att testa
pipelinen utan nätverksåtkomst. Härmar strukturen i Jönköpings kommuns
protokoll (sidhuvud, §-rubriker, beslutssatser, Dnr)."""

from pathlib import Path

import pymupdf

PAGES = [
    """JÖNKÖPINGS KOMMUN
Barn- och utbildningsnämnden
SAMMANTRÄDESPROTOKOLL
2025-04-15

Plats och tid: Rumlaborgssalen, Stadshuset Huskvarna, kl. 8.15

§ 41 Fastställande av dagordning

Beslut
Barn- och utbildningsnämnden beslutar
att fastställa dagordningen.

§ 42 Skolskjutsreglemente, revidering
Dnr BUN 2025/123

Sammanfattning
Utbildningsförvaltningen har tagit fram ett förslag till reviderat
skolskjutsreglemente. Avståndsgränsen för årskurs F-3 föreslås
sänkas från 3 km till 2 km.

Beslut
Barn- och utbildningsnämnden beslutar
att anta reviderat skolskjutsreglemente att gälla från 2025-08-01.
""",
    """§ 43 Budgetuppföljning per mars 2025
Dnr BUN 2025/87

Sammanfattning
Prognosen för helåret visar ett underskott om 12 mnkr, främst inom
grundskolan till följd av ökade kostnader för särskilt stöd.

Beslut
Barn- och utbildningsnämnden beslutar
att godkänna budgetuppföljningen samt
att ge förvaltningen i uppdrag att återkomma med åtgärdsplan.

Reservation
Ledamot X reserverar sig mot beslutet.
""",
]


def make(dest: Path) -> Path:
    doc = pymupdf.open()
    for text in PAGES:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=10)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest))
    return dest


if __name__ == "__main__":
    print(make(Path("data/pdf/barn-och-utbildningsnamnden-2025-04-15.pdf")))
