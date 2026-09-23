"""Signal 1: Bid-/Vergabe-Rollen ausgeschrieben (Bundesagentur fuer Arbeit).

Quelle:   https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs
Auth:     Header  X-API-Key: jobboerse-jobsuche
Frequenz: taeglich
Kosten:   0 EUR

=== SCHEMA-DRIFT, AM 23.09.2026 LIVE FESTGESTELLT ===
Die Community-Spec (github.com/bundesAPI/jobsuche-api, openapi.yaml v2.1.0)
dokumentiert fuer /pc/v6/jobs eine Antwort mit `stellenangebote[]` und den
Feldern `refnr`, `titel`, `arbeitgeber`, `arbeitsort`,
`aktuelleVeroeffentlichungsdatum`.

Die API liefert tatsaechlich:
    ergebnisliste[]
      .referenznummer                    statt refnr
      .stellenangebotsTitel              statt titel
      .firma                             statt arbeitgeber
      .hauptberuf                        (standardisierte Berufsbezeichnung!)
      .stellenlokationen[].adresse.{ort,plz,region,strasse}   statt arbeitsort
      .datumErsteVeroeffentlichung       statt aktuelleVeroeffentlichungsdatum
      .veroeffentlichungszeitraum.von

Ein Adapter, der nur der Spec folgt, liefert still NULL Treffer - die
Antwort ist ja HTTP 200. Genau deshalb lesen wir hier beide Varianten und
loggen, wenn eine Antwort in keine passt.

Das ist zugleich das Kernargument gegen diese Quelle im Produktivbetrieb:
Die Bundesagentur bietet KEINE offiziell freigegebene API. Kein SLA, keine
Versionierung, Feldnamen aendern sich ohne Ankuendigung. Fuer ein verkauftes
Produkt gehoert das vorab juristisch und betrieblich bewertet.

=== GLUECKSFUND ===
`hauptberuf` ist eine standardisierte Berufsbezeichnung aus der
BA-Klassifikation, z. B. "Tender-Manager/in". Das ist ein deutlich
praeziserer Filter als Freitext im Titel und faengt Faelle, in denen der
Stellentitel kreativ ist. Wir werten beides aus.

=== EINSCHRAENKUNG, DIE DIE ARCHITEKTUR BESTIMMT ===
Die Antwort enthaelt Firmennamen und Adresse, aber KEINE Domain und KEINE
Registernummer. Die Zuordnung Firma -> Domain passiert deshalb komplett
nachgelagert in resolve/.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Any, Iterable

import requests

from src.config import JOB_TITLE_EXCLUDE, JOB_TITLE_INCLUDE
from src.resolve.normalize import fold
from src.sources.base import FixtureMixin
from src.store import RawSignal

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
API_KEY = os.getenv("BA_API_KEY", "jobboerse-jobsuche")

QUERIES = [
    "Bid Manager", "Angebotsmanager", "Ausschreibungsmanager",
    "Tender Manager", "Vergabemanagement", "Submission",
    "Vertrieb oeffentliche Auftraggeber", "Public Sector Sales",
]


def _pick(item: dict[str, Any], *keys: str) -> Any:
    """Erstes vorhandenes Feld. Faengt die Drift zwischen Spec und Realitaet."""
    for k in keys:
        if item.get(k) not in (None, "", []):
            return item[k]
    return None


def _location(item: dict[str, Any]) -> dict[str, Any]:
    """v6: stellenlokationen[].adresse   |   alt: arbeitsort"""
    locs = item.get("stellenlokationen")
    if isinstance(locs, list) and locs:
        return (locs[0] or {}).get("adresse") or {}
    return item.get("arbeitsort") or {}


class BAJobsSource(FixtureMixin):
    name = "ba_jobs"
    signal_type = "bid_rolle_ausgeschrieben"

    def __init__(self, page_size: int = 50, max_pages: int = 4):
        self.page_size = page_size
        self.max_pages = max_pages

    @staticmethod
    def is_relevant(title: str, beruf: str | None = None) -> tuple[bool, str]:
        """Der haeufigste False Positive ist die EINKAUFSseite: 'Vergabemanager'
        sitzt genauso in der Kommune wie beim Bieter. Erst Blacklist, dann
        Whitelist - und zwar ueber Titel UND standardisierten Beruf."""
        haystack = f"{fold(title or '')} {fold(beruf or '')}"
        for bad in JOB_TITLE_EXCLUDE:
            if fold(bad) in haystack:
                return False, f"exclude:{bad}"
        for good in JOB_TITLE_INCLUDE:
            if fold(good) in haystack:
                return True, f"include:{good}"
        return False, "no_match"

    def _call(self, was: str, page: int, since_days: int) -> dict:
        resp = requests.get(
            BASE_URL,
            headers={"X-API-Key": API_KEY, "Accept": "application/json"},
            params={
                "was": was, "wo": "Deutschland", "umkreis": 200,
                "size": self.page_size, "page": page,
                "veroeffentlichtseit": min(max(since_days, 1), 100),
                "angebotsart": 1,        # ARBEIT, kein Praktikum/Ausbildung
                "zeitarbeit": "false",   # ANUE ist kein Systemhaus-Signal
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch(self, since: date, live: bool = True) -> Iterable[RawSignal]:
        since_days = max((date.today() - since).days, 1)
        raw_rows: list[dict] = []

        if live:
            seen: set[str] = set()
            for was in QUERIES:
                for page in range(1, self.max_pages + 1):
                    try:
                        data = self._call(was, page, since_days)
                    except requests.HTTPError as exc:
                        print(f"  ! {self.name}: {was} S.{page} -> {exc}")
                        break

                    items = _pick(data, "ergebnisliste", "stellenangebote") or []
                    if not items:
                        if page == 1 and data.get("maxErgebnisse"):
                            # HTTP 200, Treffer laut Zaehler, aber Liste leer
                            # unter beiden bekannten Feldnamen -> Drift.
                            print(f"  ! {self.name}: unbekanntes Antwortschema, "
                                  f"keys={sorted(data.keys())}")
                        break

                    for it in items:
                        ref = _pick(it, "referenznummer", "refnr")
                        if ref and ref not in seen:
                            seen.add(str(ref))
                            raw_rows.append(it)
                    if len(items) < self.page_size:
                        break
            self.save_fixture(raw_rows)
        else:
            raw_rows = self.load_fixture()

        for it in raw_rows:
            title = _pick(it, "stellenangebotsTitel", "titel") or ""
            beruf = _pick(it, "hauptberuf", "beruf")
            ok, why = self.is_relevant(title, beruf)
            if not ok:
                continue

            employer = str(_pick(it, "firma", "arbeitgeber") or "").strip()
            if not employer:
                continue

            ref = str(_pick(it, "referenznummer", "refnr") or "")
            adr = _location(it)
            pub = (_pick(it, "datumErsteVeroeffentlichung",
                         "aktuelleVeroeffentlichungsdatum")
                   or (it.get("veroeffentlichungszeitraum") or {}).get("von"))

            yield RawSignal(
                source=self.name,
                external_id=ref,
                signal_type=self.signal_type,
                event_date=str(pub)[:10] if pub else None,
                org_name_raw=employer,
                org_place=adr.get("ort"),
                source_url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
                title=title,
                payload={
                    "plz": adr.get("plz"),
                    "region": adr.get("region"),
                    "hauptberuf": beruf,
                    "vertragsdauer": it.get("vertragsdauer"),
                    "homeoffice": it.get("homeofficemoeglich"),
                    "title_match": why,
                },
            )
