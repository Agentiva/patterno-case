"""Signal 2: Vergabedaten (Datenservice Oeffentlicher Einkauf).

Quelle:   https://oeffentlichevergabe.de/api/notice-exports?pubMonth=YYYY-MM&format=ocds.zip
Doku:     https://oeffentlichevergabe.de/documentation/swagger-ui/opendata/index.html
Lizenz:   CC0 - keine Lizenzkosten, keine ToS-Risiken
Frequenz: taeglich abrufbar, Monatspakete
Kosten:   0 EUR

WARUM DIESE QUELLE UND NICHT TED:
TED enthaelt nur oberschwellige EU-Vergaben. Der Datenservice Oeffentlicher
Einkauf (Bekanntmachungsservice des Beschaffungsamts) enthaelt Bund, Laender
UND Kommunen inklusive UNTERSCHWELLIGER Verfahren - also genau den Teil des
Marktes, der auf TED gar nicht erscheint. Fuer ein Segment wie IT-Systemhaeuser,
das stark kommunal einkauft, ist das der Unterschied zwischen Spitze und Eisberg.
TED bleibt als Ergaenzung fuer EU-weite und grenzueberschreitende Verfahren.

DREI SIGNALTYPEN AUS EINER QUELLE:
  zuschlag_gewonnen            - Award in den letzten 4-8 Wochen
  offene_ausschreibung_im_profil - laufendes Verfahren, Frist in 2-4 Wochen
  rahmenvertrag_laeuft_aus     - Vertragsende in 6-9 Monaten -> Neuausschreibung

Der dritte ist der wertvollste: Er ist datiert, oeffentlich belegbar, und es
gibt ihn in keinem Standard-Sales-Tool. Er entsteht rein rechnerisch aus dem
Vertragsende in der Zuschlagsbekanntmachung.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import date, datetime, timedelta
from typing import Any, Iterable

import requests

from src.resolve.cpv import classify
from src.sources.base import FixtureMixin
from src.store import RawSignal

EXPORT_URL = "https://oeffentlichevergabe.de/api/notice-exports"

# Fenster fuer das Rahmenvertrags-Signal: 6-9 Monate vor Vertragsende
FRAMEWORK_LEAD_MIN_DAYS = 180
FRAMEWORK_LEAD_MAX_DAYS = 270

# Fenster fuer "offene Ausschreibung": Frist in 2-4 Wochen
DEADLINE_MIN_DAYS = 10
DEADLINE_MAX_DAYS = 32


def _matches_cpv(codes: list[str]) -> bool:
    return any(
        str(c).startswith(p) for c in codes for p in CPV_IT_PREFIXES
    )


def _iso(value: Any) -> str | None:
    """OCDS-Datumsfelder sind ISO-8601 mit Zeitzone. Wir wollen nur das Datum."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (ValueError, TypeError):
        return str(value)[:10] or None


class VergabeSource(FixtureMixin):
    """Datenservice Oeffentlicher Einkauf, OCDS-Export."""

    name = "vergabe_dovs"
    signal_type = "vergabe"

    def __init__(self, months: int = 3):
        self.months = months

    # -- Abruf ----------------------------------------------------------------
    def _download_month(self, ym: str) -> list[dict]:
        """Ein Monatspaket als ZIP holen und die OCDS-Releases extrahieren."""
        resp = requests.get(
            EXPORT_URL,
            params={"pubMonth": ym, "format": "ocds.zip"},
            timeout=180,
            stream=True,
        )
        resp.raise_for_status()
        releases: list[dict] = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                if not member.lower().endswith(".json"):
                    continue
                try:
                    doc = json.loads(zf.read(member).decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                # Das Paket kann ein Release-Package oder Einzelreleases sein.
                if isinstance(doc, dict) and "releases" in doc:
                    releases.extend(doc["releases"])
                elif isinstance(doc, dict):
                    releases.append(doc)
                elif isinstance(doc, list):
                    releases.extend(doc)
        return releases

    def fetch(self, since: date, live: bool = True) -> Iterable[RawSignal]:
        if live:
            releases: list[dict] = []
            cursor = date.today()
            for _ in range(self.months):
                ym = cursor.strftime("%Y-%m")
                try:
                    releases.extend(self._download_month(ym))
                    print(f"  . {self.name}: {ym} geladen")
                except requests.HTTPError as exc:
                    print(f"  ! {self.name}: {ym} -> {exc}")
                cursor = (cursor.replace(day=1) - timedelta(days=1))
            self.save_fixture(releases)
        else:
            releases = self.load_fixture()

        today = date.today()
        for rel in releases:
            yield from self._releases_to_signals(rel, since, today)

    # -- Fachlogik ------------------------------------------------------------
    def _releases_to_signals(
        self, rel: dict, since: date, today: date
    ) -> Iterable[RawSignal]:
        tender = rel.get("tender") or {}
        verdict = classify(tender)
        if not verdict["is_it"]:
            return
        cpv = verdict["cpv_codes"]

        ocid = rel.get("ocid") or rel.get("id") or ""
        url = f"https://oeffentlichevergabe.de/ui/de/notice/{ocid}"
        buyer = (rel.get("buyer") or {}).get("name")
        title = tender.get("title") or ""

        # --- Typ A + C: Zuschlag / Rahmenvertrags-Ablauf ---------------------
        for award in rel.get("awards") or []:
            award_date = _iso(award.get("date")) or _iso(rel.get("date"))
            period_end = _iso((award.get("contractPeriod") or {}).get("endDate"))

            for supplier in award.get("suppliers") or []:
                sup_name = (supplier.get("name") or "").strip()
                if not sup_name:
                    continue
                addr = supplier.get("address") or {}
                place = addr.get("locality") or addr.get("region")

                base_payload = {
                    "ocid": ocid, "cpv": cpv[:8], "mixed_lot": verdict["mixed_lot_warning"], "buyer": buyer,
                    "award_id": award.get("id"),
                    "value": (award.get("value") or {}).get("amount"),
                    "currency": (award.get("value") or {}).get("currency"),
                    "contract_end": period_end,
                    "supplier_id": supplier.get("id"),
                    "postal_code": addr.get("postalCode"),
                }

                # A) frischer Zuschlag
                if award_date and date.fromisoformat(award_date) >= since:
                    yield RawSignal(
                        source=self.name,
                        external_id=f"{ocid}:award:{award.get('id')}:{supplier.get('id')}",
                        signal_type="zuschlag_gewonnen",
                        event_date=award_date,
                        org_name_raw=sup_name,
                        org_place=place,
                        source_url=url,
                        title=title,
                        payload=base_payload,
                    )

                # C) Rahmenvertrag laeuft in 6-9 Monaten aus
                if period_end:
                    try:
                        days_left = (date.fromisoformat(period_end) - today).days
                    except ValueError:
                        days_left = -1
                    if FRAMEWORK_LEAD_MIN_DAYS <= days_left <= FRAMEWORK_LEAD_MAX_DAYS:
                        yield RawSignal(
                            source=self.name,
                            external_id=f"{ocid}:expiry:{award.get('id')}:{supplier.get('id')}",
                            signal_type="rahmenvertrag_laeuft_aus",
                            event_date=today.isoformat(),
                            org_name_raw=sup_name,
                            org_place=place,
                            source_url=url,
                            title=title,
                            payload={**base_payload, "days_to_expiry": days_left},
                        )

        # --- Typ B: offenes Verfahren mit naher Frist -------------------------
        # Hier ist der Adressat NICHT der Bieter, sondern ein Account aus
        # Longlist 1, dessen CPV-/Regionsprofil passt. Das Matching passiert
        # im Scoring, nicht hier - deshalb org_name_raw = Vergabestelle.
        deadline = _iso((tender.get("tenderPeriod") or {}).get("endDate"))
        if deadline and not rel.get("awards"):
            try:
                days_left = (date.fromisoformat(deadline) - today).days
            except ValueError:
                days_left = -1
            if DEADLINE_MIN_DAYS <= days_left <= DEADLINE_MAX_DAYS:
                yield RawSignal(
                    source=self.name,
                    external_id=f"{ocid}:open",
                    signal_type="offene_ausschreibung_im_profil",
                    event_date=_iso(rel.get("date")) or today.isoformat(),
                    org_name_raw=buyer or "unbekannte Vergabestelle",
                    org_place=((rel.get("buyer") or {}).get("address") or {}).get("locality"),
                    source_url=url,
                    title=title,
                    payload={
                        "ocid": ocid, "cpv": cpv[:8], "mixed_lot": verdict["mixed_lot_warning"],
                        "deadline": deadline, "days_to_deadline": days_left,
                        "is_buyer_side": True,
                        "value": (tender.get("value") or {}).get("amount"),
                    },
                )
