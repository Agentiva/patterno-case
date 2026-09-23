"""Delta-Store: haelt fest, was wir schon gesehen haben.

Kernanforderung aus dem Case: "Bei einem erneuten Lauf soll die Pipeline nur
neue oder veraenderte Treffer ausgeben."

Zwei Mechanismen:
  1. signal_id   = sha256(source, external_id)  -> Identitaet
  2. content_hash = sha256(relevante Felder)    -> Veraenderung

Ein Treffer wird ausgegeben, wenn er neu ist ODER sein content_hash sich
gegenueber dem gespeicherten Stand geaendert hat.

Warum ein Overlap-Fenster statt "seit last_run":
Bekanntmachungen werden nachtraeglich publiziert und Stellenanzeigen
nachtraeglich editiert. Wer nur ab last_run zieht, verliert genau diese
Faelle. Wir ziehen deshalb immer OVERLAP_DAYS zurueck und deduplizieren
ueber die ID, nicht ueber das Datum.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

OVERLAP_DAYS = 14

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    signal_id     TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    external_id   TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    signal_type   TEXT NOT NULL,
    event_date    TEXT,
    org_name_raw  TEXT,
    org_place     TEXT,
    domain        TEXT,
    company_id    TEXT,
    match_confidence REAL,
    source_url    TEXT,
    title         TEXT,
    payload       TEXT,
    first_seen_run INTEGER NOT NULL,
    first_seen_at  TEXT NOT NULL,
    last_seen_run  INTEGER NOT NULL,
    last_seen_at   TEXT NOT NULL,
    change_count   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_signals_source   ON signals(source);
CREATE INDEX IF NOT EXISTS idx_signals_domain   ON signals(domain);
CREATE INDEX IF NOT EXISTS idx_signals_event    ON signals(event_date);

CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    rows_in     INTEGER DEFAULT 0,
    rows_new    INTEGER DEFAULT 0,
    rows_changed INTEGER DEFAULT 0,
    rows_unchanged INTEGER DEFAULT 0,
    errors      TEXT
);

-- Treffer unterhalb der Resolver-Confidence landen hier statt geraten zu werden.
CREATE TABLE IF NOT EXISTS review_queue (
    signal_id   TEXT PRIMARY KEY,
    org_name_raw TEXT,
    org_place   TEXT,
    candidates  TEXT,
    reason      TEXT,
    created_at  TEXT
);
"""


@dataclass
class RawSignal:
    """Was ein Source-Adapter liefert. Quellneutral."""
    source: str
    external_id: str
    signal_type: str
    event_date: str | None            # ISO YYYY-MM-DD
    org_name_raw: str
    org_place: str | None = None
    source_url: str | None = None
    title: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    # wird nach der Resolution gefuellt
    domain: str | None = None
    company_id: str | None = None
    match_confidence: float | None = None

    @property
    def signal_id(self) -> str:
        return hashlib.sha256(
            f"{self.source}|{self.external_id}".encode("utf-8")
        ).hexdigest()[:32]

    @property
    def content_hash(self) -> str:
        """Nur fachlich relevante Felder. Reihenfolge stabil halten,
        sonst flappt der Hash und alles gilt als 'changed'."""
        relevant = {
            "signal_type": self.signal_type,
            "event_date": self.event_date,
            "org_name_raw": self.org_name_raw,
            "org_place": self.org_place,
            "title": self.title,
            "payload": {k: self.payload[k] for k in sorted(self.payload)},
        }
        blob = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


class DeltaStore:
    def __init__(self, path: str | Path = "data/state.sqlite"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -- Laufsteuerung ---------------------------------------------------------
    def start_run(self, source: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (source, started_at) VALUES (?, ?)",
            (source, datetime.utcnow().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, stats: dict[str, int], errors: str | None = None) -> None:
        self.conn.execute(
            """UPDATE runs SET finished_at=?, rows_in=?, rows_new=?,
               rows_changed=?, rows_unchanged=?, errors=? WHERE run_id=?""",
            (
                datetime.utcnow().isoformat(timespec="seconds"),
                stats.get("in", 0), stats.get("new", 0),
                stats.get("changed", 0), stats.get("unchanged", 0),
                errors, run_id,
            ),
        )
        self.conn.commit()

    def fetch_since(self, source: str) -> date:
        """Ab wann ziehen wir? Letzter erfolgreicher Lauf minus Overlap-Fenster.
        Ohne Vorlauf: 56 Tage (= das im Case geforderte 4-8-Wochen-Fenster)."""
        row = self.conn.execute(
            """SELECT started_at FROM runs WHERE source=? AND finished_at IS NOT NULL
               ORDER BY run_id DESC LIMIT 1""",
            (source,),
        ).fetchone()
        if not row:
            return date.today() - timedelta(days=56)
        last = datetime.fromisoformat(row["started_at"]).date()
        return last - timedelta(days=OVERLAP_DAYS)

    # -- Kern: Upsert mit Delta-Erkennung --------------------------------------
    def upsert(self, sig: RawSignal, run_id: int) -> str:
        """Gibt 'new' | 'changed' | 'unchanged' zurueck."""
        now = datetime.utcnow().isoformat(timespec="seconds")
        existing = self.conn.execute(
            "SELECT content_hash, change_count FROM signals WHERE signal_id=?",
            (sig.signal_id,),
        ).fetchone()

        if existing is None:
            self.conn.execute(
                """INSERT INTO signals (signal_id, source, external_id, content_hash,
                   signal_type, event_date, org_name_raw, org_place, domain, company_id,
                   match_confidence, source_url, title, payload,
                   first_seen_run, first_seen_at, last_seen_run, last_seen_at, change_count)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
                (sig.signal_id, sig.source, sig.external_id, sig.content_hash,
                 sig.signal_type, sig.event_date, sig.org_name_raw, sig.org_place,
                 sig.domain, sig.company_id, sig.match_confidence, sig.source_url,
                 sig.title, json.dumps(sig.payload, ensure_ascii=False),
                 run_id, now, run_id, now),
            )
            self.conn.commit()
            return "new"

        if existing["content_hash"] != sig.content_hash:
            self.conn.execute(
                """UPDATE signals SET content_hash=?, signal_type=?, event_date=?,
                   org_name_raw=?, org_place=?, domain=?, company_id=?,
                   match_confidence=?, source_url=?, title=?, payload=?,
                   last_seen_run=?, last_seen_at=?, change_count=change_count+1
                   WHERE signal_id=?""",
                (sig.content_hash, sig.signal_type, sig.event_date, sig.org_name_raw,
                 sig.org_place, sig.domain, sig.company_id, sig.match_confidence,
                 sig.source_url, sig.title, json.dumps(sig.payload, ensure_ascii=False),
                 run_id, now, sig.signal_id),
            )
            self.conn.commit()
            return "changed"

        self.conn.execute(
            "UPDATE signals SET last_seen_run=?, last_seen_at=? WHERE signal_id=?",
            (run_id, now, sig.signal_id),
        )
        self.conn.commit()
        return "unchanged"

    def queue_for_review(self, sig: RawSignal, candidates: list, reason: str) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO review_queue
               (signal_id, org_name_raw, org_place, candidates, reason, created_at)
               VALUES (?,?,?,?,?,?)""",
            (sig.signal_id, sig.org_name_raw, sig.org_place,
             json.dumps(candidates, ensure_ascii=False), reason,
             datetime.utcnow().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    # -- Auslesen --------------------------------------------------------------
    def emitted_in_run(self, run_id: int) -> list[sqlite3.Row]:
        """Genau das, was der Case verlangt: nur neu oder veraendert."""
        return self.conn.execute(
            """SELECT * FROM signals
               WHERE first_seen_run = ?
                  OR (last_seen_run = ? AND change_count > 0)
               ORDER BY event_date DESC""",
            (run_id, run_id),
        ).fetchall()

    def active_signals(self, days: int = 56) -> list[sqlite3.Row]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return self.conn.execute(
            "SELECT * FROM signals WHERE event_date >= ? ORDER BY event_date DESC",
            (cutoff,),
        ).fetchall()

    def run_log(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM runs ORDER BY run_id DESC LIMIT ?", (limit,)
        ).fetchall()

    def close(self) -> None:
        self.conn.close()
