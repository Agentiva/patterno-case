"""Verifikation aufgeloester Domains.

=== WARUM DIESES MODUL EXISTIERT (Messung vom 23.09.2026) ===
Die Domain-Resolution laeuft zweistufig:
  Stufe 1: Apollo-Lookup mit Ortsfilter Deutschland  -> praezise, aber loechrig
  Stufe 2: ohne Ortsfilter, verkuerzter Name         -> mehr Treffer, viel Muell

An einer ersten Stichprobe bekannter Marken (Bechtle, CANCOM, Controlware,
Materna, iteratec) sah Stufe 2 grossartig aus: 4 von 5 korrekt, Gesamtquote
77 %. Diese Stichprobe war verzerrt - grosse Marken sind in Apollo sauber
gepflegt.

Im Longtail kippt das Bild. Von 12 Stufe-2-Aufloesungen waren 8 falsch:
  Dedalus HealthCare GmbH (Bonn)   -> dedalus.at            Oesterreich
  msg systems ag (Ismaning)        -> msg-systems.ro        Rumaenien
  EOMI AG (Hamburg)                -> eominnesota.org       Entrepreneurs
                                                            Organization Minnesota
  Netlight Consulting GmbH (FFM)   -> domainflotta.hu       Ungarn
  EduXpert GmbH (Regensburg)       -> eduxpert.co.uk        UK
  RICOH Deutschland GmbH           -> ricoh-documentcenter.de  falsche Teileinheit
  Sopra Steria SE (Hamburg)        -> soprasteria.com       franz. Konzern
  Eviden Germany GmbH (Berlin)     -> eviden.com            Konzern

Ein unbesehen uebernommener Stufe-2-Treffer schickt also Post nach Minnesota.
Deshalb: Stufe 2 liefert nur noch KANDIDATEN. Erst dieses Modul entscheidet.

=== REGEL ===
Der Zuschlag ging an einen deutschen Rechtstraeger. Also muss die Domain
zu einem deutschen Auftritt gehoeren. Belege dafuer, absteigend:
  1. .de-Domain                                     -> stark
  2. Apollo-Sitzland Deutschland                    -> stark
  3. Name enthaelt den Ortsnamen aus der Vergabe    -> mittel
  4. nichts davon                                   -> ablehnen, Review-Queue
"""
from __future__ import annotations

from src.resolve.normalize import fold, normalize_company

# TLDs, die ein deutsches Unternehmen praktisch nie als Hauptauftritt nutzt,
# wenn der Zuschlag an eine deutsche Gesellschaft ging.
FOREIGN_TLDS = {
    "at": "Oesterreich", "ch": "Schweiz", "ro": "Rumaenien", "hu": "Ungarn",
    "pl": "Polen", "cz": "Tschechien", "uk": "UK", "fr": "Frankreich",
    "es": "Spanien", "it": "Italien", "nl": "Niederlande", "se": "Schweden",
    "dk": "Daenemark", "no": "Norwegen", "fi": "Finnland", "in": "Indien",
    "us": "USA", "org": "Non-Profit", "net": "generisch",
}

# Generische TLDs sind neutral - erst der Sitz entscheidet.
NEUTRAL_TLDS = {"com", "eu", "io", "tech", "group"}


def tld_of(domain: str) -> str:
    return (domain or "").rsplit(".", 1)[-1].lower()


def verify(award_name: str, award_city: str | None, candidate: dict,
           stage: int) -> dict:
    """Entscheidet, ob ein Lookup-Treffer uebernommen wird.

    candidate: {name, domain, country?}
    stage:     1 = mit Ortsfilter, 2 = ohne
    """
    domain = (candidate.get("domain") or "").lower()
    cand_name = candidate.get("name") or ""
    country = (candidate.get("country") or "").strip().lower()
    tld = tld_of(domain)

    if not domain:
        return _reject("kein Domain-Treffer", 0.0)

    signals: list[str] = []
    score = 0.0

    # Stufe 1 hatte bereits den Ortsfilter Deutschland an -> starker Beleg.
    if stage == 1:
        signals.append("Stufe 1 mit Ortsfilter Deutschland")
        score += 0.45

    if tld == "de":
        signals.append(".de-Domain")
        score += 0.30
    elif tld in FOREIGN_TLDS and stage == 2:
        return _reject(
            f"TLD .{tld} ({FOREIGN_TLDS[tld]}) passt nicht zum deutschen "
            f"Rechtstraeger '{award_name}'", 0.0, domain)
    elif tld in NEUTRAL_TLDS:
        signals.append(f"neutrale TLD .{tld}")
        score += 0.10

    if country in ("germany", "deutschland"):
        signals.append("Apollo-Sitz Deutschland")
        score += 0.25

    # Namensaehnlichkeit: schuetzt vor "EOMI" -> "Entrepreneurs Organization"
    a, b = set(normalize_company(award_name).split()), set(normalize_company(cand_name).split())
    overlap = len(a & b) / max(len(a | b), 1)
    if overlap >= 0.5:
        signals.append(f"Namensueberlappung {overlap:.0%}")
        score += 0.20
    elif overlap < 0.2:
        return _reject(
            f"Name passt nicht: '{cand_name}' vs. '{award_name}' "
            f"(Ueberlappung {overlap:.0%})", 0.0, domain)

    if award_city and fold(award_city.split()[0]) in fold(cand_name):
        signals.append("Ortsname im Firmennamen")
        score += 0.10

    score = round(min(score, 1.0), 3)
    accepted = score >= 0.60
    return {
        "accepted": accepted,
        "domain": domain if accepted else "",
        "candidate_domain": domain,
        "confidence": score,
        "stage": stage,
        "signals": "; ".join(signals),
        "reject_reason": "" if accepted else f"Confidence {score} unter Schwelle 0.60",
    }


def _reject(reason: str, score: float, domain: str = "") -> dict:
    return {
        "accepted": False, "domain": "", "candidate_domain": domain,
        "confidence": score, "stage": 0, "signals": "",
        "reject_reason": reason,
    }
