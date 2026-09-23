"""Belegt jede proof_url wirklich das, was sie behauptet?

=== WARUM ES DIESES SKRIPT GIBT ===
Die erste Version der Pipeline baute Beleg-URLs nach dem Muster
    https://oeffentlichevergabe.de/ui/de/notice/<ocid>
Das war geraten, nie abgerufen. Im Browser erschien
"Wir koennen diese Seite nicht finden".

Der Grund ist fies: Die Seite ist eine Single-Page-App. Sie antwortet auf
JEDE /ui/-URL mit HTTP 200 und derselben 1.309 Byte grossen Huelle; die
404-Meldung rendert erst JavaScript im Browser. Ein naiver Status-Check
haette den Fehler also BESTAETIGT statt ihn zu finden.

Zwei Lehren, beide im Code verankert:
  1. Wir verlinken die API, nicht die SPA. Deren Status ist ehrlich.
  2. Ein Statuscode allein reicht nicht - wir pruefen zusaetzlich
     Content-Type und Groesse.

Verifiziert am 23.09.2026:
    /api/notices/<release id>             -> 200  application/xml
    /api/notices/<release id>?format=pdf  -> 200  application/pdf
    /api/notices/<ocid>                   -> 404
    /ui/de/notice/<irgendwas>             -> 200, aber immer 1.309 Byte SPA

Aufruf:
    python3 -m src.verify_proofs --sample 25
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import requests

DATA = Path("data")
TIMEOUT = 25

# Antwortet eine URL mit genau dieser Groesse, ist es die leere SPA-Huelle.
SPA_SHELL_BYTES = {1309}
OK_TYPES = ("application/pdf", "application/xml", "text/xml", "application/json")

# TED beantwortet JEDE serverseitige Anfrage mit HTTP 202 und 0 Byte - eine
# JavaScript-Challenge. Geprueft am 23.09.2026 mit Browser-User-Agent gegen
# /en/notice/-/detail/, /udl?uri=, /pdf, /xml und /html: ueberall 202/0.
# Diese URLs sind damit weder bestaetigt noch widerlegt. Sie als Fehler zu
# zaehlen waere genauso falsch wie sie stillschweigend durchzuwinken -
# deshalb eine eigene dritte Kategorie.
CHALLENGE_HOSTS = ("ted.europa.eu",)


def check(url: str) -> dict:
    if not url:
        return {"ok": False, "status": 0, "reason": "keine URL"}
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return {"ok": False, "status": 0, "reason": f"nicht erreichbar: {exc}"}

    ctype = (r.headers.get("content-type") or "").split(";")[0].strip()
    size = len(r.content)

    if (r.status_code == 202 and size == 0
            and any(h in url for h in CHALLENGE_HOSTS)):
        return {"ok": False, "unverifiable": True, "status": 202, "size": 0,
                "type": ctype,
                "reason": "JS-Challenge - maschinell nicht pruefbar"}
    if r.status_code != 200:
        return {"ok": False, "status": r.status_code, "size": size,
                "type": ctype, "reason": f"HTTP {r.status_code}"}
    if size in SPA_SHELL_BYTES:
        return {"ok": False, "status": 200, "size": size, "type": ctype,
                "reason": "SPA-Huelle - die Seite zeigt im Browser 404"}
    if ctype not in OK_TYPES:
        return {"ok": False, "status": 200, "size": size, "type": ctype,
                "reason": f"unerwarteter Content-Type {ctype}"}
    if size < 500:
        return {"ok": False, "status": 200, "size": size, "type": ctype,
                "reason": "Antwort verdaechtig klein"}
    return {"ok": True, "status": 200, "size": size, "type": ctype, "reason": ""}


def main() -> int:
    ap = argparse.ArgumentParser(prog="verify-proofs")
    ap.add_argument("--file", default=str(DATA / "longlist_markt.csv"))
    ap.add_argument("--column", default="proof_url")
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    path = Path(a.file)
    if not path.exists():
        sys.exit(f"{path} fehlt")

    with path.open(encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get(a.column)]
    if not rows:
        sys.exit(f"Spalte {a.column} ist leer")

    random.seed(a.seed)
    sample = random.sample(rows, min(a.sample, len(rows)))
    print(f"Pruefe {len(sample)} von {len(rows)} Zeilen aus {path.name}\n")

    ok = 0
    failures: list[tuple[str, str, str]] = []
    unverifiable: list[tuple[str, str, str]] = []
    for i, row in enumerate(sample, 1):
        res = check(row[a.column])
        ok += res["ok"]
        mark = "OK " if res["ok"] else ("?  " if res.get("unverifiable") else "FEHL")
        name = (row.get("legal_name") or row.get("firma_raw") or "")[:34]
        print(f"  {i:>2}. [{mark}] {name:<36}{res.get('type','-'):<18}"
              f"{res.get('size','-'):>8}  {res['reason'][:44]}")
        if res.get("unverifiable"):
            unverifiable.append((name, row[a.column], res["reason"]))
        elif not res["ok"]:
            failures.append((name, row[a.column], res["reason"]))

    checkable = len(sample) - len(unverifiable)
    rate = ok / checkable if checkable else 0.0
    print(f"\nPruefbar: {checkable}/{len(sample)} - davon erreichbar und "
          f"plausibel: {ok} = {rate:.0%}")
    if unverifiable:
        print(f"Nicht maschinell pruefbar: {len(unverifiable)} "
              f"(Quelle hinter JS-Challenge, im Browser aufzurufen)")
        for name, url, _ in unverifiable[:5]:
            print(f"  {name}\n    {url}")
    if failures:
        print("\nFehlschlaege:")
        for name, url, reason in failures:
            print(f"  {name}\n    {url}\n    -> {reason}")
    return 0 if (checkable and rate >= 0.95) else 1


if __name__ == "__main__":
    sys.exit(main())
