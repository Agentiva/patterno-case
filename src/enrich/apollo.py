"""Apollo-Enrichment fuer die gesamte Longlist - scriptbar statt Chat-Roundtrips.

WARUM ALS SKRIPT UND NICHT UEBER MCP
Der MCP-Lookup loest eine Firma pro Aufruf auf. Bei 342 Firmen waeren das
~342 Aufrufe nur fuer Domains, dann ~35 Enrichment-Calls und nochmal hunderte
fuer Kontakte. Nicht resumierbar, nicht exportierbar, nicht wiederholbar.
Apollo weist in seinen eigenen Tool-Beschreibungen darauf hin.

Hier laeuft dieselbe Logik gegen die REST-API:
  - Cache auf Platte: jeder Treffer wird gespeichert, ein Abbruch kostet nichts
  - Rate-Limiting und Backoff
  - Trockenlauf (--dry-run) zeigt die Credit-Kosten VOR dem ersten Call
  - Jede Stufe schreibt ihre Trefferquote ins Log

KOSTEN (Stand Apollo-Doku, vor dem Lauf mit --dry-run pruefen)
  organizations/bulk_enrich : 1 Credit je Treffer,  0 bei Fehlschlag
  mixed_people/search       : 1 Credit je Anfrage mit Ergebnis
  people/bulk_match         : 1 Credit je Treffer
  organizations/lookup      : kostenlos

AUFRUF
  export APOLLO_API_KEY=...
  python3 -m src.enrich.apollo --dry-run              # nur Kalkulation
  python3 -m src.enrich.apollo --stage domains
  python3 -m src.enrich.apollo --stage firmographics
  python3 -m src.enrich.apollo --stage contacts --max-per-account 3
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import requests

from src.resolve.domain_verify import verify
from src.resolve.impressum import verify_impressum
from src.resolve.normalize import normalize_company

API = "https://api.apollo.io/api/v1"
DATA = Path("data")
CACHE = DATA / "apollo_cache"
LONGLIST = DATA / "longlist_markt.csv"

RATE_SLEEP = 0.35          # ~3 Anfragen/Sekunde
MAX_RETRIES = 4

# Personas aus dem Playbook. Reihenfolge = Prioritaet beim Kontakt-Ziehen.
PERSONA_TITLES = [
    ("Champion - Bid/Tender", [
        "Bid Manager", "Angebotsmanager", "Ausschreibungsmanager",
        "Tender Manager", "Leiter Angebotswesen", "Bietermanagement",
        "Vergabemanagement", "Submission",
    ]),
    ("Economic Buyer", [
        "Geschäftsführer", "Managing Director", "Vertriebsleiter",
        "Leiter Vertrieb", "Head of Public Sector", "Head of Sales",
        "Leiter Öffentliche Auftraggeber",
    ]),
    ("User/Nutzer", [
        "Key Account Manager Public Sector", "Account Manager",
        "Pre-Sales Consultant", "Vertriebsinnendienst",
    ]),
]


def key() -> str:
    k = os.getenv("APOLLO_API_KEY")
    if not k:
        sys.exit("APOLLO_API_KEY ist nicht gesetzt. "
                 "Key in Apollo unter Settings > Integrations > API erzeugen.")
    return k


def call(path: str, payload: dict, method: str = "POST") -> dict:
    """Ein API-Aufruf mit Backoff. 429 und 5xx werden wiederholt."""
    url = f"{API}{path}"
    headers = {"Content-Type": "application/json", "Cache-Control": "no-cache",
               "x-api-key": key()}
    for attempt in range(MAX_RETRIES):
        try:
            if method == "POST":
                r = requests.post(url, json=payload, headers=headers, timeout=60)
            else:
                r = requests.get(url, params=payload, headers=headers, timeout=60)
        except requests.RequestException as exc:
            wait = 2 ** attempt
            print(f"    ! Netzfehler ({exc}), warte {wait}s")
            time.sleep(wait)
            continue

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2 ** (attempt + 2)))
            print(f"    . Rate Limit, warte {wait}s")
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        if r.status_code >= 400:
            print(f"    ! HTTP {r.status_code}: {r.text[:160]}")
            return {}
        time.sleep(RATE_SLEEP)
        return r.json()
    return {}


# --- Cache -------------------------------------------------------------------
def cache_path(stage: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / f"{stage}.json"


def load_cache(stage: str) -> dict:
    p = cache_path(stage)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_cache(stage: str, data: dict) -> None:
    cache_path(stage).write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def read_longlist() -> list[dict]:
    with LONGLIST.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


# --- Stufe 1+2+3: Domain -----------------------------------------------------
def stage_domains(rows: list[dict], check_impressum: bool = True) -> dict:
    """Name -> Domain, dreistufig mit Verifikation. Kostenlos."""
    cache = load_cache("domains")
    stats = {"cached": 0, "stage1": 0, "stage2": 0, "impressum_ok": 0,
             "rejected": 0, "none": 0}

    for i, row in enumerate(rows, 1):
        cid = row["company_id"]
        if cid in cache:
            stats["cached"] += 1
            continue

        name, city = row["legal_name"], row.get("city") or None
        result = {"domain": "", "confidence": 0.0, "stage": 0, "note": ""}

        for stage, params in (
            (1, {"q_organization_fuzzy_name": name,
                 "organization_locations": ["Germany"], "per_page": 1}),
            (2, {"q_organization_fuzzy_name": " ".join(name.split()[:2]),
                 "per_page": 3}),
        ):
            data = call("/mixed_companies/search", params)
            orgs = (data.get("organizations") or []) + (data.get("accounts") or [])
            for org in orgs[:3]:
                cand = {"name": org.get("name"),
                        "domain": org.get("primary_domain") or org.get("domain"),
                        "country": (org.get("country") or "")}
                v = verify(name, city, cand, stage)
                if v["accepted"]:
                    result = {"domain": v["domain"], "confidence": v["confidence"],
                              "stage": stage, "note": v["signals"]}
                    stats[f"stage{stage}"] += 1
                    break
                # Stufe 3: Heuristik unsicher -> Impressum entscheidet
                if check_impressum and cand["domain"]:
                    imp = verify_impressum(cand["domain"], name, city)
                    if imp["match"]:
                        result = {"domain": cand["domain"],
                                  "confidence": round(0.5 + imp["confidence_delta"], 3),
                                  "stage": 3, "note": f"Impressum: {imp['evidence']}"}
                        stats["impressum_ok"] += 1
                        break
                result["note"] = v["reject_reason"]
            if result["domain"]:
                break

        if not result["domain"]:
            stats["rejected" if result["note"] else "none"] += 1
        cache[cid] = result
        if i % 25 == 0:
            save_cache("domains", cache)
            print(f"  {i}/{len(rows)} | {stats}")

    save_cache("domains", cache)
    print(f"\nDomains: {stats}")
    return cache


# --- Stufe 4: Firmographics --------------------------------------------------
def stage_firmographics(domains: dict) -> dict:
    """Domain -> Mitarbeiterzahl, Branche. 1 Credit je Treffer."""
    cache = load_cache("firmographics")
    todo = sorted({d["domain"] for d in domains.values()
                   if d.get("domain") and d["domain"] not in cache})
    print(f"Firmographics: {len(todo)} offen (bis zu {len(todo)} Credits)")

    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        data = call("/organizations/bulk_enrich", {"domains": batch})
        for org in data.get("organizations") or []:
            dom = org.get("primary_domain")
            if dom:
                cache[dom] = {
                    "name": org.get("name"),
                    "employees": org.get("estimated_num_employees"),
                    "industry": org.get("industry"),
                    "naics": org.get("naics_codes") or [],
                    "sic": org.get("sic_codes") or [],
                    "phone": (org.get("primary_phone") or {}).get("number"),
                    "linkedin": org.get("linkedin_url"),
                    "city": org.get("city"), "country": org.get("country"),
                    "founded": org.get("founded_year"),
                }
        save_cache("firmographics", cache)
        print(f"  {min(i + 10, len(todo))}/{len(todo)}")
    return cache


# --- Stufe 5: Kontakte -------------------------------------------------------
def stage_contacts(domains: dict, max_per_account: int = 3) -> dict:
    """Domain -> bis zu N Kontakte je Persona. Suche + Match kosten Credits."""
    cache = load_cache("contacts")
    doms = sorted({d["domain"] for d in domains.values() if d.get("domain")})
    todo = [d for d in doms if d not in cache]
    print(f"Kontakte: {len(todo)} Accounts offen")

    for n, dom in enumerate(todo, 1):
        found: list[dict] = []
        for persona, titles in PERSONA_TITLES:
            if len(found) >= max_per_account:
                break
            data = call("/mixed_people/search", {
                "q_organization_domains_list": [dom],
                "person_titles": titles,
                "per_page": 10,
            })
            for p in (data.get("people") or []):
                if len(found) >= max_per_account:
                    break
                if any(f["id"] == p.get("id") for f in found):
                    continue
                found.append({"id": p.get("id"), "persona": persona,
                              "title": p.get("title"),
                              "first_name": p.get("first_name")})

        # E-Mails in einem Rutsch nachziehen
        if found:
            m = call("/people/bulk_match",
                     {"details": [{"id": f["id"]} for f in found]})
            by_id = {p.get("id"): p for p in (m.get("matches") or [])}
            for f in found:
                p = by_id.get(f["id"]) or {}
                f.update({
                    "name": p.get("name"), "email": p.get("email"),
                    "email_status": p.get("email_status"),
                    "catchall": p.get("email_domain_catchall"),
                    "linkedin_url": p.get("linkedin_url"),
                    "city": p.get("city"),
                })
        cache[dom] = found
        if n % 10 == 0:
            save_cache("contacts", cache)
            print(f"  {n}/{len(todo)}")
    save_cache("contacts", cache)
    return cache


# --- Export ------------------------------------------------------------------
def export(domains: dict, firmo: dict, contacts: dict, rows: list[dict]) -> None:
    by_id = {r["company_id"]: r for r in rows}

    acc = []
    for cid, d in domains.items():
        row = by_id.get(cid, {})
        f = firmo.get(d.get("domain") or "", {})
        acc.append({
            "company_id": cid, "legal_name": row.get("legal_name", ""),
            "domain": d.get("domain", ""), "domain_confidence": d.get("confidence", 0),
            "domain_stage": d.get("stage", 0), "domain_beleg": d.get("note", ""),
            "employees": f.get("employees", ""), "industry": f.get("industry", ""),
            "naics": ";".join(f.get("naics", [])), "phone_zentrale": f.get("phone", ""),
            "apollo_city": f.get("city", ""), "apollo_country": f.get("country", ""),
            "tier": row.get("tier", ""), "awards_total": row.get("awards_total", ""),
            "proof_url": row.get("proof_url", ""),
        })
    acc.sort(key=lambda r: (-(r["employees"] or 0) if isinstance(r["employees"], int) else 0))
    _write(DATA / "enrichment_accounts_full.csv", acc)

    con = []
    for dom, people in contacts.items():
        for p in people:
            con.append({
                "account_domain": dom, "name": p.get("name", ""),
                "rolle": p.get("title", ""), "persona": p.get("persona", ""),
                "linkedin_url": p.get("linkedin_url", ""),
                "email": p.get("email", ""),
                "email_status": p.get("email_status", ""),
                "catchall": p.get("catchall", ""), "ort": p.get("city", ""),
            })
    _write(DATA / "enrichment_kontakte_full.csv", con)
    print(f"\nExport: {len(acc)} Accounts, {len(con)} Kontakte")


def _write(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path}: {len(rows)} Zeilen")


def dry_run(rows: list[dict]) -> None:
    d = load_cache("domains")
    resolved = sum(1 for v in d.values() if v.get("domain"))
    print("Trockenlauf - nichts wird abgerufen\n")
    print(f"  Firmen in der Longlist:        {len(rows)}")
    print(f"  Domains bereits im Cache:      {len(d)} (davon aufgeloest: {resolved})")
    print(f"  Domain-Lookups offen:          {len(rows) - len(d)}   -> 0 Credits")
    print(f"  Firmographics offen:           ~{resolved}   -> bis zu {resolved} Credits")
    print(f"  Kontaktsuchen (3 Personas):    ~{resolved * 3}   -> bis zu {resolved * 3} Credits")
    print(f"  Kontakt-Matches (3 je Account):~{resolved * 3}   -> bis zu {resolved * 3} Credits")
    print(f"\n  Grobe Obergrenze gesamt:       ~{resolved * 7} Credits")
    print("  Tatsaechlich weniger, weil nicht jede Suche ein Ergebnis liefert.")


def main() -> int:
    ap = argparse.ArgumentParser(prog="apollo-enrich")
    ap.add_argument("--stage", choices=["domains", "firmographics", "contacts", "export", "all"],
                    default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-per-account", type=int, default=3)
    ap.add_argument("--no-impressum", action="store_true",
                    help="Stufe 3 ueberspringen (schneller, ungenauer)")
    a = ap.parse_args()

    rows = read_longlist()
    if a.dry_run:
        dry_run(rows)
        return 0

    domains = load_cache("domains")
    if a.stage in ("domains", "all"):
        domains = stage_domains(rows, check_impressum=not a.no_impressum)

    firmo = load_cache("firmographics")
    if a.stage in ("firmographics", "all"):
        firmo = stage_firmographics(domains)

    contacts = load_cache("contacts")
    if a.stage in ("contacts", "all"):
        contacts = stage_contacts(domains, a.max_per_account)

    export(domains, firmo, contacts, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
