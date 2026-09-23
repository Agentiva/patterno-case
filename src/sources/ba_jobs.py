"""Signal 1: Bid-/Vergabe-Rollen ausgeschrieben (Bundesagentur fuer Arbeit).

Quelle:   https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs
Auth:     Header  X-API-Key: jobboerse-jobsuche
Frequenz: taeglich
Kosten:   0 EUR
Spec:     https://github.com/bundesAPI/jobsuche-api  (openapi.yaml, v2.1.0)

WICHTIGE EINSCHRAENKUNG - im README ehrlich benennen:
Die Bundesagentur bietet KEINE offiziell dokumentierte oeffentliche API an.
Die hier genutzte Schnittstelle ist von der bundesAPI-Community dokumentiert
(reverse engineered). Fuer den Produktivbetrieb heisst das:
  - kein SLA, Endpunkt kann sich ohne Ankuendigung aendern
  - Nutzungsbedingungen vorab pruefen
  - defensiv implementieren (Schema-Drift abfangen, nie hart auf Felder bauen)
Alternative mit klarer Rechtslage waere ein kommerzieller Job-Datenanbieter.

ZWEITE EINSCHRAENKUNG, die die Architektur bestimmt:
Die Antwort enthaelt NUR den Arbeitgebernamen als Freitext (`arbeitgeber`)
und den Ort - KEINE Domain, KEINE Registernummer. Die gesamte Zuordnung
Firma -> Domain muss also nachgelagert passieren. Das ist der Grund, warum
resolve/ ein eigenes Modul ist und nicht drei Zeilen im Adapter.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Iterable

import requests

from src.config import JOB_TITLE_EXCLUDE, JOB_TITLE_INCLUDE
from src.resolve.normalize import fold
from src.sources.base import FixtureMixin
from src.store import RawSignal

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
API_KEY = os.getenv("BA_API_KEY", "jobboerse-jobsuche")

# Suchbegriffe. Die API sucht Freitext im Jobtitel; wir fahren mehrere
# Queries und deduplizieren spaeter ueber die refnr.
QUERIES = [
    "Bid Manager", "Angebotsmanager", "Ausschreibungsmanager",
    "Tender Manager", "Vergabemanagement", "Submission",
    "Vertrieb oeffentliche Auftraggeber", "Public Sector Sales",
]


class BAJobsSource(FixtureMixin):
    name = "ba_jobs"
    signal_type = "bid_rolle_ausgeschrieben"

    def __init__(self, page_size: int = 50, max_pages: int = 4):
        self.page_size = page_size
        self.max_pages = max_pages

    # -- Filter ---------------------------------------------------------------
    @staticmethod
    def is_relevant_title(title: str) -> tuple[bool, str]:
        """Der haeufigste False Positive dieses Signals ist die EINKAUFSseite:
        'Vergabemanager' sitzt genauso in der Kommune wie beim Bieter.
        Deshalb erst Blacklist, dann Whitelist."""
        t = fold(title or "")
        for bad in JOB_TITLE_EXCLUDE:
            if fold(bad) in t:
                return False, f"exclude:{bad}"
        for good in JOB_TITLE_INCLUDE:
            if fold(good) in t:
                return True, f"include:{good}"
        return False, "no_match"

    # -- Abruf ----------------------------------------------------------------
    def _call(self, was: str, page: int, since_days: int) -> dict:
        resp = requests.get(
            BASE_URL,
            headers={"X-API-Key": API_KEY, "Accept": "application/json"},
            params={
                "was": was,
                "wo": "Deutschland",
                "umkreis": 200,
                "size": self.page_size,
                "page": page,
                # 0-100 erlaubt; deckt unser 4-8-Wochen-Fenster ab
                "veroeffentlichtseit": min(max(since_days, 1), 100),
                "angebotsart": 1,        # 1 = ARBEIT (kein Praktikum/Ausbildung)
                "zeitarbeit": "false",   # ANUE ist fuer uns kein Systemhaus-Signal
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch(self, since: date, live: bool = True) -> Iterable[RawSignal]:
        since_days = max((date.today() - since).days, 1)
        raw_rows: list[dict] = []

        if live:
            seen_refs: set[str] = set()
            for was in QUERIES:
                for page in range(1, self.max_pages + 1):
                    try:
                        data = self._call(was, page, since_days)
                    except requests.HTTPError as exc:
                        print(f"  ! {self.name}: {was} S.{page} -> {exc}")
                        break
                    items = data.get("stellenangebote") or []
                    if not items:
                        break
                    for it in items:
                        ref = it.get("refnr") or it.get("referenznummer")
                        if ref and ref not in seen_refs:
                            seen_refs.add(ref)
                            raw_rows.append(it)
                    if len(items) < self.page_size:
                        break
            self.save_fixture(raw_rows)
        else:
            raw_rows = self.load_fixture()

        for it in raw_rows:
            title = it.get("titel") or it.get("beruf") or ""
            ok, why = self.is_relevant_title(title)
            if not ok:
                continue

            employer = (it.get("arbeitgeber") or "").strip()
            if not employer:
                continue

            ort = (it.get("arbeitsort") or {})
            ref = it.get("refnr") or it.get("referenznummer") or ""

            yield RawSignal(
                source=self.name,
                external_id=str(ref),
                signal_type=self.signal_type,
                event_date=it.get("aktuelleVeroeffentlichungsdatum"),
                org_name_raw=employer,
                org_place=ort.get("ort"),
                source_url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
                title=title,
                payload={
                    "plz": ort.get("plz"),
                    "region": ort.get("region"),
                    "eintrittsdatum": it.get("eintrittsdatum"),
                    "title_match": why,
                },
            )
