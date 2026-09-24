"""Aufgabe 1: Longlist aller relevanten IT-Systemhaeuser - aus Vergabedaten.

KERNENTSCHEIDUNG
Wir bauen die Liste NICHT aus Firmenverzeichnissen, die wir auf
Public-Sector-Bezug filtern, sondern aus Vergabedaten, die wir auf
Systemhaus-Eignung filtern.

Der Unterschied ist der ganze Case. Verzeichnis-first liefert "koennte
relevant sein". Vergabedaten-first liefert "hat am 14.03.2026 Los 2 der
Ausschreibung XY gewonnen, OCID ocds-...". Das ist ein Beleg, kein Attribut -
und genau danach fragt die Aufgabe: "Wie belegst du MIT DATEN, dass ein
Unternehmen an oeffentlichen Vergaben teilnimmt, statt es nur anzunehmen?"

DIE EHRLICHE SCHWAECHE
Zuschlagsbekanntmachungen nennen den GEWINNER, nicht die Verlierer. Ein
Systemhaus, das zwoelfmal bietet und nie gewinnt, ist hier unsichtbar -
obwohl es der beste Patterno-Kunde ueberhaupt waere. Deshalb:
  - Tier C existiert und ist ausdruecklich WERTVOLL, nicht Restkategorie
  - die Coverage-Schaetzung unten quantifiziert die Luecke
  - "Verlierer-Inferenz" ist Vorschlag Nr. 2 fuer die zwei Wochen
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

from src.resolve.cpv import classify
from src.sources.dovs import notice_url
from src.resolve.normalize import (
    check_exclusion, normalize_company, resolution_confidence, split_consortium,
)
from src.resolve.parties import bidder_parties, clean_name, winner_keys

DATA = Path("data")


# --- Beweishierarchie ---------------------------------------------------------
# Jede Zeile der Longlist traegt proof_type + proof_url + proof_date.
# Damit ist die von Patterno angekuendigte Stichprobenpruefung trivial.
PROOF_CONFIDENCE = {
    "P1_zuschlag_24m": 0.95,       # Zuschlag, Gewinner ausdruecklich benannt
    "P1B_bieter_unterlegen": 0.90, # Bieter neben einem anderen Gewinner -> verloren
    "P1C_alleinbieter": 0.85,      # einziger Bieter im Zuschlag -> Gewinner erschlossen
    "P1D_ausgang_offen": 0.88,     # Bieter unter mehreren, kein Gewinner benannt
    "P2_zuschlag_48m": 0.85,       # Zuschlag 24-48 Monate zurueck
    "P3_rahmenvertrag": 0.80,      # laufender Rahmenvertrag / Praequalifikation
    "P4_referenz_website": 0.65,   # namentliche Referenz oeffentlicher AG
    "P5_schwaches_signal": 0.45,   # Public-Landingpage, Zertifikat, Stellenanzeige
    "P6_nur_branche": 0.20,        # nur Branchen-/Groessenpassung -> kein A/B
}

# === DIE BIETERLISTE, UND WARUM SIE VIER BELEGARTEN BRAUCHT ===
#
# Die erste Fassung las ausschliesslich awards[].suppliers - also GEWINNER.
# Die eigene Modulbeschreibung nannte das die ehrliche Schwaeche: Wer zwoelfmal
# bietet und nie gewinnt, ist unsichtbar, obwohl genau er den Schmerz hat, den
# Patterno loest.
#
# tender.tenderers schliesst diese Luecke. Gemessen am 23.09.2026 an 17.185
# IT-Releases aus 12 Monaten:
#   Releases mit benannten Bietern  : 4.750
#   davon mit benanntem Gewinner    :   441
#   davon ohne benannten Gewinner   : 4.309
#
# ACHTUNG, HIER LAG EINE FALLE. Von den 4.309 Bekanntmachungen ohne
# Gewinnerangabe haben 3.987 genau EINEN Bieter (numberOfTenderers = 1).
# Ein einziger Bieter in einer ZUSCHLAGSbekanntmachung ist der Gewinner - die
# veroeffentlichende Plattform hat ihn nur in die Bieterrolle gemappt statt
# unter awards[].suppliers. Haetten wir alle Bieter ohne Gewinnerangabe als
# "hat geboten und verloren" gefuehrt, waere die Haelfte der Longlist mit
# einer frei erfundenen Eigenschaft in die Ansprache gegangen.
#
# Deshalb vier getrennte Belegarten statt einer. Der Unterschied ist nicht
# akademisch, er entscheidet den ersten Satz:
#   P1  Gewinner benannt        -> "Sie haben ... gewonnen"
#   P1C einziger Bieter         -> dito, aber erschlossen: Quelle mitschicken
#   P1B Bieter, anderer gewann  -> "Sie haben geboten und nicht den Zuschlag bekommen"
#   P1D Ausgang offen           -> "Sie haben sich beteiligt" - mehr geben die Daten nicht her


@dataclass
class Company:
    legal_name: str
    normalized: str
    city: str | None = None
    postal_code: str | None = None
    supplier_ids: set[str] = field(default_factory=set)
    awards: list[dict] = field(default_factory=list)
    bids: list[dict] = field(default_factory=list)   # geboten, Ausgang offen
    consortium_only: bool = True     # bisher nur als ARGE-Mitglied gesehen
    sources: set[str] = field(default_factory=set)

    # wird extern angereichert (siehe docs/waterfalls.md)
    domain: str | None = None
    domain_confidence: float = 0.0
    domain_source: str | None = None
    employees: int | None = None

    @property
    def award_count(self) -> int:
        """Anzahl VERFAHREN, nicht Zuschlagszeilen.

        Eine Mehrlos-Rahmenvereinbarung erzeugt dutzende Zuschlagszeilen mit
        derselben OCID. Wer die zaehlt, haelt einen einzigen Rahmenvertrag
        faelschlich fuer 112 gewonnene Verfahren.
        """
        return len({a["ocid"] for a in self.awards if a.get("ocid")})

    @property
    def award_rows(self) -> int:
        return len(self.awards)

    def _bid_ocids(self, outcome: str) -> set[str]:
        return {b["ocid"] for b in self.bids
                if b.get("ocid") and b.get("outcome") == outcome}

    @property
    def sole_bidder_wins(self) -> int:
        """Einziger Bieter in einer Zuschlagsbekanntmachung -> Gewinn,
        erschlossen statt benannt."""
        return len(self._bid_ocids("alleinbieter_gewonnen"))

    @property
    def lost_count(self) -> int:
        """Geboten, waehrend ein anderer benannter Bieter den Zuschlag bekam."""
        return len(self._bid_ocids("unterlegen"))

    @property
    def open_count(self) -> int:
        """Geboten, Ausgang aus den Daten nicht ableitbar."""
        return len(self._bid_ocids("offen"))

    @property
    def wins_total(self) -> int:
        """Benannte plus erschlossene Zuschlaege."""
        return self.award_count + self.sole_bidder_wins

    @property
    def participation_count(self) -> int:
        """Verfahren mit belegter Teilnahme, gewonnen oder nicht."""
        return len({r["ocid"] for r in self.rows if r.get("ocid")})

    @property
    def last_bid(self) -> str | None:
        dates = [b["date"] for b in self.bids if b.get("date")]
        return max(dates) if dates else None

    @property
    def rows(self) -> list[dict]:
        """Alle Teilnahmebelege, unabhaengig vom Ausgang."""
        return self.awards + self.bids

    @property
    def from_mixed_lot_only(self) -> bool:
        """Nur ueber Sammelvergaben mit fachfremden Gewerken belegt -
        schwacher IT-Beleg, gehoert nicht nach Tier A/B."""
        rows = self.rows
        return bool(rows) and all(r.get("mixed_lot") for r in rows)

    @property
    def last_award(self) -> str | None:
        dates = [a["date"] for a in self.awards if a.get("date")]
        return max(dates) if dates else None

    @property
    def buyers(self) -> list[str]:
        return sorted({r["buyer"] for r in self.rows if r.get("buyer")})

    @property
    def cpv_profile(self) -> list[str]:
        codes: set[str] = set()
        for r in self.rows:
            codes.update(r.get("cpv") or [])
        return sorted(codes)[:10]


def proof_for(company: Company, today: date) -> tuple[str, str | None, str | None]:
    """Staerkster verfuegbarer Beleg fuer Public-Sector-Aktivitaet."""
    last = company.last_award
    if not last:
        # Kein benannter Zuschlag, aber namentlich als Bieter gefuehrt. Das ist
        # kein schwacher Beleg - es ist derselbe amtliche Datensatz, nur die
        # andere Spalte. Welcher der drei Belegarten es ist, entscheidet der
        # Ausgang, den wir aus der Bekanntmachung ableiten konnten.
        for outcome, ptype in (("unterlegen", "P1B_bieter_unterlegen"),
                               ("alleinbieter_gewonnen", "P1C_alleinbieter"),
                               ("offen", "P1D_ausgang_offen")):
            rows = [b for b in company.bids if b.get("outcome") == outcome]
            if rows:
                newest = max(rows, key=lambda b: b.get("date") or "")
                return ptype, newest.get("url"), (newest.get("date") or "")[:10] or None
        return "P6_nur_branche", None, None
    try:
        age_days = (today - date.fromisoformat(last[:10])).days
    except ValueError:
        age_days = 9999
    url = next((a.get("url") for a in company.awards if a.get("url")), None)
    ptype = "P1_zuschlag_24m" if age_days <= 730 else (
        "P2_zuschlag_48m" if age_days <= 1460 else "P3_rahmenvertrag")
    return ptype, url, last[:10]


# === WARUM DAS TIERING OHNE MITARBEITERZAHL AUSKOMMT ===
# Die erste Fassung stufte nach Mitarbeitenden ein (Zielkorridor 50-2.000).
# Das klang vernuenftig und war in der Praxis unbrauchbar:
#
#   - Die Zahl fehlte bei 2.468 von 2.468 Zeilen, weil sie erst aus dem
#     Enrichment kommt. Jede Firma fiel in denselben Zweig -> 2.464x Tier B.
#   - Wo sie vorlag, war sie bei 5 von 10 Firmen die des KONZERNS statt die
#     des Rechtstraegers (Bechtle 17.000, Computacenter 21.000/UK).
#
# Ein Tier darf nicht an einem Fremddatum haengen, das meistens fehlt und
# oft das falsche Unternehmen beschreibt. Es haengt jetzt ausschliesslich
# an dem, was wir selbst belegt haben - und das ist mehr, als es klingt:
#
#   Haeufigkeit    Wie viele Verfahren in 12 Monaten?      (1 bis 131)
#   Aktualitaet    Wie alt ist der juengste Beleg?         (Median 177 Tage)
#   Breite         Wie viele verschiedene Auftraggeber?    (626 Firmen > 1)
#   Belegart       Zuschlag benannt, erschlossen, offen?
#
# Gemessen am 23.09.2026 ueber 2.468 Firmen: A 236, B 1.268, C 964.
# Gegenprobe: Von den fuenf Firmen, die unabhaengig per Apollo als
# ICP-passend bestaetigt wurden (63-900 MA), landen drei allein aus den
# Vergabedaten in Tier A. Die Groesse korreliert also, ohne dass wir sie
# brauchen.
#
# Die Mitarbeiterzahl bleibt als Spalte erhalten - sie ist fuer Ansprache
# und Segmentierung nuetzlich. Sie beeinflusst das Tier nur nicht mehr.

# Ab hier gilt eine Firma als regelmaessiger Bieter.
TIER_A_MIN_VERFAHREN = 3
# Juenger als das, und der Angebotsprozess laeuft nachweislich JETZT.
TIER_A_MAX_ALTER_TAGE = 180

# tier_status sagt nicht mehr "vorlaeufig/final" (das hing an der
# Mitarbeiterzahl), sondern worauf das Tier beruht. Damit ist ohne Blick in
# proof_type klar, wie belastbar die Einstufung ist.
TIER_STATUS = {
    "P1_zuschlag_24m": "zuschlag_benannt",
    "P2_zuschlag_48m": "zuschlag_benannt",
    "P1B_bieter_unterlegen": "zuschlag_benannt",
    "P1C_alleinbieter": "zuschlag_erschlossen",
    "P1D_ausgang_offen": "teilnahme_offen",
    "P3_rahmenvertrag": "schwacher_beleg",
    "P4_referenz_website": "schwacher_beleg",
    "P5_schwaches_signal": "schwacher_beleg",
    "P6_nur_branche": "kein_beleg",
}

STRONG_PROOFS = ("P1_zuschlag_24m", "P2_zuschlag_48m", "P1B_bieter_unterlegen",
                 "P1C_alleinbieter", "P1D_ausgang_offen")


def _alter_text(days: int | None) -> str:
    if days is None:
        return "ohne Datum"
    if days <= 1:
        return "juengster Beleg von heute"
    if days <= 31:
        return f"juengster Beleg vor {days} Tagen"
    months = days // 30
    return f"juengster Beleg vor {months} Monat{'' if months == 1 else 'en'}"


def tier_for(proof_type: str, participations: int = 0,
             proof_age_days: int | None = None, buyer_count: int = 0,
             mixed_lot_only: bool = False) -> tuple[str, str, str]:
    """Tier, Begruendung und Status - ausschliesslich aus Vergabedaten.

    Die Mitarbeiterzahl geht bewusst NICHT ein (siehe Kommentar oben).

    Rueckgabe: (tier, tier_rationale, tier_status)
    """
    status = TIER_STATUS.get(proof_type, "kein_beleg")

    if mixed_lot_only:
        return ("C", "nur ueber Sammelvergabe mit fachfremden Gewerken belegt - "
                     "IT-Eigenschaft nicht gesichert, vor Ansprache pruefen",
                status)
    if proof_type not in STRONG_PROOFS:
        if proof_type in ("P3_rahmenvertrag", "P4_referenz_website",
                          "P5_schwaches_signal"):
            return ("C", "Public-Sector-Bezug belegt, aber kein Zuschlag und "
                         "keine Bieterrolle gefunden", status)
        return ("D", "kein belegter Public-Sector-Bezug", status)

    alter = _alter_text(proof_age_days)
    breite = (f", {buyer_count} verschiedene Auftraggeber" if buyer_count > 1
              else "")
    frisch = proof_age_days is not None and proof_age_days <= TIER_A_MAX_ALTER_TAGE

    if participations >= TIER_A_MIN_VERFAHREN and frisch:
        return ("A", f"{participations} Verfahren in 12 Monaten, {alter}"
                     f"{breite} - laufender Angebotsprozess", status)
    if participations >= 2:
        return ("B", f"{participations} Verfahren in 12 Monaten, {alter}"
                     f"{breite} - wiederkehrender Bieter", status)
    if frisch:
        return ("B", f"1 Verfahren, {alter} - Teilnahme aktuell, aber bisher "
                     f"einmalig", status)
    return ("C", f"{participations or 1} Verfahren, {alter} - Teilnahme belegt, "
                 f"aber weder haeufig noch aktuell", status)


def assign_tier(company: Company, proof_type: str,
                proof_date: str | None = None,
                today: date | None = None) -> tuple[str, str, str]:
    """Duenner Adapter: Company -> tier_for()."""
    return tier_for(
        proof_type=proof_type,
        participations=company.participation_count,
        proof_age_days=_age_days(proof_date, today),
        buyer_count=len(company.buyers),
        mixed_lot_only=company.from_mixed_lot_only,
    )


def _age_days(iso: str | None, today: date | None = None) -> int | None:
    if not iso:
        return None
    try:
        return (( today or date.today()) - date.fromisoformat(iso[:10])).days
    except ValueError:
        return None


# --- Aufbau -------------------------------------------------------------------
def companies_from_awards(releases: Iterable[dict], cpv_ok) -> dict[str, Company]:
    """OCDS-Releases -> Firmenindex. Konsortien werden aufgesplittet,
    Ausschlusslisten greifen, Mehrfachzuschlaege werden aggregiert."""
    index: dict[str, Company] = {}

    for rel in releases:
        tender = rel.get("tender") or {}
        verdict = classify(tender)
        if not verdict["is_it"]:
            continue
        cpv = verdict["cpv_codes"]

        ocid = rel.get("ocid") or ""
        notice_id = rel.get("id") or ""
        buyer = (rel.get("buyer") or {}).get("name")
        title = tender.get("title")

        for award in rel.get("awards") or []:
            adate = (award.get("date") or rel.get("date") or "")[:10] or None
            for supplier in award.get("suppliers") or []:
                raw = clean_name(supplier.get("name"))
                if not raw:
                    continue
                addr = supplier.get("address") or {}
                members, is_consortium = split_consortium(raw)

                for member in members:
                    excluded, _reason = check_exclusion(member)
                    if excluded:
                        continue
                    key = normalize_company(member)
                    if not key:
                        continue
                    c = index.get(key)
                    if c is None:
                        c = Company(legal_name=member.strip(), normalized=key,
                                    city=addr.get("locality"),
                                    postal_code=addr.get("postalCode"))
                        index[key] = c
                    if supplier.get("id"):
                        c.supplier_ids.add(str(supplier["id"]))
                    if not is_consortium:
                        c.consortium_only = False
                    c.sources.add("dovs")
                    c.awards.append({
                        "ocid": ocid, "date": adate, "buyer": buyer, "title": title,
                        "cpv": cpv[:8], "main_cpv": verdict["main_cpv"],
                        "it_share": verdict["it_share"],
                        "mixed_lot": verdict["mixed_lot_warning"],
                        "value": (award.get("value") or {}).get("amount"),
                        "consortium": is_consortium,
                        "notice_id": notice_id,
                        "url": notice_url(notice_id),
                    })

        # --- Bieter ----------------------------------------------------------
        # Die Regel, wer Bieter ist und was ueber seinen Ausgang bekannt ist,
        # steht in src/resolve/parties.py - dieselbe Funktion nutzt der
        # Signalpfad in src/sources/dovs.py. Solange beide dieselbe Regel
        # lesen, koennen Longlist und Signalmotor nicht auseinanderlaufen.
        won_here = winner_keys(rel)
        bid_date = (rel.get("date") or "")[:10] or None

        for bidder in bidder_parties(rel):
            tenderer = bidder["party"]
            addr = tenderer.get("address") or {}
            members, is_consortium = split_consortium(bidder["name"])

            for member in members:
                key = normalize_company(member)
                if not key or key in won_here:
                    continue          # hat in diesem Verfahren gewonnen
                excluded, _reason = check_exclusion(member)
                if excluded:
                    continue
                c = index.get(key)
                if c is None:
                    c = Company(legal_name=member.strip(), normalized=key,
                                city=addr.get("locality"),
                                postal_code=addr.get("postalCode"))
                    index[key] = c
                if tenderer.get("id"):
                    c.supplier_ids.add(str(tenderer["id"]))
                if not is_consortium:
                    c.consortium_only = False
                c.sources.add("dovs")
                c.bids.append({
                    "ocid": ocid, "date": bid_date, "buyer": buyer, "title": title,
                    "cpv": cpv[:8], "main_cpv": verdict["main_cpv"],
                    "it_share": verdict["it_share"],
                    "mixed_lot": verdict["mixed_lot_warning"],
                    "consortium": is_consortium,
                    "notice_id": notice_id,
                    "url": notice_url(notice_id),
                    "outcome": bidder["outcome"],
                    "bidder_count": bidder["bidder_count"],
                })
    return index


# --- Vollstaendigkeit ---------------------------------------------------------
# Hier stand ein Chapman-Schaetzer (capture_recapture) fuer die Marktgroesse.
# Er war nie aufgerufen - und das README behauptete trotzdem, er schaetze die
# Abdeckung. Eine Funktion, die niemand ruft, ist kein Feature, sondern eine
# Zusage ohne Deckung; dieselbe Fehlerklasse wie der nie feuernde Signaltyp
# und das tote enrich_merge-Modul.
#
# Ehrlich ist: Fuer eine belastbare Schaetzung fehlt die zweite, UNABHAENGIGE
# Quelle. Vergabedaten und Branchenrankings ueberrepraesentieren beide grosse
# Unternehmen, die Unabhaengigkeitsannahme des Schaetzers waere verletzt und
# das Ergebnis systematisch zu niedrig.
#
# Deshalb ist die Vollstaendigkeitsmessung Teil des Zwei-Wochen-Plans
# (Eval-Harness mit gelabeltem Ground-Truth-Set), nicht eine Zahl, die hier
# ohne Grundlage entsteht. Siehe README.


# --- Export -------------------------------------------------------------------
COLUMNS = [
    "company_id", "legal_name", "domain", "domain_confidence", "domain_source",
    "city", "postal_code", "employees", "employees_scope",
    "tier", "tier_status", "tier_rationale",
    "proof_type", "proof_confidence", "proof_url", "proof_date",
    "awards_total", "award_rows", "last_award_date",
    "sole_bidder_wins", "bids_lost", "bids_outcome_unknown",
    "last_bid_date", "participations_total", "win_rate",
    "buyers", "buyers_total", "cpv_profile", "main_cpv", "mixed_lot_only",
    "consortium_only", "supplier_ids", "sources", "first_seen",
]


def export(index: dict[str, Company], path: Path | None = None,
           today: date | None = None) -> Path:
    today = today or date.today()
    path = path or (DATA / "longlist_markt.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for key, c in index.items():
        ptype, purl, pdate = proof_for(c, today)
        tier, rationale, tier_status = assign_tier(c, ptype, pdate, today)
        rows.append({
            "company_id": key,
            "legal_name": c.legal_name,
            "domain": c.domain or "",
            "domain_confidence": c.domain_confidence or "",
            "domain_source": c.domain_source or "",
            "city": c.city or "",
            "postal_code": c.postal_code or "",
            "employees": c.employees if c.employees is not None else "",
            "employees_scope": "",
            "tier": tier,
            "tier_status": tier_status,
            "tier_rationale": rationale,
            "proof_type": ptype,
            "proof_confidence": PROOF_CONFIDENCE.get(ptype, ""),
            "proof_url": purl or "",
            "proof_date": pdate or "",
            "awards_total": c.award_count,
            "award_rows": c.award_rows,
            "last_award_date": (c.last_award or "")[:10],
            "sole_bidder_wins": c.sole_bidder_wins,
            "bids_lost": c.lost_count,
            "bids_outcome_unknown": c.open_count,
            "last_bid_date": (c.last_bid or "")[:10],
            "participations_total": c.participation_count,
            # Die eigentliche Verkaufszahl: Wie oft hat der Betrieb Angebots-
            # aufwand betrieben, und wie oft hat sich das gelohnt? Eine
            # niedrige Quote bei vielen Teilnahmen ist der Gespraechsaufhaenger.
            # Verfahren mit unklarem Ausgang bleiben draussen - sonst rechnen
            # wir eine Niederlage herbei, die in den Daten nicht steht.
            "win_rate": (round(c.wins_total / (c.wins_total + c.lost_count), 2)
                         if (c.wins_total + c.lost_count) else ""),
            "buyers": ";".join(c.buyers[:5]),
            # buyers ist auf 5 gekappt, damit die CSV lesbar bleibt.
            # Die echte Zahl braucht das Tiering - also eigene Spalte.
            "buyers_total": len(c.buyers),
            "cpv_profile": ";".join(c.cpv_profile),
            "main_cpv": next((r.get("main_cpv") for r in c.rows if r.get("main_cpv")), ""),
            "mixed_lot_only": "ja" if c.from_mixed_lot_only else "nein",
            "consortium_only": "ja" if c.consortium_only else "nein",
            "supplier_ids": ";".join(sorted(c.supplier_ids)),
            "sources": ";".join(sorted(c.sources)),
            "first_seen": today.isoformat(),
        })

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    rows.sort(key=lambda r: (order.get(r["tier"], 9),
                             -int(r["participations_total"])))

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    return path


def summary(index: dict[str, Company], today: date | None = None) -> dict:
    today = today or date.today()
    tiers: dict[str, int] = defaultdict(int)
    for c in index.values():
        ptype, _, pdate = proof_for(c, today)
        tiers[assign_tier(c, ptype, pdate, today)[0]] += 1
    return {
        "firmen_gesamt": len(index),
        "tiers": dict(sorted(tiers.items())),
        "nur_als_konsortialmitglied": sum(1 for c in index.values() if c.consortium_only),
        "mit_mehrfachzuschlag": sum(1 for c in index.values() if c.award_count > 1),
        "mit_zuschlag_benannt": sum(1 for c in index.values() if c.awards),
        # Die Gruppen, die es vor der Bieterauswertung gar nicht gab.
        "alleinbieter_gewinner": sum(
            1 for c in index.values() if not c.awards and c.sole_bidder_wins),
        "unterlegene_bieter": sum(1 for c in index.values() if c.lost_count),
        "mehrfach_unterlegen": sum(1 for c in index.values() if c.lost_count > 1),
        "ausgang_offen": sum(
            1 for c in index.values()
            if not c.awards and not c.sole_bidder_wins and not c.lost_count),
        "ohne_domain": sum(1 for c in index.values() if not c.domain),
    }
