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

from src.resolve.normalize import (
    check_exclusion, normalize_company, resolution_confidence, split_consortium,
)

DATA = Path("data")


# --- Beweishierarchie ---------------------------------------------------------
# Jede Zeile der Longlist traegt proof_type + proof_url + proof_date.
# Damit ist die von Patterno angekuendigte Stichprobenpruefung trivial.
PROOF_CONFIDENCE = {
    "P1_zuschlag_24m": 0.95,     # Zuschlag in den letzten 24 Monaten
    "P2_zuschlag_48m": 0.85,     # Zuschlag 24-48 Monate zurueck
    "P3_rahmenvertrag": 0.80,    # laufender Rahmenvertrag / Praequalifikation
    "P4_referenz_website": 0.65, # namentliche Referenz oeffentlicher AG
    "P5_schwaches_signal": 0.45, # Public-Landingpage, Zertifikat, Stellenanzeige
    "P6_nur_branche": 0.20,      # nur Branchen-/Groessenpassung -> kein A/B
}


@dataclass
class Company:
    legal_name: str
    normalized: str
    city: str | None = None
    postal_code: str | None = None
    supplier_ids: set[str] = field(default_factory=set)
    awards: list[dict] = field(default_factory=list)
    consortium_only: bool = True     # bisher nur als ARGE-Mitglied gesehen
    sources: set[str] = field(default_factory=set)

    # wird extern angereichert (siehe docs/waterfalls.md)
    domain: str | None = None
    domain_confidence: float = 0.0
    domain_source: str | None = None
    employees: int | None = None

    @property
    def award_count(self) -> int:
        return len(self.awards)

    @property
    def last_award(self) -> str | None:
        dates = [a["date"] for a in self.awards if a.get("date")]
        return max(dates) if dates else None

    @property
    def buyers(self) -> list[str]:
        return sorted({a["buyer"] for a in self.awards if a.get("buyer")})

    @property
    def cpv_profile(self) -> list[str]:
        codes: set[str] = set()
        for a in self.awards:
            codes.update(a.get("cpv") or [])
        return sorted(codes)[:10]


def proof_for(company: Company, today: date) -> tuple[str, str | None, str | None]:
    """Staerkster verfuegbarer Beleg fuer Public-Sector-Aktivitaet."""
    last = company.last_award
    if not last:
        return "P6_nur_branche", None, None
    try:
        age_days = (today - date.fromisoformat(last[:10])).days
    except ValueError:
        age_days = 9999
    url = next((a.get("url") for a in company.awards if a.get("url")), None)
    ptype = "P1_zuschlag_24m" if age_days <= 730 else (
        "P2_zuschlag_48m" if age_days <= 1460 else "P3_rahmenvertrag")
    return ptype, url, last[:10]


def assign_tier(company: Company, proof_type: str) -> tuple[str, str]:
    """Tiering mit ausgeschriebener Begruendung - die Begruendung landet als
    eigene Spalte im Export, damit eine Pruefung nicht raten muss."""
    strong = proof_type in ("P1_zuschlag_24m", "P2_zuschlag_48m")
    emp = company.employees

    if strong and emp is not None and 50 <= emp <= 2000:
        return "A", f"Zuschlagsbeleg ({proof_type}) und {emp} MA im Zielkorridor 50-2.000"
    if strong and emp is not None and emp < 50:
        return "B", f"Zuschlagsbeleg, aber nur {emp} MA - kleineres Paket, kuerzerer Zyklus"
    if strong and emp is not None and emp > 2000:
        return "B", f"Zuschlagsbeleg, aber {emp} MA - eigene Bid-Abteilung wahrscheinlich, laengerer Zyklus"
    if strong:
        return "B", f"Zuschlagsbeleg ({proof_type}), Mitarbeiterzahl nicht ermittelt"
    if proof_type in ("P3_rahmenvertrag", "P4_referenz_website", "P5_schwaches_signal"):
        return "C", "Public-Sector-Bezug belegt, aber kein Zuschlag gefunden - moeglicher Dauerbieter ohne Zuschlag, hoher Bedarf"
    return "D", "nur Branchen-/Groessenpassung, kein belegter Public-Sector-Bezug"


# --- Aufbau -------------------------------------------------------------------
def companies_from_awards(releases: Iterable[dict], cpv_ok) -> dict[str, Company]:
    """OCDS-Releases -> Firmenindex. Konsortien werden aufgesplittet,
    Ausschlusslisten greifen, Mehrfachzuschlaege werden aggregiert."""
    index: dict[str, Company] = {}

    for rel in releases:
        tender = rel.get("tender") or {}
        cpv: list[str] = []
        main = (tender.get("classification") or {}).get("id")
        if main:
            cpv.append(str(main))
        for item in tender.get("items") or []:
            cid = (item.get("classification") or {}).get("id")
            if cid:
                cpv.append(str(cid))
        if not cpv_ok(cpv):
            continue

        ocid = rel.get("ocid") or rel.get("id") or ""
        buyer = (rel.get("buyer") or {}).get("name")
        title = tender.get("title")

        for award in rel.get("awards") or []:
            adate = (award.get("date") or rel.get("date") or "")[:10] or None
            for supplier in award.get("suppliers") or []:
                raw = (supplier.get("name") or "").strip()
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
                        "cpv": sorted(set(cpv))[:8],
                        "value": (award.get("value") or {}).get("amount"),
                        "consortium": is_consortium,
                        "url": f"https://oeffentlichevergabe.de/ui/de/notice/{ocid}",
                    })
    return index


# --- Vollstaendigkeit ---------------------------------------------------------
def capture_recapture(n1: int, n2: int, overlap: int) -> dict:
    """Chapman-Schaetzer fuer die Marktgroesse.

        N = ((n1+1)(n2+1) / (m+1)) - 1

    n1 = Firmen aus Quelle 1 (Vergabedaten)
    n2 = Firmen aus Quelle 2 (Verzeichnis/Ranking)
    m  = Ueberschneidung

    WICHTIGER VORBEHALT - gehoert so ins README:
    Der Schaetzer setzt voraus, dass beide Quellen UNABHAENGIG sind. Das sind
    sie hier nicht: Vergabedaten und Branchenrankings ueberrepraesentieren
    beide grosse Unternehmen. Die Ueberschneidung ist dadurch kuenstlich hoch
    und N systematisch ZU NIEDRIG geschaetzt. Die reale Marktgroesse liegt
    eher am oberen Rand des Intervalls, der Longtail kleiner Systemhaeuser
    ist unterrepraesentiert.
    """
    if overlap <= 0:
        return {"estimate": None, "note": "keine Ueberschneidung - nicht schaetzbar"}

    n_hat = ((n1 + 1) * (n2 + 1) / (overlap + 1)) - 1
    var = ((n1 + 1) * (n2 + 1) * (n1 - overlap) * (n2 - overlap)
           / ((overlap + 1) ** 2 * (overlap + 2)))
    se = math.sqrt(var) if var > 0 else 0.0
    return {
        "estimate": round(n_hat),
        "ci95_low": round(max(n_hat - 1.96 * se, max(n1, n2))),
        "ci95_high": round(n_hat + 1.96 * se),
        "n1_vergabedaten": n1, "n2_verzeichnis": n2, "overlap": overlap,
        "coverage_quelle1": round(n1 / n_hat, 3) if n_hat else None,
        "vorbehalt": ("Unabhaengigkeitsannahme verletzt: beide Quellen "
                      "ueberrepraesentieren grosse Unternehmen. N ist damit "
                      "eher eine Untergrenze."),
    }


# --- Export -------------------------------------------------------------------
COLUMNS = [
    "company_id", "legal_name", "domain", "domain_confidence", "domain_source",
    "city", "postal_code", "employees", "tier", "tier_rationale",
    "proof_type", "proof_confidence", "proof_url", "proof_date",
    "awards_total", "last_award_date", "buyers", "cpv_profile",
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
        tier, rationale = assign_tier(c, ptype)
        rows.append({
            "company_id": key,
            "legal_name": c.legal_name,
            "domain": c.domain or "",
            "domain_confidence": c.domain_confidence or "",
            "domain_source": c.domain_source or "",
            "city": c.city or "",
            "postal_code": c.postal_code or "",
            "employees": c.employees if c.employees is not None else "",
            "tier": tier,
            "tier_rationale": rationale,
            "proof_type": ptype,
            "proof_confidence": PROOF_CONFIDENCE.get(ptype, ""),
            "proof_url": purl or "",
            "proof_date": pdate or "",
            "awards_total": c.award_count,
            "last_award_date": (c.last_award or "")[:10],
            "buyers": ";".join(c.buyers[:5]),
            "cpv_profile": ";".join(c.cpv_profile),
            "consortium_only": "ja" if c.consortium_only else "nein",
            "supplier_ids": ";".join(sorted(c.supplier_ids)),
            "sources": ";".join(sorted(c.sources)),
            "first_seen": today.isoformat(),
        })

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    rows.sort(key=lambda r: (order.get(r["tier"], 9), -int(r["awards_total"])))

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    return path


def summary(index: dict[str, Company], today: date | None = None) -> dict:
    today = today or date.today()
    tiers: dict[str, int] = defaultdict(int)
    for c in index.values():
        ptype, _, _ = proof_for(c, today)
        tiers[assign_tier(c, ptype)[0]] += 1
    return {
        "firmen_gesamt": len(index),
        "tiers": dict(sorted(tiers.items())),
        "nur_als_konsortialmitglied": sum(1 for c in index.values() if c.consortium_only),
        "mit_mehrfachzuschlag": sum(1 for c in index.values() if c.award_count > 1),
        "ohne_domain": sum(1 for c in index.values() if not c.domain),
    }
