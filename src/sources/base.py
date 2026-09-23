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

    # Zwei Laeufe teilen sich eine Quelle, brauchen aber verschiedene Korpora:
    #   run      -> 3 Monate, Signalfenster
    #   longlist -> 12 Monate, Marktuniversum
    # Bis zum 23.09.2026 schrieben beide in dieselbe Datei. Der kuerzere Lauf
    # ueberschrieb also den laengeren, und der naechste Longlist-Lauf baute
    # die Marktliste aus 2 Monaten statt 12: 38 Firmen statt 342 - ohne
    # Fehlermeldung. Deshalb bekommt jeder Korpus seinen eigenen Slot.
    fixture_variant: str = ""

    def fixture_path(self) -> Path:
        suffix = f".{self.fixture_variant}" if self.fixture_variant else ""
        return FIXTURE_DIR / f"{self.name}{suffix}.json"

    def sample_path(self) -> Path:
        """Kleines, versioniertes Sample fuer `make demo`.

        Die Vollfixtures sind zu gross fuers Repo (der DOEE-Export aus 12
        Monaten wiegt 86 MB). Sie bleiben lokal und stehen in .gitignore;
        eingecheckt ist nur das Sample, damit ein frischer Clone sofort
        `make demo` fahren kann.
        """
        return FIXTURE_DIR / f"{self.name}.sample.json"

    def load_fixture(self) -> list[dict]:
        p = self.fixture_path()
        if not p.exists():
            p = self.sample_path()
        if not p.exists():
            raise FileNotFoundError(
                f"Weder Fixture noch Sample vorhanden: {self.fixture_path()}\n"
                f"Einmal mit --live laufen lassen, dann wird die Fixture geschrieben."
            )
        return json.loads(p.read_text(encoding="utf-8"))

    # 200 war zu wenig: Die Longlist braucht alle Zuschlagsbekanntmachungen
    # aus 12 Monaten. Bei 200 Releases blieben nach dem IT-Filter 14 uebrig,
    # davon keine mit Zuschlag -> Longlist leer.
    # 20.000 sind es immer noch: 12 Monate DOEE sind rund 190.000 Releases.
    # Die Grenze schuetzt nur die Platte, deshalb gilt sie je Variante - und
    # sie schneidet nie mehr stumm ab.
    MAX_FIXTURE_ROWS = 20000

    def save_fixture(self, rows: list[dict]) -> None:
        p = self.fixture_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if len(rows) > self.MAX_FIXTURE_ROWS:
            print(f"  ! Fixture {p.name}: {len(rows)} Zeilen auf "
                  f"{self.MAX_FIXTURE_ROWS} gekuerzt - Offline-Laeufe sehen "
                  f"weniger als der Live-Lauf.")
        p.write_text(
            json.dumps(rows[: self.MAX_FIXTURE_ROWS], ensure_ascii=False),
            encoding="utf-8",
        )
