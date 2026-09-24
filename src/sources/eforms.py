"""Angebotsfristen aus dem eForms-XML nachladen.

=== WARUM ES DIESES MODUL GIBT ===
Der Signaltyp `offene_ausschreibung_im_profil` hat nie gefeuert. Die Suche
nach der Ursache lief zweimal in die Irre:

  1. Der Adapter las `tender.tenderPeriod.endDate`  -> 0 Treffer
  2. Ersatzweise `tender.awardPeriod.endDate`        -> nur bei bereits
                                                        vergebenen Verfahren

Daraus wurde der Schluss gezogen, der Feed fuehre keine Angebotsfrist. Das
war falsch. Er fuehrt sie nur nicht im OCDS-JSON.

Dieselbe Bekanntmachung als XML abgerufen (24.09.2026, Notice
b620a611-d587-4da1-90a3-11779974625e):

    GET /api/notices/<id>        -> 200, application/xml, 354 KB
    cac:TenderSubmissionDeadlinePeriod
        cbc:EndDate   2026-10-01+02:00
        cbc:EndTime   12:00:00+02:00
    17 von 17 Losen tragen die Frist

Das ist BT-131 aus eForms-DE. Die URL dafuer baut dovs.notice_url() schon
laenger - sie wurde nur nie gelesen.

=== WARUM MIT CACHE ===
Im Korpus stehen 9.975 laufende Verfahren; im 8-Wochen-Fenster sind es
1.568. Ein XML wiegt rund 350 KB. Jeden Lauf alles neu zu holen waere
eine halbe Gigabyte fuer Daten, die sich nicht aendern.

Die Frist steht fest, sobald die Bekanntmachung veroeffentlicht ist. Sie
kann nachtraeglich verschoben werden - dafuer gibt es das
Ueberlappungsfenster der Pipeline, das dieselbe Bekanntmachung erneut
liest und die Aenderung als `changed` erkennt.

Deshalb: Cache auf Platte, Schluessel ist die notice_id.
    Erstlauf   ~800 Abrufe
    danach     ~200 je Woche
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

CACHE = Path("data/eforms_fristen.json")
NOTICE_URL = "https://oeffentlichevergabe.de/api/notices/{id}"
TIMEOUT = 30
WORKER = 6

# BT-131, Frist fuer den Eingang der Angebote. Steht je Los.
DEADLINE_BLOCK = re.compile(
    r"<cac:TenderSubmissionDeadlinePeriod>(.*?)</cac:TenderSubmissionDeadlinePeriod>",
    re.S)
END_DATE = re.compile(r"<cbc:EndDate>([^<]+)</cbc:EndDate>")
END_TIME = re.compile(r"<cbc:EndTime>([^<]+)</cbc:EndTime>")


def _load() -> dict:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Ein kaputter Cache darf den Lauf nicht stoppen - er wird neu
        # aufgebaut. Stillschweigend passiert das nicht.
        print("  ! eforms: Cache unlesbar, wird neu aufgebaut")
        return {}


def _save(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def parse_deadline(xml: str) -> dict | None:
    """Frueheste Angebotsfrist des Dokuments.

    Mehrlosverfahren tragen die Frist je Los. Wer nachfassen will, muss
    sich an der FRUEHESTEN orientieren - die entscheidet, wann es eng wird.
    """
    beste = None
    lose = 0
    for block in DEADLINE_BLOCK.findall(xml):
        d = END_DATE.search(block)
        if not d:
            continue
        lose += 1
        t = END_TIME.search(block)
        datum = d.group(1)[:10]
        if beste is None or datum < beste["deadline"]:
            beste = {"deadline": datum,
                     "uhrzeit": (t.group(1)[:8] if t else ""),
                     "lose_mit_frist": lose}
    if beste:
        beste["lose_mit_frist"] = lose
    return beste


def _fetch(notice_id: str) -> tuple[str, dict | None]:
    try:
        r = requests.get(NOTICE_URL.format(id=notice_id), timeout=TIMEOUT)
        if r.status_code != 200:
            return notice_id, {"fehler": f"HTTP {r.status_code}"}
        return notice_id, parse_deadline(r.text) or {"fehler": "keine Frist im XML"}
    except requests.RequestException as exc:
        return notice_id, {"fehler": type(exc).__name__}


def fristen(notice_ids: list[str], live: bool = True) -> dict:
    """notice_id -> {deadline, uhrzeit, lose_mit_frist} oder {fehler}.

    Ohne live werden nur zwischengespeicherte Werte zurueckgegeben; der
    Offline-Lauf holt also nichts nach.
    """
    cache = _load()
    offen = [n for n in dict.fromkeys(notice_ids) if n and n not in cache]

    if not live:
        if offen:
            print(f"  . eforms: {len(offen)} Fristen fehlen im Cache "
                  f"(offline, nichts nachgeladen)")
        return cache

    if offen:
        print(f"  . eforms: {len(cache)} Fristen im Cache, "
              f"{len(offen)} werden geholt")
        fehler = 0
        fertig = 0
        with ThreadPoolExecutor(max_workers=WORKER) as pool:
            for nid, res in pool.map(_fetch, offen):
                cache[nid] = res or {"fehler": "leer"}
                fertig += 1
                if res and "fehler" in res:
                    fehler += 1
                # Zwischenspeichern. Beim ersten Lauf sind es mehrere
                # hundert Abrufe - ohne das waere ein Abbruch nach zehn
                # Minuten ein Totalverlust, und der naechste Lauf finge
                # wieder bei null an.
                if fertig % 50 == 0:
                    _save(cache)
                    print(f"    {fertig}/{len(offen)} geholt")
        _save(cache)
        if fehler:
            quote = fehler / len(offen)
            print(f"  . eforms: {fehler} von {len(offen)} ohne Frist "
                  f"({quote:.0%})")
            # Eine hohe Fehlerquote heisst: Das Feld heisst anders oder die
            # API hat sich geaendert. Das darf nicht als "diese Woche keine
            # offenen Verfahren" durchgehen - genau so ist dieser Signaltyp
            # ueber Wochen unbemerkt tot gewesen.
            if quote > 0.5:
                print(f"  ! eforms: mehr als die Haelfte ohne Frist. "
                      f"Feldnamen gegen das XML pruefen, bevor die Zahlen "
                      f"geglaubt werden.")
    return cache


def statistik(cache: dict) -> dict:
    mit = sum(1 for v in cache.values() if v and "deadline" in v)
    return {"gesamt": len(cache), "mit_frist": mit,
            "ohne_frist": len(cache) - mit}
