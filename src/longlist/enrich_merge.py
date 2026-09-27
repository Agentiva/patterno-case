"""Angereicherte Domains und Mitarbeiterzahlen zurueck in die Longlist.

=== WAS DIESES MODUL TUT UND WAS NICHT ===
Es fuellt Domain, Mitarbeiterzahl, Branche und LinkedIn - alles, was die
ANSPRACHE braucht.

Es entscheidet NICHT ueber das Tier. Das haengt ausschliesslich an
Vergabedaten (siehe src/longlist/build.py, tier_for). Der Grund steht dort
ausfuehrlich; kurz: Die Mitarbeiterzahl fehlte bei allen 2.458 Zeilen und
war dort, wo sie vorlag, bei 5 von 10 Firmen die des Konzerns statt die des
bietenden Rechtstraegers.

    longlist --live   ->  Tiers stehen fest (Vergabedaten)
    (Clay / Apollo)   ->  Domain + Mitarbeiterzahl
    retier            ->  Anreicherung einspielen

Das Tier wird hier trotzdem neu gerechnet, aber aus einem anderen Grund:
Ein Kriterium wandert mit der Zeit - die Aktualitaet des Belegs wird jeden
Tag schlechter. Deshalb laeuft `retier` auch ohne --from sinnvoll.

=== DIE FALLE, DIE HIER ABGEFANGEN WIRD ===
Apollo loest eine Domain auf den KONZERN auf, die Vergabe ging aber an den
RECHTSTRAEGER. Zwei Beispiele aus dem Lauf vom 23.09.2026:

  Zuschlag an: "Computacenter AG & Co OHG"  (Kerpen)
  Apollo:      computacenter.com -> Hatfield/UK, 21.000 MA
               = die britische Konzernmutter

  Zuschlag an: "Bechtle GmbH & Co. KG"      (regionales Systemhaus)
  Apollo:      bechtle.com -> Neckarsulm, 17.000 MA
               = die Bechtle AG, also der Konzern

Das Tier beruehrt das nicht mehr. Fuer die ANSPRACHE ist es trotzdem
entscheidend: Wer 17.000 als Groesse des regionalen Systemhauses liest,
schreibt den Konzernvertrieb an statt die Niederlassung, die geboten hat.

Deshalb wird `employees_scope` explizit gefuehrt. Ein Konzernwert landet
nicht in `employees`, sondern in `employees_note` - sichtbar, aber nicht
als Eigenschaft des Bieters ausgegeben.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from src.longlist.build import _age_days, tier_for
from src.resolve.normalize import normalize_company

DATA = Path("data")

# Oberkante des ICP. Wer darueber liegt, ist entweder wirklich ein Konzern
# oder Apollo hat auf die Mutter aufgeloest - beides muss geprueft werden.
ICP_MAX_EMPLOYEES = 2000

# Spaltennamen, unter denen die Anreicherung zurueckkommen darf. Clay laesst
# den Nutzer frei benennen, Apollo liefert eigene - statt einem starren
# Schema also eine Liste von Synonymen je Feld.
FIELD_ALIASES = {
    "company_id": ("company_id", "companyid"),
    "legal_name": ("legal_name", "name", "company", "company_name", "firma"),
    "domain": ("domain", "company_domain", "website", "url", "domain_final"),
    "employees": ("employees", "employee_count", "mitarbeiter",
                  "mitarbeiterzahl", "headcount", "estimated_num_employees",
                  "num_employees", "size"),
    "country": ("country", "land", "hq_country"),
    "city": ("city", "ort", "hq_city"),
    "apollo_name": ("apollo_name", "matched_name", "enriched_name"),
    "industry": ("industry", "branche", "apollo_industry"),
    "linkedin": ("linkedin", "linkedin_url", "apollo_linkedin"),
    "domain_source": ("domain_source", "quelle", "source"),
    "domain_confidence": ("domain_confidence", "confidence", "domain_konfidenz"),
}

# Rang der Domainquellen. Eine spaetere Anreicherung darf eine BESSERE
# Quelle nicht ueberschreiben.
#
# Der Fall, der das noetig macht: Die amtliche Domain kommt aus
# contactPoint des Bieters in der Bekanntmachung - das Unternehmen hat sie
# der Vergabestelle selbst gemeldet. Apollo und Clay loesen dagegen
# regelmaessig auf die Konzernmutter auf (Computacenter AG & Co OHG in
# Kerpen -> computacenter.com in Hatfield/UK). Wer erst `domains_amtlich`
# und danach den Clay-Export einspielt, hat ohne diese Regel die schlechtere
# Zahl in der Spalte - und merkt es nicht, weil die Spalte gefuellt bleibt.
SOURCE_RANK = {
    "amtlich_bestaetigt": 0.95,     # url und Mail der Bekanntmachung stimmen ueberein
    "amtlich_namensbezug": 0.90,    # eine amtliche Quelle, Domainstamm passt zum Namen
    "amtlich_unbestaetigt": 0.60,
    "enrichment": 0.70,             # Clay/Apollo ohne eigene Konfidenzangabe
}
DEFAULT_RANK = 0.70


def _rank(source: str | None, confidence=None) -> float:
    """Guete einer Domainangabe. Eine mitgelieferte Konfidenz gewinnt."""
    try:
        if confidence not in (None, ""):
            return float(confidence)
    except (TypeError, ValueError):
        pass
    return SOURCE_RANK.get((source or "").strip(), DEFAULT_RANK)


def _norm_key(k: str) -> str:
    return (k or "").strip().lower().replace(" ", "_").replace("-", "_")


def _pick(row: dict, field: str):
    """Ersten belegten Alias eines Feldes zurueckgeben."""
    lookup = {_norm_key(k): v for k, v in row.items()}
    for alias in FIELD_ALIASES[field]:
        v = lookup.get(alias)
        if v not in (None, ""):
            return v
    return None


def _to_int(value) -> int | None:
    """'1.234', '1,234', '250-500', 1234.0 -> int oder None.

    Clay und Tabellenprogramme formatieren Zahlen gern mit Tausendertrenner;
    ungefiltert wird aus '1.234' eine 1 oder ein Fehler.
    """
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().replace(" ", "")
    # "10.000+" ist ein Groessenband nach oben. Als None waere die Firma
    # "unbekannt gross" und liefe ins Tiering, als Zahl faellt sie korrekt
    # durch die ICP-Oberkante.
    s = s.rstrip("+").strip()
    if "-" in s:                      # Groessenband "250-500" -> Mitte
        parts = [p for p in s.split("-") if p.strip().replace(".", "").replace(",", "").isdigit()]
        if len(parts) == 2:
            lo, hi = (_to_int(parts[0]) or 0), (_to_int(parts[1]) or 0)
            return (lo + hi) // 2 or None
    s = s.replace(".", "").replace(",", "").replace(" ", "")
    return int(s) if s.isdigit() else None


def _clean_domain(value) -> str:
    d = str(value or "").strip().lower()
    for prefix in ("https://", "http://", "www."):
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d.split("/")[0].strip()


def classify_headcount(award_name: str, rec: dict) -> dict:
    """Ist die Mitarbeiterzahl die des Bieters oder die des Konzerns?"""
    apollo_name = rec.get("apollo_name") or rec.get("legal_name") or ""
    country = (rec.get("country") or "").strip()
    emp = rec.get("employees")

    flags = []
    if country and country.lower() not in ("germany", "deutschland", "de"):
        flags.append(f"Sitz {country}, Zuschlag ging an deutschen Rechtstraeger")
    if isinstance(emp, int) and emp > ICP_MAX_EMPLOYEES:
        flags.append(f"{emp} MA liegt ueber der ICP-Oberkante {ICP_MAX_EMPLOYEES}")
    if apollo_name and normalize_company(apollo_name) != normalize_company(award_name):
        flags.append(f"Name weicht ab: '{apollo_name}' vs. Zuschlag '{award_name}'")

    if not flags:
        return {"scope": "rechtstraeger", "note": "", "usable_for_tier": True}
    return {
        "scope": "konzern_oder_unklar",
        "note": " | ".join(flags),
        # Bewusst NICHT fuers Tiering verwenden. Lieber "unbekannt" als falsch.
        "usable_for_tier": False,
    }


def load_enrichment(path: Path) -> list[dict]:
    """Angereicherte Daten aus CSV (Clay-Export) oder JSON (Apollo) lesen."""
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        raw = json.loads(text)
        rows = raw if isinstance(raw, list) else raw.get("records") or []
    else:
        rows = list(csv.DictReader(text.splitlines()))

    out = []
    for r in rows:
        out.append({
            "company_id": _pick(r, "company_id"),
            "legal_name": _pick(r, "legal_name"),
            "domain": _clean_domain(_pick(r, "domain")),
            "employees": _to_int(_pick(r, "employees")),
            "country": _pick(r, "country"),
            "city": _pick(r, "city"),
            "apollo_name": _pick(r, "apollo_name"),
            "industry": _pick(r, "industry"),
            "linkedin": _pick(r, "linkedin"),
            "domain_source": _pick(r, "domain_source"),
        })
    return out


def merge(enriched_path: Path | None = None,
          longlist_path: Path | None = None) -> dict:
    """Anreicherung einspielen und die Tiers nachziehen.

    Ohne enriched_path werden nur die Tiers neu gerechnet - sinnvoll, weil
    die Aktualitaet des Belegs mit jedem Tag altert.
    """
    longlist_path = Path(longlist_path or (DATA / "longlist_markt.csv"))
    records = load_enrichment(Path(enriched_path)) if enriched_path else []

    # Drei Schluessel, absteigend nach Verlaesslichkeit. company_id ist der
    # Schluessel, den wir selbst vergeben haben - kommt er zurueck, ist die
    # Zuordnung eindeutig. Name und Domain sind Rueckfallebenen fuer den
    # Fall, dass Clay die Spalte nicht mitfuehrt.
    by_id = {r["company_id"]: r for r in records if r.get("company_id")}
    by_name = {normalize_company(r["legal_name"]): r
               for r in records if r.get("legal_name")}
    by_domain = {r["domain"]: r for r in records if r.get("domain")}

    with longlist_path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{longlist_path} ist leer")

    fields = list(rows[0].keys())
    for c in ("employees_scope", "employees_note", "domain_note", "tier_status",
              "apollo_industry", "apollo_linkedin"):
        if c not in fields:
            fields.append(c)

    before = Counter(r.get("tier", "") for r in rows)
    stats = Counter()

    for row in rows:
        row.setdefault("employees_scope", "")
        row.setdefault("employees_note", "")
        row.setdefault("domain_note", "")
        row.setdefault("apollo_industry", "")
        row.setdefault("apollo_linkedin", "")

        rec = (by_id.get(row["company_id"])
               or by_name.get(row["company_id"])
               or by_domain.get(row.get("domain") or ""))
        if rec:
            stats["gematcht"] += 1
            if rec.get("domain"):
                neu = _rank(rec.get("domain_source"), rec.get("domain_confidence"))
                alt = _rank(row.get("domain_source"), row.get("domain_confidence"))
                # Gleiche Domain aus beiden Quellen ist eine Bestaetigung,
                # kein Konflikt. Ohne diese Zeile meldete der Lauf 33
                # "abgewiesene" Domains, von denen 31 mit der vorhandenen
                # identisch waren - eine Warnung, die nichts warnt, wird
                # ueberlesen, und dann auch die zwei echten Faelle.
                gleich = (rec["domain"] or "").strip().lower() == \
                         (row.get("domain") or "").strip().lower()
                if gleich:
                    stats["domain_bestaetigt"] += 1
                elif not row.get("domain") or neu >= alt:
                    row["domain"] = rec["domain"]
                    row["domain_source"] = rec.get("domain_source") or "enrichment"
                    if rec.get("domain_confidence") not in (None, ""):
                        row["domain_confidence"] = rec["domain_confidence"]
                    stats["domain_uebernommen"] += 1
                else:
                    # Nicht stillschweigend verwerfen: Wer den Clay-Export
                    # einspielt, soll sehen, dass die bessere Quelle gewonnen
                    # hat - und welche Domain stattdessen angeboten wurde.
                    stats["domain_bessere_behalten"] += 1
                    # Eigene Spalte, nicht employees_note: Dieser Hinweis
                    # handelt von der Domain, und employees_note wird wenige
                    # Zeilen weiter unten von classify_headcount neu gesetzt -
                    # der Text waere still verschwunden.
                    row["domain_note"] = (
                        f"{rec['domain']} verworfen, {row['domain']} "
                        f"({row.get('domain_source')}) ist besser belegt")
            row["apollo_industry"] = rec.get("industry") or row["apollo_industry"]
            row["apollo_linkedin"] = rec.get("linkedin") or row["apollo_linkedin"]

            verdict = classify_headcount(row["legal_name"], rec)
            row["employees_scope"] = verdict["scope"]
            row["employees_note"] = verdict["note"]
            if rec.get("employees") is not None and verdict["usable_for_tier"]:
                row["employees"] = rec["employees"]
                stats["mitarbeiterzahl_nutzbar"] += 1
            elif rec.get("employees") is not None:
                # Wert bekannt, aber Konzern oder unklar -> Spalte leer
                # lassen, damit das Tiering ihn nicht benutzt. Die Zahl
                # steht in employees_note und geht also nicht verloren.
                row["employees"] = ""
                row["employees_note"] = (
                    f"{verdict['note']} | gemeldeter Wert: {rec['employees']}")
                stats["mitarbeiterzahl_verworfen"] += 1
        else:
            stats["ohne_treffer"] += 1

        # --- Tier neu berechnen, OHNE die Mitarbeiterzahl -------------------
        # Das Tier haengt ausschliesslich an Vergabedaten. Die Anreicherung
        # aendert daran per Definition nichts - sie fuellt Domain und
        # Mitarbeiterzahl fuer die Ansprache.
        # Gerechnet wird trotzdem neu, weil ein Kriterium mit der Zeit
        # wandert: Die Aktualitaet des Belegs wird jeden Tag schlechter.
        # Genau dafuer laeuft `retier` auch ohne --from.
        before_tier = row.get("tier")
        tier, rationale, status = tier_for(
            proof_type=row.get("proof_type", ""),
            participations=_to_int(row.get("participations_total")) or 0,
            proof_age_days=_age_days(row.get("proof_date")),
            # buyers_total, nicht buyers: die Spalte buyers ist auf 5
            # Eintraege gekappt und ergaebe nie mehr als 5.
            buyer_count=(_to_int(row.get("buyers_total"))
                         or len([b for b in (row.get("buyers") or "").split(";") if b])),
            mixed_lot_only=(row.get("mixed_lot_only") == "ja"),
        )
        row["tier"], row["tier_rationale"], row["tier_status"] = tier, rationale, status
        if before_tier and before_tier != tier:
            stats["tier_geaendert_durch_alterung"] += 1

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    rows.sort(key=lambda r: (order.get(r["tier"], 9),
                             -(_to_int(r.get("participations_total")) or 0)))

    with longlist_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL,
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    return {
        "pfad": longlist_path,
        "zeilen": len(rows),
        "angereicherte_saetze": len(records),
        "stats": dict(stats),
        "tier_vorher": dict(sorted(before.items())),
        "tier_nachher": dict(sorted(Counter(r["tier"] for r in rows).items())),
        "mit_domain": sum(1 for r in rows if r.get("domain")),
    }
