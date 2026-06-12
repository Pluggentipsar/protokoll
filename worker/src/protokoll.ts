// Ren söklogik över det inbäddade ärendeindexet. Korpusen är liten
// (~1300 ärenden) så sökning i minnet är snabbt och kräver ingen databas.
// Samma beteende som Python-sidan: prefixmatchning, rubrik viktas högre.

import arenden from "../data/arenden.json";

export interface Arende {
  id: number;
  namnd: string;
  datum: string | null;
  paragraf: number;
  rubrik: string;
  dnr: string | null;
  beslut: string | null;
  fil: string;
  kalla: string | null;
  text: string;
}

const DATA = arenden as Arende[];

function tokenize(q: string): string[] {
  return q
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((w) => w.length > 0);
}

function score(a: Arende, terms: string[]): number {
  const rubrik = a.rubrik.toLowerCase();
  const text = (a.rubrik + " " + a.text + " " + (a.beslut ?? "")).toLowerCase();
  let s = 0;
  for (const t of terms) {
    if (rubrik.includes(t)) s += 10;
    const m = text.match(new RegExp(escapeRe(t), "g"));
    if (m) s += m.length;
  }
  return s;
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function snippet(text: string, terms: string[], len = 240): string {
  const lower = text.toLowerCase();
  let at = -1;
  for (const t of terms) {
    const i = lower.indexOf(t);
    if (i !== -1 && (at === -1 || i < at)) at = i;
  }
  const start = at === -1 ? 0 : Math.max(0, at - 60);
  return (start > 0 ? "… " : "") + text.slice(start, start + len).trim() + " …";
}

export function sok(
  fraga: string,
  franDatum = "",
  tillDatum = "",
  maxTraffar = 10,
): Arende[] & { snippetFor?: (a: Arende) => string } {
  const terms = tokenize(fraga);
  if (terms.length === 0) return [];
  let cand = DATA.filter((a) => score(a, terms) > 0);
  if (franDatum) cand = cand.filter((a) => (a.datum ?? "") >= franDatum);
  if (tillDatum) cand = cand.filter((a) => (a.datum ?? "") <= tillDatum);
  cand.sort((a, b) => score(b, terms) - score(a, terms));
  return cand.slice(0, Math.max(1, Math.min(maxTraffar, 50)));
}

export function utdrag(a: Arende, fraga: string): string {
  return snippet(a.text, tokenize(fraga));
}

export function hamtaArende(id: number): Arende | undefined {
  return DATA.find((a) => a.id === id);
}

export interface Sammantrade {
  namnd: string;
  datum: string | null;
  fil: string;
  antal_arenden: number;
  paragrafer: string;
}

export function listaSammantraden(): Sammantrade[] {
  const byFil = new Map<string, Arende[]>();
  for (const a of DATA) {
    const arr = byFil.get(a.fil) ?? [];
    arr.push(a);
    byFil.set(a.fil, arr);
  }
  const out: Sammantrade[] = [];
  for (const [fil, arr] of byFil) {
    const ps = arr.map((a) => a.paragraf);
    out.push({
      namnd: arr[0].namnd,
      datum: arr[0].datum,
      fil,
      antal_arenden: arr.length,
      paragrafer: `${Math.min(...ps)}-${Math.max(...ps)}`,
    });
  }
  out.sort((a, b) => (a.datum ?? "").localeCompare(b.datum ?? ""));
  return out;
}
