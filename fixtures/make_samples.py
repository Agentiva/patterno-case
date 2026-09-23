#!/usr/bin/env python3
"""Baut aus den lokalen Vollfixtures die eingecheckten Samples.

WARUM ES DIESES SKRIPT GIBT
Die Vollfixtures wiegen zusammen ueber 150 MB und gehoeren nicht ins Repo.
Eingecheckt ist nur ein Sample - und ein zufaelliges Sample waere wertlos:
Die interessanten Pfade sind selten. Ein Zufallsschnitt aus 17.185 Releases
enthaelt mit hoher Wahrscheinlichkeit KEINEN auslaufenden Rahmenvertrag
(7 Treffer in 8 Wochen) und keinen unterlegenen Bieter (1 Treffer in 12
Monaten). `make demo` zeigte dann genau einen Signaltyp, und der Rest der
Pipeline blieb unbewiesen.

Deshalb wird gezielt geschichtet: Jeder Pfad, den die Pipeline kennt, kommt
mit einer garantierten Mindestzahl ins Sample.

    python3 fixtures/make_samples.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

FIX = Path(__file__).resolve().parent
TODAY = date.today()

FRAMEWORK_MIN, FRAMEWORK_MAX = 180, 270
TARGET = {
    "zuschlag_mit_gewinner": 60,   # awards[].suppliers benannt
    "alleinbieter": 60,            # genau ein tenderer, kein supplier
    "mehrbieter": 40,              # mehrere tenderer
    "rahmenvertrag_ablauf": 40,    # Los mit Vertragsende im Nachfassfenster
    "konsortium": 15,              # Name enthaelt eine Bietergemeinschaft
    "rest": 60,
}


def _bucket(rel: dict) -> str:
    tender = rel.get("tender") or {}
    sups = [s for a in (rel.get("awards") or [])
            for s in (a.get("suppliers") or []) if s.get("name")]
    tens = [t for t in (tender.get("tenderers") or []) if t.get("name")]

    for lot in tender.get("lots") or []:
        end = (lot.get("contractPeriod") or {}).get("endDate")
        if not end:
            continue
        try:
            days = (date.fromisoformat(end[:10]) - TODAY).days
        except ValueError:
            continue
        if FRAMEWORK_MIN <= days <= FRAMEWORK_MAX:
            return "rahmenvertrag_ablauf"

    names = " ".join(x.get("name", "") for x in sups + tens).lower()
    if any(w in names for w in ("bietergemeinschaft", " arge ", "konsortium")):
        return "konsortium"
    if sups:
        return "zuschlag_mit_gewinner"
    if len(tens) == 1:
        return "alleinbieter"
    if len(tens) > 1:
        return "mehrbieter"
    return "rest"


def sample_dovs() -> None:
    src = FIX / "vergabe_dovs.longlist.json"
    if not src.exists():
        src = FIX / "vergabe_dovs.json"
    releases = json.loads(src.read_text(encoding="utf-8"))

    # Neueste zuerst: Das Signalfenster der Demo sind 8 Wochen.
    releases.sort(key=lambda r: r.get("date") or "", reverse=True)

    picked: list[dict] = []
    counts = {k: 0 for k in TARGET}
    for rel in releases:
        b = _bucket(rel)
        if counts[b] < TARGET[b]:
            counts[b] += 1
            picked.append(rel)
        if all(counts[k] >= TARGET[k] for k in TARGET):
            break

    out = FIX / "vergabe_dovs.sample.json"
    out.write_text(json.dumps(picked, ensure_ascii=False), encoding="utf-8")
    print(f"{out.name}: {len(picked)} Releases aus {len(releases)}")
    for k, v in counts.items():
        mark = "ok " if v >= TARGET[k] else "!! "
        print(f"  {mark}{k:<24}{v:>4} / {TARGET[k]}")


def sample_plain(name: str, limit: int) -> None:
    src = FIX / f"{name}.json"
    if not src.exists():
        print(f"  ! {src.name} fehlt - uebersprungen")
        return
    rows = json.loads(src.read_text(encoding="utf-8"))
    out = FIX / f"{name}.sample.json"
    out.write_text(json.dumps(rows[:limit], ensure_ascii=False), encoding="utf-8")
    print(f"{out.name}: {min(limit, len(rows))} von {len(rows)}")


if __name__ == "__main__":
    sample_dovs()
    sample_plain("ted", 400)
    sample_plain("ba_jobs", 400)
