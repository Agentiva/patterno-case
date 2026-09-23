"""CPV-Auswertung: ist eine Vergabe wirklich IT - oder nur zufaellig auch?

=== DER FEHLER, DER DIESES MODUL NOETIG MACHT (23.09.2026) ===
Die erste Version filterte: "irgendein CPV im Datensatz beginnt mit 48/72/302..."
Ergebnis: Unter den Top 40 nach Zuschlagsanzahl standen HAHN+KOLB Werkzeuge,
Stuermer Werkzeuge-Maschinen, Huettinger Holzbearbeitungsmaschinen, Hoffmann
Qualitaetswerkzeuge, ETS DIDACTIC, Lucas-Nuelle, STAHLGRUBER, BayWa und
Fronius - allesamt keine IT-Systemhaeuser.

Ursache: eine einzige Rahmenvereinbarung der Handwerkskammer
Niederbayern-Oberpfalz fuer Werkstatt- und Schulausstattung. Sie fuehrt
dutzende CPV-Codes, darunter 30213000 (Laptops) neben Werkzeugmaschinen,
Kabeln und Leuchten. Jeder Lieferant auf diesem Rahmen wurde dadurch als
"IT" markiert.

Erkennungsmerkmal im Nachhinein: identische Zuschlagszahlen (112, 112, 112,
... 72, 72, 72). Das sind nicht 112 gewonnene Verfahren, sondern 112
Zuschlagszeilen EINES Verfahrens.

=== ZWEI KORREKTUREN ===
1. IT muss DOMINANT sein, nicht beilaeufig:
   - Hauptklassifikation (tender.classification) entscheidet, wenn vorhanden
   - sonst muss ein Mindestanteil der CPV-Codes IT sein
2. Verfahren statt Zuschlagszeilen zaehlen: Dedupe ueber die OCID.

Das ist inhaltlich exakt das Problem, das Patterno BID fuer Bieter loest -
"fachfremde Gewerke im Leistungsverzeichnis". Hier trifft es uns selbst.
"""
from __future__ import annotations

from src.config import CPV_IT_PREFIXES

# Anteil IT-CPVs, ab dem eine Vergabe ohne Hauptklassifikation als IT gilt.
# 0.5 ist bewusst streng: Bei einer Mehrlos-Ausschreibung mit 30 Gewerken
# und 2 IT-Losen wollen wir NICHT alle Lieferanten einsammeln.
MIN_IT_SHARE = 0.5


def is_it_cpv(code: str | None) -> bool:
    return bool(code) and any(str(code).startswith(p) for p in CPV_IT_PREFIXES)


def extract_cpv(tender: dict) -> tuple[str | None, list[str]]:
    """Gibt (Hauptklassifikation, alle CPV-Codes) zurueck."""
    main = (tender.get("classification") or {}).get("id")
    codes: list[str] = []
    if main:
        codes.append(str(main))
    for item in tender.get("items") or []:
        cid = (item.get("classification") or {}).get("id")
        if cid:
            codes.append(str(cid))
        for add in item.get("additionalClassifications") or []:
            if add.get("id"):
                codes.append(str(add["id"]))
    for add in tender.get("additionalClassifications") or []:
        if add.get("id"):
            codes.append(str(add["id"]))
    return (str(main) if main else None), codes


def classify(tender: dict) -> dict:
    """Entscheidet, ob eine Vergabe als IT-Vergabe zaehlt - mit Begruendung.

    Die Begruendung wandert in den Export, damit eine Stichprobenpruefung
    nachvollziehen kann, warum ein Datensatz drin ist oder fehlt.
    """
    main, codes = extract_cpv(tender)
    unique = sorted(set(codes))
    it_codes = [c for c in unique if is_it_cpv(c)]
    share = len(it_codes) / len(unique) if unique else 0.0

    if main is not None:
        ok = is_it_cpv(main)
        reason = (f"Hauptklassifikation {main} "
                  f"{'ist' if ok else 'ist nicht'} IT")
    elif not unique:
        ok, reason = False, "keine CPV-Codes im Datensatz"
    else:
        ok = share >= MIN_IT_SHARE
        reason = (f"keine Hauptklassifikation; IT-Anteil "
                  f"{len(it_codes)}/{len(unique)} = {share:.0%} "
                  f"{'>=' if ok else '<'} {MIN_IT_SHARE:.0%}")

    # Warnsignal fuer Mehrlos-Sammelvergaben, auch wenn sie durchkommen:
    # viele Codes bei niedrigem IT-Anteil deutet auf eine Sammelausschreibung
    # mit fachfremden Gewerken hin.
    mixed = len(unique) >= 8 and share < 0.5

    return {
        "is_it": ok,
        "reason": reason,
        "main_cpv": main,
        "it_share": round(share, 3),
        "cpv_count": len(unique),
        "cpv_codes": unique[:12],
        "mixed_lot_warning": mixed,
    }
