"""Wer ist in einer Bekanntmachung Bieter, wer Gewinner - und was wissen wir?

=== WARUM DIESES MODUL EIGENSTAENDIG IST ===
Die Regel, wie aus einer OCDS-Bekanntmachung Firmen werden, brauchen zwei
Stellen mit voellig verschiedenem Zweck:

  src/longlist/build.py   Aufgabe 1: das Marktuniversum
  src/sources/dovs.py     Aufgabe 2: das woechentliche Signal

Als die Regel nur in build.py stand, sah Aufgabe 1 die ganze Bieterseite und
Aufgabe 2 nur die benannten Gewinner. Gemessen am 23.09.2026 an 17.185
IT-Releases aus 12 Monaten:

    Zuschlagszeilen mit benanntem Gewinner :   751
    Bieterzeilen (tender.tenderers)        : 5.735   -> Faktor 7,6

Konkret hiess das: Der Signaltyp "rahmenvertrag_laeuft_aus" haette 3 statt 67
Treffer geliefert. Eine Longlist, deren Signalmotor nur ein Siebtel derselben
Longlist sieht, ist keine Pipeline, sondern zwei Programme mit demselben Namen.

=== DIE FACHLICHE REGEL ===
tender.tenderers fuehrt die namentlich bekannten Bieter. Ob jemand gewonnen
hat, steht dort NICHT - das muss erschlossen werden:

  1. Steht die Firma unter awards[].suppliers        -> Gewinner, benannt
  2. Ist sie der EINZIGE Bieter einer Zuschlags-
     bekanntmachung ohne Gewinnerangabe              -> Gewinner, erschlossen
  3. Steht daneben ein anderer benannter Gewinner    -> unterlegen
  4. Mehrere Bieter, kein Gewinner benannt           -> Ausgang offen

Fall 2 ist der haeufigste und war die gefaehrlichste Falle: 3.987 der 4.309
Bekanntmachungen ohne Gewinnerangabe haben genau einen Bieter. Wer die
pauschal als "hat geboten und verloren" fuehrt, verkauft eine erfundene
Eigenschaft - und zwar mit amtlicher Beleg-URL daneben.

=== WAS DER FEED NICHT HERGIBT ===
Von 441 Bekanntmachungen, die Bieter UND Gewinner benennen, sind die beiden
Listen in 438 Faellen identisch. Unterlegene Wettbewerber werden also
praktisch nicht veroeffentlicht: In 12 Monaten fanden sich 3 Faelle.
Das Systemhaus, das zwoelfmal bietet und nie gewinnt, bleibt hier unsichtbar.
Der Weg dorthin fuehrt ueber Vergabekammer-Entscheidungen - siehe README,
Zwei-Wochen-Plan.
"""
from __future__ import annotations

from src.resolve.normalize import normalize_company, split_consortium, strip_role_prefix


def clean_name(value: str | None) -> str:
    """Firmenname ohne angehaengte Anschrift und ohne Rollenpraefix.

    Manche Plattformen kleben beides an:
        "&effect data solutions GmbH\\nPasteurstr. 34\\n10407 Berlin"
        "Mitglied 1: cimt consulting ag"
    Ungefiltert wandert die Strasse in den company_id-Key und dieselbe Firma
    erscheint zweimal.
    """
    return strip_role_prefix((value or "").split("\n")[0].strip())


def winner_keys(rel: dict) -> set[str]:
    """Normalisierte Namen aller benannten Zuschlagsempfaenger des Releases."""
    return {
        normalize_company(m)
        for a in (rel.get("awards") or [])
        for s in (a.get("suppliers") or [])
        for m in split_consortium(clean_name(s.get("name")))[0]
    }


def bidder_parties(rel: dict) -> list[dict]:
    """Bieter des Releases, die NICHT schon als Gewinner benannt sind.

    Rueckgabe je Eintrag: {party, name, outcome, bidder_count}
    outcome: alleinbieter_gewonnen | unterlegen | offen
    """
    tender = rel.get("tender") or {}
    named = [t for t in (tender.get("tenderers") or []) if t.get("name")]
    if not named:
        return []

    won = winner_keys(rel)
    n_tenderers = tender.get("numberOfTenderers")
    is_award_notice = bool(rel.get("awards")) or "award" in (rel.get("tag") or [])

    if is_award_notice and not won and len(named) == 1 and n_tenderers in (1, None):
        outcome = "alleinbieter_gewonnen"
    elif won:
        outcome = "unterlegen"
    else:
        outcome = "offen"

    out: list[dict] = []
    for party in named:
        name = clean_name(party.get("name"))
        if not name:
            continue
        out.append({"party": party, "name": name, "outcome": outcome,
                    "bidder_count": n_tenderers})
    return out


def lot_end_dates(tender: dict) -> dict[str, str | None]:
    """Vertragsenden je Los.

    Gemessen am 23.09.2026 in 20.000 Releases:
        awards[].contractPeriod       ->      0 Treffer
        tender.lots[].contractPeriod  -> 15.716 Treffer
    Die erste Fassung las das Award-Feld und der Signaltyp
    "rahmenvertrag_laeuft_aus" feuerte nie - ohne Fehlermeldung, weil ein
    leeres Feld genauso aussieht wie "kein Vertragsende".
    """
    return {
        lot["id"]: (lot.get("contractPeriod") or {}).get("endDate")
        for lot in (tender.get("lots") or []) if lot.get("id")
    }
