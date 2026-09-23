"""Signal 2b: EU-weite Vergabedaten (TED Search API).

Quelle:   POST https://api.ted.europa.eu/v3/notices/search
Doku:     https://docs.ted.europa.eu/api/latest/search.html
Auth:     KEINE. Die API ist oeffentlich und unauthentifiziert.
          Ein API-Key ist optional und hebt nur die Rate Limits an.
Lizenz:   offene EU-Daten
Kosten:   0 EUR

VERHAELTNIS ZU dovs.py:
Der Datenservice Oeffentlicher Einkauf ist die PRIMAERquelle fuer Deutschland,
weil er auch unterschwellige Verfahren enthaelt. TED deckt nur den
oberschwelligen EU-Bereich ab, dafuer aber grenzueberschreitend und mit
harmonisierten eForms-Feldern. Wir nutzen TED deshalb ergaenzend:
  - als Cross-Check fuer die Entity-Resolution (zweite unabhaengige Quelle,
    Grundlage fuer die Capture-Recapture-Schaetzung der Vollstaendigkeit)
  - fuer Vergaben deutscher Systemhaeuser ausserhalb Deutschlands

WARUM NICHT DER APIFY-ACTOR:
`foxlabs/ted-tenders` ($4/1.000 Ergebnisse) wrappt genau diese kostenlose API
und liefert beim Gewinner nur `winnerNames` + `winnerCountries` - die
GEWINNERADRESSE fehlt. Die brauchen wir aber fuer das Ortsmatching in der
Entity-Resolution. Die Rohdaten hier enthalten sie.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Any, Iterable

import requests

from src.config import CPV_IT_PREFIXES
from src.sources.base import FixtureMixin
from src.store import RawSignal

SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"
PAGE_SIZE = 250          # laut Doku das Maximum pro Seite

FIELDS = [
    "publication-number", "publication-date", "notice-type", "form-type",
    "notice-title", "buyer-name", "buyer-country",
    "classification-cpv", "winner-name", "winner-country",
    "organisation-name-serv-prov", "organisation-city-serv-prov",
    "organisation-country-serv-prov", "award-criterion-type",
    "total-value", "deadline-receipt-request",
]


def _first(value: Any) -> str | None:
    """TED-Felder sind haeufig Listen oder Sprach-Dicts. Wir wollen einen Wert.
    Defensiv, weil sich die Verschachtelung je Feld unterscheidet."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        for item in value:
            got = _first(item)
            if got:
                return got
        return None
    if isinstance(value, dict):
        for key in ("deu", "eng", "value", "text"):
            if key in value:
                got = _first(value[key])
                if got:
                    return got
        for v in value.values():
            got = _first(v)
            if got:
                return got
    return None


def _all_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [s for item in value for s in _all_strings(item)]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _all_strings(v)]
    return []


class TEDSource(FixtureMixin):
    name = "ted"
    signal_type = "zuschlag_gewonnen"

    def __init__(self, max_pages: int = 8):
        self.max_pages = max_pages

    def _query(self, since: date) -> str:
        """TED Expert-Query. CPV-Praefixe als OR-Kette, Land DE,
        nur Zuschlagsbekanntmachungen ab dem Stichtag."""
        cpv = " OR ".join(f"classification-cpv={p}*" for p in CPV_IT_PREFIXES)
        return (
            f"({cpv}) "
            f"AND buyer-country=DEU "
            f"AND publication-date>={since.strftime('%Y%m%d')} "
            f"AND notice-type=can-standard"
        )

    def _call(self, query: str, token: str | None) -> dict:
        body: dict[str, Any] = {
            "query": query,
            "fields": FIELDS,
            "limit": PAGE_SIZE,
            "paginationMode": "ITERATION",
            "scope": "ALL",
        }
        if token:
            body["iterationNextToken"] = token
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if os.getenv("TED_API_KEY"):
            headers["Authorization"] = f"Bearer {os.environ['TED_API_KEY']}"
        resp = requests.post(SEARCH_URL, json=body, headers=headers, timeout=90)
        resp.raise_for_status()
        return resp.json()

    def fetch(self, since: date, live: bool = True) -> Iterable[RawSignal]:
        if live:
            notices: list[dict] = []
            token: str | None = None
            query = self._query(since)
            for page in range(self.max_pages):
                try:
                    data = self._call(query, token)
                except requests.HTTPError as exc:
                    print(f"  ! {self.name}: Seite {page + 1} -> {exc}")
                    break
                batch = data.get("notices") or data.get("results") or []
                notices.extend(batch)
                token = data.get("iterationNextToken")
                print(f"  . {self.name}: Seite {page + 1}, {len(batch)} Notices")
                if not token or len(batch) < PAGE_SIZE:
                    break
            self.save_fixture(notices)
        else:
            notices = self.load_fixture()

        for n in notices:
            pub = _first(n.get("publication-number"))
            if not pub:
                continue
            pub_date = (_first(n.get("publication-date")) or "")[:10] or None
            title = _first(n.get("notice-title"))
            buyer = _first(n.get("buyer-name"))
            cpv = _all_strings(n.get("classification-cpv"))[:8]

            # Gewinner steht je nach eForms-Variante in unterschiedlichen
            # Feldern. Beide pruefen, sonst verliert man die Haelfte.
            winners = (_all_strings(n.get("winner-name"))
                       or _all_strings(n.get("organisation-name-serv-prov")))
            cities = _all_strings(n.get("organisation-city-serv-prov"))

            for idx, winner in enumerate(dict.fromkeys(winners)):
                yield RawSignal(
                    source=self.name,
                    external_id=f"{pub}:{idx}",
                    signal_type=self.signal_type,
                    event_date=pub_date,
                    org_name_raw=winner,
                    org_place=cities[idx] if idx < len(cities) else (cities[0] if cities else None),
                    source_url=f"https://ted.europa.eu/en/notice/-/detail/{pub}",
                    title=title,
                    payload={
                        "publication_number": pub,
                        "buyer": buyer,
                        "cpv": cpv,
                        "value": _first(n.get("total-value")),
                        "notice_type": _first(n.get("notice-type")),
                        "source_scope": "EU_oberschwellig",
                    },
                )
