"""Stufe 2 des Domain-Waterfalls: die offenen Zeilen fuer Clay exportieren.

=== WO DAS IM WATERFALL STEHT ===
    Stufe 0   contactPoint der Bieterpartei in der Bekanntmachung
              -> 1.487 von 2.458 (60,5 %), Quelle und Konfidenz je Zeile
    Stufe 1   Apollo Organizations Lookup (creditfrei)
    Stufe 2   KI-Recherche in Clay          <- DIESE DATEI
              -> nur die restlichen 971 Zeilen (39,5 %)
    Stufe 3   Impressum-Verifikation
    Stufe 4   Review-Queue von Hand

Die Reihenfolge ist keine Geschmacksfrage. Stufe 0 ist die staerkste
Quelle, die es gibt: Das Unternehmen hat die Adresse der Vergabestelle
SELBST gemeldet, und sie steht in derselben Bekanntmachung wie der
Zuschlagsbeleg. Was danach kommt, ist Ableitung.

=== WARUM DIESE DATEI UEBERHAUPT EXISTIERT ===
Man koennte die gesamte Longlist in Clay laden und den KI-Schritt ueber
einen Conditional Run auf leere Domains beschraenken. Das funktioniert -
kostet aber 2.458 Zeilen Tabellenplatz fuer 971 Zeilen Arbeit, und jeder
spaetere Blick auf die Tabelle muss den Filter mitdenken.

Sauberer ist, die Teilmenge zu exportieren, die Arbeit braucht. Der
Rueckweg laeuft ueber denselben `retier`-Pfad wie jeder andere
Enrichment-Export.

=== DIE SPALTE, DIE UEBER ALLES ENTSCHEIDET: ort ===
Eine KI, die nur den Firmennamen bekommt, raet. Gemessen an der frueheren
namensbasierten Aufloesung: 8 von 12 Zeilen im Longtail falsch.

    EOMI AG, Hamburg           -> eominnesota.org  (Entrepreneurs Org. Minnesota)
    msg systems ag, Ismaning   -> msg-systems.ro   (Rumaenien)
    Netlight Consulting, FFM   -> domainflotta.hu  (Ungarn)
    Dedalus HealthCare, Bonn   -> dedalus.at       (Oesterreich)

Bei internationalen Marken steht der Firmenname im Impressum JEDER
Landesgesellschaft. Der Diskriminator ist der Ort aus der
Bekanntmachung - er steht nur im Impressum der Gesellschaft, an die der
Zuschlag ging. Deshalb geht `ort` mit in den Export und in den Prompt.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA = Path("data")
QUELLE = DATA / "longlist_markt.csv"
ZIEL = DATA / "clay_domain_todo.csv"

# Nur diese Spalten. Clay-Tabellen werden unuebersichtlich, und jede Spalte,
# die der Prompt nicht braucht, ist eine, die jemand spaeter falsch verknuepft.
FELDER = [
    "company_id",        # Rueckschluessel fuer retier - NICHT entfernen
    "legal_name",        # Eingabe fuer den Prompt
    "ort",               # Eingabe fuer den Prompt, der Diskriminator
    "plz",
    "tier",              # fuer den Conditional Run: erst A, dann B
    "verfahren_12m",     # Prioritaet innerhalb eines Tiers
    "cpv_kurz",          # Kontext fuer die KI: welche Art IT
    "proof_url",         # Gegenprobe von Hand: passt die gefundene Firma?
]


# CPV-Profile sind bis zu 10 Codes lang. Die ersten drei genuegen als
# Kontext ("worum geht es ueberhaupt"), und `main_cpv` ist in der Longlist
# bei allen 971 offenen Zeilen leer - eine Spalte, die nie etwas enthaelt,
# ist in einer Clay-Tabelle nur Rauschen.
def _cpv_kurz(profil: str, n: int = 3) -> str:
    return ";".join([c for c in profil.split(";") if c][:n])


def main() -> int:
    if not QUELLE.exists():
        raise SystemExit(f"{QUELLE} fehlt - erst 'make longlist' und 'make domains'")

    rows = list(csv.DictReader(QUELLE.open(encoding="utf-8-sig")))
    offen = [r for r in rows if not (r.get("domain") or "").strip()]

    # Nach Tier und Verfahrenszahl sortieren. Wer den Lauf nach 300 Zeilen
    # abbricht, hat dann die wertvollsten 300 - nicht die alphabetisch
    # ersten.
    rang = {"A": 0, "B": 1, "C": 2}

    def sortkey(r: dict) -> tuple:
        try:
            verf = -int(r.get("participations_total") or 0)
        except ValueError:
            verf = 0
        return (rang.get(r.get("tier", ""), 9), verf, r.get("legal_name", "").lower())

    offen.sort(key=sortkey)

    out = [{
        "company_id": r["company_id"],
        "legal_name": r["legal_name"],
        "ort": r.get("city") or "",
        "plz": r.get("postal_code") or "",
        "tier": r.get("tier") or "",
        "verfahren_12m": r.get("participations_total") or "",
        "cpv_kurz": _cpv_kurz(r.get("cpv_profile") or ""),
        "proof_url": r.get("proof_url") or "",
    } for r in offen]

    if not out:
        print("Keine offenen Domains - Stufe 2 wird nicht gebraucht.")
        return 0

    with ZIEL.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FELDER, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(out)

    ohne_ort = sum(1 for r in out if not r["ort"])
    verteilung = {t: sum(1 for r in out if r["tier"] == t) for t in ("A", "B", "C")}

    print(f"{ZIEL}: {len(out)} Zeilen ohne Domain "
          f"(von {len(rows)} in der Longlist)")
    print(f"  Tier: {verteilung}")
    print(f"  ohne Ortsangabe: {ohne_ort}"
          f"{'  <- bei diesen raet die KI, Treffer von Hand pruefen' if ohne_ort else ''}")
    print()
    print("  Naechste Schritte:")
    print("    1. Datei in Clay hochladen (CSV-Import)")
    print("    2. Spalte 'Domain finden' anlegen, Prompt aus")
    print("       docs/clay_domain_waterfall.md")
    print("    3. Conditional Run:  {{domain}} is empty")
    print("    4. Export zurueckspielen:")
    print("       python3 -m src.cli retier --from <clay-export.csv>")
    print("       (domain_source muss 'clay_ai' sein - sonst wird die")
    print("        Vermutung wie eine amtliche Angabe behandelt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
