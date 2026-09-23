"""Gemeinsames Interface aller Signalquellen.

Eine Pipeline, N Adapter. Neue Quelle = neue Klasse, sonst aendert sich nichts.
Genau das ist der Punkt: Die Delta-Logik, die Resolution und das Scoring
existieren einmal, nicht pro Quelle.

Jeder Adapter kann offline laufen (fixtures/) damit `make demo` ohne
Netzzugang und ohne API-Keys funktioniert - wichtig fuer eine Live-Demo,
bei der man sich nicht auf fremde APIs verlassen will.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable, Protocol

from src.store import RawSignal

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"


class SignalSource(Protocol):
    name: str
    signal_type: str

    def fetch(self, since: date, live: bool = True) -> Iterable[RawSignal]:
        ...


class FixtureMixin:
    """Laedt eine gespeicherte Antwort statt die echte API zu rufen."""

    name: str

    def fixture_path(self) -> Path:
        return FIXTURE_DIR / f"{self.name}.json"

    def load_fixture(self) -> list[dict]:
        p = self.fixture_path()
        if not p.exists():
            raise FileNotFoundError(
                f"Fixture fehlt: {p}\n"
                f"Einmal mit --live laufen lassen, dann wird sie geschrieben."
            )
        return json.loads(p.read_text(encoding="utf-8"))

    def save_fixture(self, rows: list[dict]) -> None:
        p = self.fixture_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(rows[:200], ensure_ascii=False, indent=2), encoding="utf-8"
        )
