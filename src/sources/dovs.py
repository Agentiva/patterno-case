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
from src.sources.eforms import fristen
from src.resolve.normalize import normalize_company
from src.resolve.parties import bidder_parties, winner_keys
from src.sources.base import FixtureMixin
from src.store import RawSignal

EXPORT_URL = "https://oeffentlichevergabe.de/api/notice-exports"
NOTICE_URL = "https://oeffentlichevergabe.de/api/notices/{id}"


def notice_url(notice_id: str, fmt: str = "pdf") -> str:
    """Belegbare, im Browser lesbare URL einer Bekanntmachung.

    Verifiziert am 23.09.2026:
      /api/notices/<release id>              -> 200, application/xml
      /api/notices/<release id>?format=pdf   -> 200, application/pdf
      /api/notices/<ocid>                    -> 404
      /ui/de/notice/<beliebig>               -> 200, aber nur die SPA-Huelle
    """
    if not notice_id:
        return ""
    base = NOTICE_URL.format(id=notice_id)
    return f"{base}?format={fmt}" if fmt else base

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
        # Wird in fetch() gefuellt, bevor Signale entstehen.
        self._fristen: dict = {}

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

        # Angebotsfristen nachladen, bevor die Signale entstehen.
        #
        # ACHTUNG, hier lag ein teurer Fehler: Die erste Fassung filterte
        # nur nach "offen und jung genug" - aber ueber ALLE Releases, nicht
        # nur die IT-relevanten. Die CPV-Pruefung passiert erst weiter
        # unten in _releases_to_signals.
        # Gemessen: 1.695 IT-Kandidaten gegenueber rund 28.250 ohne
        # CPV-Filter, also Faktor 17. Der erste Live-Lauf lief dadurch in
        # den 30-Minuten-Timeout, ohne eine einzige Frist zu speichern.
        #
        # Die Reihenfolge ist also nicht egal: erst fachlich eingrenzen,
        # dann Netzwerk kosten verursachen.
        aelteste = today - timedelta(days=DEADLINE_MAX_DAYS + 30)
        kandidaten = [
            rel.get("id") for rel in releases
            if rel.get("id") and not rel.get("awards")
            and "tender" in (rel.get("tag") or [])
            and not ((rel.get("tender") or {}).get("tenderPeriod") or {}).get("endDate")
            and (rel.get("date") or "")[:10] >= aelteste.isoformat()
            and classify(rel.get("tender") or {})["is_it"]
        ]
        self._fristen = fristen(kandidaten, live=live) if kandidaten else {}

        # === EINE ZEILE JE VERFAHREN, NICHT JE BEKANNTMACHUNG ===
        # Ein Vergabeverfahren (ocid) kann mehrere Bekanntmachungen haben -
        # typisch eine Korrektur einen Tag nach dem Original. Beide tragen
        # dieselbe external_id, aber verschiedene notice_id, also
        # verschiedene content_hashes.
        #
        # Ungefiltert ueberschreiben sie sich im selben Lauf gegenseitig,
        # und der Store meldet sie JEDE WOCHE als "geaendert", obwohl sich
        # nichts geaendert hat. Gemessen: 17 Schluessel, die bei vier
        # Laeufen hintereinander konstant 25 Aenderungen erzeugten.
        #
        # Das ist keine Kleinigkeit: Der Delta-Ausgabe soll man glauben
        # koennen. Dauerhaftes Rauschen zerstoert genau das.
        #
        # Gewollt ist die juengste Bekanntmachung je Verfahren. Der
        # Gleichstand wird ueber die notice_id aufgeloest, damit das
        # Ergebnis nicht von der Lesereihenfolge abhaengt.
        neueste: dict[str, RawSignal] = {}
        for rel in releases:
            for sig in self._releases_to_signals(rel, since, today):
                alt = neueste.get(sig.external_id)
                if alt is None or self._rang(sig) > self._rang(alt):
                    neueste[sig.external_id] = sig
        yield from neueste.values()

    @staticmethod
    def _rang(sig: RawSignal) -> tuple[str, str]:
        return (sig.event_date or "", str((sig.payload or {}).get("notice_id") or ""))

    # -- Fachlogik ------------------------------------------------------------
    def _releases_to_signals(
        self, rel: dict, since: date, today: date
    ) -> Iterable[RawSignal]:
        tender = rel.get("tender") or {}
        verdict = classify(tender)
        if not verdict["is_it"]:
            return
        cpv = verdict["cpv_codes"]

        ocid = rel.get("ocid") or ""
        # ACHTUNG: ocid und id sind NICHT dasselbe.
        #   ocid = das Verfahren  (ocds-mnwr74-<uuid>)  -> in der API 404
        #   id   = die einzelne Bekanntmachung (<uuid>) -> die wollen wir
        # Die erste Version nutzte die ocid und baute daraus eine /ui/-URL.
        # Ergebnis: Die Seite laedt (HTTP 200, SPA-Huelle) und zeigt im
        # Browser "Wir koennen diese Seite nicht finden". Ein HTTP-Check haette
        # das NICHT gefunden - deshalb verlinken wir jetzt die API, deren
        # Status ehrlich ist.
        notice_id = rel.get("id") or ""
        url = notice_url(notice_id)
        buyer = (rel.get("buyer") or {}).get("name")
        title = tender.get("title") or ""

        # Vertragslaufzeiten haengen am LOS, nicht am Zuschlag.
        # Gemessen am 23.09.2026 in 20.000 Releases:
        #   awards[].contractPeriod        ->      0 Treffer
        #   tender.lots[].contractPeriod   -> 15.716 Treffer
        # Die erste Version las das Award-Feld. Folge: Der Signaltyp
        # rahmenvertrag_laeuft_aus - laut eigener Modulbeschreibung "der
        # wertvollste" - hat in keinem einzigen Lauf gefeuert, ohne Fehler.
        # Ein leeres Feld sieht eben genauso aus wie "kein Vertragsende".
        lot_period = {
            lot.get("id"): (lot.get("contractPeriod") or {})
            for lot in (tender.get("lots") or []) if lot.get("id")
        }

        # --- Typ A + C: Zuschlag / Rahmenvertrags-Ablauf ---------------------
        for award in rel.get("awards") or []:
            award_date = _iso(award.get("date")) or _iso(rel.get("date"))
            period_end = _iso((award.get("contractPeriod") or {}).get("endDate"))
            if not period_end:
                for lot_id in award.get("relatedLots") or []:
                    period_end = _iso(lot_period.get(lot_id, {}).get("endDate"))
                    if period_end:
                        break

            for supplier in award.get("suppliers") or []:
                sup_name = (supplier.get("name") or "").strip()
                if not sup_name:
                    continue
                addr = supplier.get("address") or {}
                place = addr.get("locality") or addr.get("region")

                base_payload = {
                    "ocid": ocid, "notice_id": notice_id, "xml_url": notice_url(notice_id, ""),
                    "cpv": cpv[:8], "mixed_lot": verdict["mixed_lot_warning"], "buyer": buyer,
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

        # --- Typ A/C fuer namentlich benannte BIETER --------------------------
        # Ohne diesen Block sieht der Signalmotor nur die benannten Gewinner,
        # waehrend die Longlist aus derselben Quelle die ganze Bieterseite
        # kennt: 751 Zuschlagszeilen gegen 5.735 Bieterzeilen in 12 Monaten.
        # Die Einstufung des Ausgangs kommt aus src/resolve/parties.py, damit
        # hier und in der Longlist garantiert dieselbe Regel gilt.
        won = winner_keys(rel)
        rel_date = _iso(rel.get("date")) or today.isoformat()
        # Bieter haengen an keinem einzelnen Los. Als Bezug fuer den
        # Vertragsablauf nehmen wir das FRUEHESTE Vertragsende des Verfahrens:
        # Wer nachfassen will, muss sich am ersten auslaufenden Los orientieren.
        ends = sorted(e for e in (
            (lot.get("contractPeriod") or {}).get("endDate")
            for lot in (tender.get("lots") or [])) if e)
        earliest_end = _iso(ends[0]) if ends else None

        for bidder in bidder_parties(rel):
            name = bidder["name"]
            if normalize_company(name) in won:
                continue                       # kommt schon aus dem Award-Block
            addr = (bidder["party"].get("address") or {})
            place = addr.get("locality") or addr.get("region")
            outcome = bidder["outcome"]

            payload = {
                "ocid": ocid, "notice_id": notice_id,
                "xml_url": notice_url(notice_id, ""),
                "cpv": cpv[:8], "mixed_lot": verdict["mixed_lot_warning"],
                "buyer": buyer, "outcome": outcome,
                "bidder_count": bidder["bidder_count"],
                "contract_end": earliest_end,
                "postal_code": addr.get("postalCode"),
                "supplier_id": bidder["party"].get("id"),
            }

            # Ein einziger Bieter in einer Zuschlagsbekanntmachung hat
            # gewonnen - erschlossen, nicht benannt. Das steht im Payload,
            # damit der erste Satz der Ansprache es beruecksichtigen kann.
            if outcome == "alleinbieter_gewonnen":
                sig_type = "zuschlag_gewonnen"
            elif outcome == "unterlegen":
                sig_type = "angebot_ohne_zuschlag"
            else:
                sig_type = "teilnahme_belegt"

            if rel_date >= since.isoformat():
                yield RawSignal(
                    source=self.name,
                    external_id=f"{ocid}:bidder:{normalize_company(name)[:40]}",
                    signal_type=sig_type,
                    event_date=rel_date,
                    org_name_raw=name,
                    org_place=place,
                    source_url=url,
                    title=title,
                    payload=payload,
                )

            # Ein auslaufender Rahmenvertrag ist nur fuer den Auftragnehmer
            # ein Anlass. Ein unterlegener Bieter hat keinen Vertrag, der
            # ablaeuft - fuer ihn waere es die naechste Ausschreibung, und
            # die steht hier nicht.
            if earliest_end and outcome == "alleinbieter_gewonnen":
                try:
                    days_left = (date.fromisoformat(earliest_end) - today).days
                except ValueError:
                    days_left = -1
                if FRAMEWORK_LEAD_MIN_DAYS <= days_left <= FRAMEWORK_LEAD_MAX_DAYS:
                    yield RawSignal(
                        source=self.name,
                        external_id=f"{ocid}:expiry:bidder:{normalize_company(name)[:40]}",
                        signal_type="rahmenvertrag_laeuft_aus",
                        event_date=today.isoformat(),
                        org_name_raw=name,
                        org_place=place,
                        source_url=url,
                        title=title,
                        payload={**payload, "days_to_expiry": days_left},
                    )

        # --- Typ B: offenes Verfahren mit naher Frist -------------------------
        # Hier ist der Adressat NICHT der Bieter, sondern ein Account aus
        # Longlist 1, dessen CPV-/Regionsprofil passt. Das Matching passiert
        # im Scoring, nicht hier - deshalb org_name_raw = Vergabestelle.
        # Die Frist steht NICHT im OCDS-JSON, sondern nur im eForms-XML
        # (BT-131, cac:TenderSubmissionDeadlinePeriod). Deshalb hat dieser
        # Signaltyp wochenlang geschwiegen. self._fristen ist der Cache,
        # den fetch() vorher gefuellt hat - siehe src/sources/eforms.py.
        deadline = _iso((tender.get("tenderPeriod") or {}).get("endDate"))
        if not deadline:
            aus_xml = (self._fristen or {}).get(notice_id) or {}
            deadline = aus_xml.get("deadline")
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
                        "ocid": ocid, "notice_id": notice_id, "xml_url": notice_url(notice_id, ""),
                    "cpv": cpv[:8], "mixed_lot": verdict["mixed_lot_warning"],
                        "deadline": deadline, "days_to_deadline": days_left,
                        "is_buyer_side": True,
                        "value": (tender.get("value") or {}).get("amount"),
                    },
                )
