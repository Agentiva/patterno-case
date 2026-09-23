"""Firmographics aus Apollo in die Longlist mergen und neu tiern.

=== DIE FALLE, DIE HIER ABGEFANGEN WIRD ===
Apollo loest eine Domain auf den KONZERN auf, die Vergabe geht aber an den
RECHTSTRAEGER. Zwei Beispiele aus dem Lauf vom 23.09.2026:

  Zuschlag an: "Computacenter AG & Co OHG"  (Deutschland, Kerpen)
  Apollo:      computacenter.com -> Hatfield, UK, 21.000 MA
               = die britische Konzernmutter

  Zuschlag an: "Bechtle GmbH & Co. KG"      (regionales Systemhaus)
  Apollo:      bechtle.com -> Neckarsulm, 17.000 MA
               = die Bechtle AG, also der Konzern

Fuer unser Tiering ist das falsch: Der ICP zielt auf 50-2.000 Mitarbeitende,
und der bietende Rechtstraeger hat oft einen Bruchteil der Konzerngroesse.
Wer den Konzernwert uebernimmt, stuft systematisch falsch ein und schreibt
den Konzernvertrieb an statt die Niederlassung, die tatsaechlich bietet.

Deshalb: headcount_scope wird explizit gefuehrt und im Zweifel als unklar
markiert, statt eine Zahl als Wahrheit auszugeben.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.resolve.normalize import normalize_company

DATA = Path("data")

# Oberkante des ICP. Wer darueber liegt, ist entweder wirklich ein Konzern
# oder Apollo hat auf die Mutter aufgeloest - beides muss geprueft werden.
ICP_MAX_EMPLOYEES = 2000


def classify_headcount(award_name: str, apollo: dict) -> dict:
    """Ist die Mitarbeiterzahl die des Bieters oder die des Konzerns?"""
    apollo_name = apollo.get("name") or ""
    country = (apollo.get("country") or "").strip()
    emp = apollo.get("employees")

    flags = []
    if country and country.lower() not in ("germany", "deutschland"):
        flags.append(f"Apollo-Sitz {country}, Zuschlag ging an deutschen Rechtstraeger")
    if isinstance(emp, int) and emp > ICP_MAX_EMPLOYEES:
        flags.append(f"{emp} MA liegt ueber der ICP-Oberkante {ICP_MAX_EMPLOYEES}")
    if normalize_company(apollo_name) != normalize_company(award_name):
        flags.append(f"Name weicht ab: Apollo '{apollo_name}' vs. Zuschlag '{award_name}'")

    if not flags:
        return {"scope": "rechtstraeger", "note": "", "usable_for_tier": True}
    return {
        "scope": "konzern_oder_unklar",
        "note": " | ".join(flags),
        # Bewusst NICHT fuers Tiering verwenden. Lieber "unbekannt" als falsch.
        "usable_for_tier": False,
    }


def merge(enriched_path: Path, longlist_path: Path | None = None) -> Path:
    longlist_path = longlist_path or (DATA / "longlist_markt.csv")
    records = json.loads(Path(enriched_path).read_text(encoding="utf-8"))
    by_norm = {normalize_company(r["name"]): r for r in records}
    by_domain = {r["domain"]: r for r in records if r.get("domain")}

    with longlist_path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys()) if rows else []

    new_cols = ["domain", "domain_source", "employees", "employees_scope",
                "employees_note", "apollo_industry", "apollo_phone",
                "apollo_linkedin", "apollo_city"]
    for c in new_cols:
        if c not in fields:
            fields.append(c)

    hits = 0
    for row in rows:
        rec = by_domain.get(row.get("domain") or "") or by_norm.get(row["company_id"])
        if not rec:
            continue
        hits += 1
        verdict = classify_headcount(row["legal_name"], rec)
        row["domain"] = rec.get("domain") or row.get("domain", "")
        row["domain_source"] = "apollo_lookup"
        row["employees"] = rec.get("employees") if verdict["usable_for_tier"] else ""
        row["employees_scope"] = verdict["scope"]
        row["employees_note"] = verdict["note"]
        row["apollo_industry"] = rec.get("industry") or ""
        row["apollo_phone"] = rec.get("phone") or ""
        row["apollo_linkedin"] = rec.get("linkedin") or ""
        row["apollo_city"] = rec.get("city") or ""

    for row in rows:
        for c in new_cols:
            row.setdefault(c, "")

    with longlist_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    return longlist_path, hits, len(records)
