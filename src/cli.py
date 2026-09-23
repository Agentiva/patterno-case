"""Pipeline-Runner.

  python -m src.cli run    --live      # echte APIs
  python -m src.cli run                # Fixtures (offline, fuer Demo)
  python -m src.cli export             # CSVs nach data/
  python -m src.cli runlog             # Laufprotokoll

Der zweite Lauf hintereinander muss 0 neue Zeilen ausgeben. Das ist der
Beweis fuer Idempotenz und genau das, was der Case verlangt.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from src.config import ENRICH_SCORE_THRESHOLD
from src.resolve.normalize import (
    check_exclusion, needs_review, normalize_company,
    resolution_confidence, split_consortium,
)
from src.score.scoring import build_why_now, score_account
from src.sources.ba_jobs import BAJobsSource
from src.sources.dovs import VergabeSource
from src.sources.ted import TEDSource
from src.store import DeltaStore, RawSignal

DATA = Path("data")
SOURCES = {
    "vergabe_dovs": VergabeSource,   # Primaer DE, inkl. unterschwellig
    "ted": TEDSource,                # Ergaenzung EU-weit, oberschwellig
    "ba_jobs": BAJobsSource,
}


def resolve(sig: RawSignal, store: DeltaStore) -> list[RawSignal]:
    """Normalisieren, Konsortien splitten, ausschliessen, Confidence setzen.

    Stufe 4 des Waterfalls (Domain-Resolution ueber Clay/Apollo/Impressum)
    passiert bewusst ausserhalb - siehe docs/waterfalls.md. Hier entsteht
    nur der belastbare Firmenname plus eine ehrliche Confidence.
    """
    out: list[RawSignal] = []
    members, is_consortium = split_consortium(sig.org_name_raw)

    for member in members:
        excluded, reason = check_exclusion(member)
        if excluded:
            continue

        # Ohne externe Verifikation bleibt die Confidence bewusst gedeckelt.
        # Lieber ein ehrliches 0.65 als ein erfundenes 0.95.
        conf = resolution_confidence(
            name_sim=1.0,
            place_match=bool(sig.org_place),
            has_register_id=bool((sig.payload or {}).get("supplier_id")),
            impressum_verified=False,
        )
        if is_consortium:
            conf -= 0.10          # ARGE-Zuordnung ist systematisch unsicherer

        clone = RawSignal(
            source=sig.source,
            external_id=(f"{sig.external_id}:{normalize_company(member)[:40]}"
                         if is_consortium else sig.external_id),
            signal_type=sig.signal_type,
            event_date=sig.event_date,
            org_name_raw=member,
            org_place=sig.org_place,
            source_url=sig.source_url,
            title=sig.title,
            payload={**sig.payload, "consortium": is_consortium},
        )
        clone.match_confidence = round(max(conf, 0.0), 3)
        clone.company_id = normalize_company(member)

        if needs_review(clone.match_confidence):
            store.queue_for_review(clone, [member], "confidence unter Schwelle")
        out.append(clone)
    return out


def cmd_run(args: argparse.Namespace) -> int:
    store = DeltaStore()
    selected = [args.source] if args.source else list(SOURCES)
    grand = defaultdict(int)

    for name in selected:
        src = SOURCES[name]()
        run_id = store.start_run(name)
        since = store.fetch_since(name)
        stats = defaultdict(int)
        errors = None
        print(f"\n[{name}] ab {since.isoformat()} (live={args.live})")

        try:
            for raw in src.fetch(since, live=args.live):
                stats["in"] += 1
                for sig in resolve(raw, store):
                    stats[store.upsert(sig, run_id)] += 1
        except Exception as exc:                       # noqa: BLE001
            errors = f"{type(exc).__name__}: {exc}"
            print(f"  ! {errors}")

        store.finish_run(run_id, stats, errors)
        emitted = store.emitted_in_run(run_id)
        print(f"  gelesen {stats['in']} | neu {stats['new']} | "
              f"geaendert {stats['changed']} | unveraendert {stats['unchanged']} "
              f"-> ausgegeben {len(emitted)}")
        for k, v in stats.items():
            grand[k] += v

    print(f"\nGesamt: neu {grand['new']}, geaendert {grand['changed']}, "
          f"unveraendert {grand['unchanged']}")
    if grand["new"] == 0 and grand["changed"] == 0:
        print("-> Keine Aenderungen. Genau so soll ein zweiter Lauf aussehen.")
    store.close()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    store = DeltaStore()
    DATA.mkdir(exist_ok=True)
    rows = store.active_signals(days=args.days)

    by_company: dict[str, list[dict]] = defaultdict(list)
    buyer_side: list[dict] = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"] or "{}")
        # Ein offenes Verfahren gehoert der VERGABESTELLE, nicht einem Bieter.
        # Diese Zeilen duerfen niemals als Account in eine Outbound-Liste
        # geraten - die Vergabestelle ist das Gegenueber des Zielkunden.
        # Sie wandern in einen eigenen Feed und werden dort ueber CPV und
        # Region gegen Longlist 1 gejoint.
        if d["payload"].get("is_buyer_side"):
            buyer_side.append(d)
            continue
        by_company[d["company_id"] or d["org_name_raw"]].append(d)

    out = []
    for company_id, sigs in by_company.items():
        # Tier kommt in der Vollversion aus Longlist 1 (JOIN ueber die Domain).
        # Ohne diesen Join bleibt es bei C - und das wird auch so exportiert,
        # statt eine Einstufung zu erfinden.
        tier = "C"
        score, comp = score_account(sigs, tier=tier)
        # Der Why-now-Satz MUSS aus dem Signal kommen, das den Score treibt.
        driver = comp.pop("driver_signal", None) or sigs[0]
        out.append({
            "company_id": company_id,
            "firma_raw": driver["org_name_raw"],
            "ort": driver.get("org_place") or "",
            "domain": driver.get("domain") or "",
            "tier": tier,
            "score": score,
            "signal_type": comp["driver"]["signal_type"],
            "signal_datum": comp["driver"]["event_date"],
            "quell_url": comp["driver"]["source_url"] or "",
            "signal_anzahl": comp["signal_count"],
            "signal_typen": ";".join(comp["distinct_signal_types"]),
            "match_confidence": driver.get("match_confidence"),
            "in_longlist_1": "",      # wird beim Join mit Longlist 1 gesetzt
            "enrich": "ja" if score >= ENRICH_SCORE_THRESHOLD else "nein",
            "why_now": build_why_now(driver),
            "score_components": json.dumps(comp, ensure_ascii=False),
        })

    out.sort(key=lambda r: r["score"], reverse=True)
    path = DATA / "longlist_signale.csv"
    if out:
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0]), quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(out)
    print(f"{path}: {len(out)} Accounts "
          f"({sum(1 for r in out if r['enrich'] == 'ja')} ueber Enrichment-Schwelle)")

    # Vergabestellen-Feed separat: Input fuer den Join gegen Longlist 1,
    # nicht fuer Outbound.
    if buyer_side:
        bpath = DATA / "offene_verfahren.csv"
        brows = [{
            "ocid": b["payload"].get("ocid"),
            "vergabestelle": b["org_name_raw"],
            "titel": b["title"],
            "cpv": ";".join(b["payload"].get("cpv", [])),
            "frist": b["payload"].get("deadline"),
            "tage_bis_frist": b["payload"].get("days_to_deadline"),
            "wert": b["payload"].get("value"),
            "quell_url": b["source_url"],
        } for b in buyer_side]
        with bpath.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(brows[0]), quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(brows)
        print(f"{bpath}: {len(brows)} offene Verfahren (Join-Input, kein Outbound)")

    review = store.conn.execute("SELECT COUNT(*) c FROM review_queue").fetchone()["c"]
    print(f"Review-Queue: {review} Treffer unter Confidence-Schwelle (nicht geraten)")
    store.close()
    return 0


def cmd_runlog(_: argparse.Namespace) -> int:
    store = DeltaStore()
    print(f"{'run':>4} {'quelle':<16} {'start':<20} {'in':>5} {'neu':>5} "
          f"{'geae.':>6} {'unver.':>7}  fehler")
    for r in store.run_log():
        print(f"{r['run_id']:>4} {r['source']:<16} {r['started_at']:<20} "
              f"{r['rows_in']:>5} {r['rows_new']:>5} {r['rows_changed']:>6} "
              f"{r['rows_unchanged']:>7}  {r['errors'] or ''}")
    store.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="patterno-signals")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Signale abrufen")
    r.add_argument("--live", action="store_true", help="echte APIs statt Fixtures")
    r.add_argument("--source", choices=list(SOURCES))
    r.set_defaults(func=cmd_run)

    e = sub.add_parser("export", help="CSV schreiben")
    e.add_argument("--days", type=int, default=56, help="Signalfenster (Default 56 = 8 Wochen)")
    e.set_defaults(func=cmd_export)

    lg = sub.add_parser("runlog", help="Laufprotokoll")
    lg.set_defaults(func=cmd_runlog)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
