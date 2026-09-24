"""Abgabepaket bauen: die vier Dateien, die der Case verlangt.

    data/enrichment_markt.csv     Aufgabe 1d - Top 40 Accounts mit Kontakt
    data/enrichment_signale.csv   Aufgabe 2d - Top 20 mit why_now und E-Mail
    data/validation_sample.csv    eigenes Stichproben-Audit

Eingang sind die Clay-Exporte (Personen + E-Mail), Referenz sind die beiden
Longlists aus der Pipeline. Gejoint wird ueber den normalisierten Firmennamen.

=== WARUM DER E-MAIL-STATUS EINE EIGENE SPALTE MIT EIGENER QUELLE HAT ===
Der Case verlangt je Kontakt einen E-Mail-Status (verifiziert / catch-all /
geraten) MIT Quelle. Der Clay-Export liefert die Adresse, aber keinen Status.
Ihn einfach als "verifiziert" zu fuehren, waere eine Erfindung.

Deshalb drei Belegstufen, jede mit ausgewiesener Herkunft:

  verifiziert_apollo    Apollo hat die Adresse bestaetigt (Lauf 23.09.2026)
  mx_ok                 Die Domain nimmt Mail an (MX-Record vorhanden).
                        Das belegt die DOMAIN, nicht das Postfach.
  kein_mx               Die Domain hat keinen MX-Record - Adresse unbrauchbar.
  ungeprueft            Weder Apollo-Status noch MX-Abfrage moeglich.

Ein MX-Record ist kein Ersatz fuer eine Adressverifikation. Er schliesst
aber den haeufigsten Totalausfall aus (getippte oder tote Domain) und kostet
nichts. Was er nicht kann, steht in der Spaltenbeschreibung - nicht im
Kleingedruckten.

=== ZWEI PRUEFUNGEN, DIE DER EXPORT NICHT MITBRINGT ===
1. E-Mail-Domain gegen Firmendomain. Gemessen: 5 von 48 weichen ab
   (acp.de vs. acp-gruppe.com, materna.group vs. materna.de). Meist die
   Konzern- statt der Auftrittsdomain, also kein Fehler - aber pruefen.
2. Textqualitaet der generierten Mails. 10 von 48 enthalten Floskeln wie
   "Ich konnte online wenig zu ... finden" oder "nehme aber an". Das ist
   das Eingestaendnis fehlender Recherche im Fliesstext. Diese Zeilen
   duerfen nicht ungeprueft raus.
"""
from __future__ import annotations

import csv
import random
import re
from pathlib import Path

from src.resolve.normalize import normalize_company

DATA = Path("data")
ADDR = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)

TOP_MARKT = 40
TOP_SIGNALE = 20

# Formulierungen, mit denen ein Textgenerator zugibt, nichts gefunden zu
# haben. Im Outbound ist das schlimmer als gar keine Personalisierung.
COPY_FLAGS = (
    "konnte online wenig", "konnte keine", "konnte nichts", "nehme aber an",
    "nehme an", "vermutlich", "ich hoffe", "falls ich richtig",
)


def _mx_ok(domain: str, cache: dict) -> bool | None:
    """Nimmt die Domain ueberhaupt Mail an? None = nicht pruefbar."""
    if not domain:
        return None
    if domain in cache:
        return cache[domain]
    try:
        import dns.resolver
        dns.resolver.resolve(domain, "MX", lifetime=8)
        cache[domain] = True
    except ImportError:
        cache[domain] = None
    except Exception:                                   # noqa: BLE001
        cache[domain] = False
    return cache[domain]


def _email_status(email: str, apollo: dict, cache: dict) -> tuple[str, str]:
    """(status, quelle) - nie geraten, immer mit Herkunft."""
    e = (email or "").strip().lower()
    if not e or not ADDR.match(e):
        return "keine_adresse", ""
    if e in apollo:
        return f"verifiziert_apollo", "apollo_people_bulk_match 23.09.2026"
    mx = _mx_ok(e.split("@")[-1], cache)
    if mx is True:
        return "mx_ok", "DNS-MX-Abfrage (belegt die Domain, nicht das Postfach)"
    if mx is False:
        return "kein_mx", "DNS-MX-Abfrage: kein Eintrag"
    return "ungeprueft", ""


def _copy_warning(row: dict) -> str:
    txt = " ".join((row.get(c) or "") for c in ("Email_1", "Email_2", "Email_3")).lower()
    hits = [f for f in COPY_FLAGS if f in txt]
    return ("Textbaustein gibt fehlende Recherche zu: "
            + ", ".join(sorted(set(hits)))) if hits else ""


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _index(rows: list[dict], key: str = "company_id") -> dict[str, dict]:
    return {r[key]: r for r in rows}


def _write(path: Path, rows: list[dict]) -> Path:
    if not rows:
        raise SystemExit(f"{path}: keine Zeilen")
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    return path


# --- Aufgabe 1d ---------------------------------------------------------------
def build_markt(clay: list[dict], longlist: dict, apollo: dict,
                cache: dict) -> list[dict]:
    """Top 40 Accounts aus longlist_markt, angereichert um Kontakt und Mail."""
    out = []
    for row in clay:
        cid = normalize_company(row.get("Company Name", ""))
        ref = longlist.get(cid)
        status, quelle = _email_status(row.get("Work Email"), apollo, cache)
        email_dom = (row.get("Work Email") or "").split("@")[-1].lower()
        comp_dom = (row.get("Company Domain") or "").lower().replace("www.", "")
        out.append({
            "company_id": cid,
            "firma": row.get("Company Name", ""),
            "domain": comp_dom,
            "tier": (ref or {}).get("tier", ""),
            "tier_status": (ref or {}).get("tier_status", ""),
            "proof_type": (ref or {}).get("proof_type", ""),
            "proof_url": (ref or {}).get("proof_url", ""),
            "proof_date": (ref or {}).get("proof_date", ""),
            "verfahren_12m": (ref or {}).get("participations_total", ""),
            "auftraggeber_12m": (ref or {}).get("buyers_total", ""),
            "in_longlist": "ja" if ref else "NEIN - nicht zuordenbar",
            "name": row.get("Full Name", ""),
            "jobtitel": row.get("Job Title", ""),
            "persona": _persona(row.get("Job Title", "")),
            "ort": row.get("Location", ""),
            "linkedin": row.get("LinkedIn Profile", ""),
            "email": row.get("Work Email", ""),
            "email_status": status,
            "email_quelle": quelle,
            "email_domain_abgleich": ("ok" if email_dom == comp_dom
                                      else f"PRUEFEN: {email_dom} vs {comp_dom}"),
            "telefon": row.get("Mobile Phone", ""),
            "telefon_typ": "mobil" if (row.get("Mobile Phone") or "").strip() else "",
            "telefon_quelle": "clay_export" if (row.get("Mobile Phone") or "").strip() else "",
            "copy_warnung": _copy_warning(row),
        })

    # Nach Tier und Verfahrenszahl sortieren, dann auf TOP_MARKT Accounts
    # kuerzen - nicht auf 40 KONTAKTE. Der Case fragt nach Accounts.
    order = {"A": 0, "B": 1, "C": 2, "D": 3, "": 9}
    out.sort(key=lambda r: (order.get(r["tier"], 9),
                            -int(r["verfahren_12m"] or 0), r["firma"]))
    keep, seen = [], []
    for r in out:
        if r["company_id"] not in seen:
            if len(seen) >= TOP_MARKT:
                continue
            seen.append(r["company_id"])
        keep.append(r)
    return keep


def _persona(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in ("bid", "tender", "angebot", "ausschreibung", "submission",
                            "proposal", "vergabemanage")):
        return "Champion - Bid/Tender"
    if any(k in t for k in ("geschäftsführ", "geschaeftsfuehr", "managing director",
                            "inhaber", "vorstand", "prokurist", "kaufmännisch",
                            "head of sales", "vertriebsleit", "niederlassungsleit")):
        return "Economic Buyer"
    return "Nutzer / Fuersprecher"


# --- Aufgabe 2d ---------------------------------------------------------------
def build_signale(clay: list[dict], signale: dict, apollo: dict,
                  cache: dict) -> list[dict]:
    """Top 20 Signal-Accounts mit why_now, Beleg und Kontakt."""
    out = []
    for row in clay:
        cid = normalize_company(row.get("Company Name", ""))
        ref = signale.get(cid)
        status, quelle = _email_status(row.get("Work Email"), apollo, cache)
        email_dom = (row.get("Work Email") or "").split("@")[-1].lower()
        comp_dom = (row.get("Company Domain") or "").lower().replace("www.", "")
        out.append({
            "company_id": cid,
            "firma": row.get("Company Name", ""),
            "domain": comp_dom,
            "tier": (ref or {}).get("tier", ""),
            "score": (ref or {}).get("score", ""),
            "signal_type": (ref or {}).get("signal_type", row.get("Signal Type", "")),
            "signal_datum": (ref or {}).get("signal_datum", row.get("Signal Datum", "")),
            # why_now kommt aus der Pipeline, nicht aus dem Export - die
            # Pipeline-Fassung ist die belegte.
            "why_now": (ref or {}).get("why_now", row.get("Why Now", "")),
            "quell_url": (ref or {}).get("quell_url", row.get("Quell Url", "")),
            "match_confidence": (ref or {}).get("match_confidence", ""),
            "in_longlist_signale": "ja" if ref else "NEIN - nicht zuordenbar",
            "name": row.get("Full Name", ""),
            "jobtitel": row.get("Job Title", ""),
            "persona": _persona(row.get("Job Title", "")),
            "ort": row.get("Location", ""),
            "linkedin": row.get("LinkedIn Profile", ""),
            "email": row.get("Work Email", ""),
            "email_status": status,
            "email_quelle": quelle,
            "email_domain_abgleich": ("ok" if email_dom == comp_dom
                                      else f"PRUEFEN: {email_dom} vs {comp_dom}"),
            "telefon": row.get("Mobile Phone", ""),
            "telefon_typ": "mobil" if (row.get("Mobile Phone") or "").strip() else "",
            "telefon_quelle": "clay_export" if (row.get("Mobile Phone") or "").strip() else "",
            "copy_warnung": _copy_warning(row),
        })
    out.sort(key=lambda r: -int(r["score"] or 0))
    keep, seen = [], []
    for r in out:
        if r["company_id"] not in seen:
            if len(seen) >= TOP_SIGNALE:
                continue
            seen.append(r["company_id"])
        keep.append(r)
    return keep


# --- Stichproben-Audit --------------------------------------------------------
def build_validation(markt: list[dict], signale: list[dict],
                     n: int = 30, seed: int = 42) -> list[dict]:
    """Zufallsstichprobe ueber beide Listen, mit Pruefergebnis je Feld.

    Der Case laesst eine Stichprobenpruefung ankuendigen. Wer sie selbst
    macht und das Ergebnis mitliefert, nimmt ihr die Schaerfe - und findet
    die eigenen Fehler zuerst.
    """
    from src.verify_proofs import check

    pool = ([{**r, "_liste": "markt"} for r in markt]
            + [{**r, "_liste": "signale"} for r in signale])
    random.seed(seed)
    sample = random.sample(pool, min(n, len(pool)))

    rows = []
    for r in sample:
        url = r.get("proof_url") or r.get("quell_url") or ""
        res = check(url) if url else {"ok": False, "reason": "keine URL",
                                      "status": 0}
        befunde = []
        if not res["ok"] and not res.get("unverifiable"):
            befunde.append(f"Beleg: {res['reason']}")
        if res.get("unverifiable"):
            befunde.append("Beleg maschinell nicht pruefbar (JS-Challenge)")
        if r.get("in_longlist", "ja").startswith("NEIN") or \
           r.get("in_longlist_signale", "ja").startswith("NEIN"):
            befunde.append("Firma nicht in der Longlist zuordenbar")
        if r["email_status"] in ("kein_mx", "keine_adresse"):
            befunde.append(f"E-Mail: {r['email_status']}")
        if r["email_domain_abgleich"] != "ok":
            befunde.append(r["email_domain_abgleich"])
        if r["copy_warnung"]:
            befunde.append("Textqualitaet")

        rows.append({
            "liste": r["_liste"],
            "firma": r["firma"],
            "name": r["name"],
            "geprueft_beleg_url": url,
            "beleg_http": res.get("status", ""),
            "beleg_typ": res.get("type", ""),
            "beleg_ok": "ja" if res["ok"] else ("n/a" if res.get("unverifiable") else "nein"),
            "email": r["email"],
            "email_status": r["email_status"],
            "email_domain_abgleich": r["email_domain_abgleich"],
            "copy_warnung": r["copy_warnung"],
            "befunde": "; ".join(befunde) or "keine",
            "urteil": "ok" if not befunde else "pruefen",
        })
    return rows


def main() -> int:
    clay_m = _read(Path("data/clay_markt_export.csv"))
    clay_s = _read(Path("data/clay_signale_export.csv"))
    longlist = _index(_read(DATA / "longlist_markt.csv"))
    signale = _index(_read(DATA / "longlist_signale.csv"))

    apollo = {}
    ap_path = DATA / "enrichment_kontakte_tierA.csv"
    if ap_path.exists():
        apollo = {r["email"].lower(): r for r in _read(ap_path)
                  if r.get("email") and r.get("email_status") == "verifiziert"}

    cache: dict = {}
    m = build_markt(clay_m, longlist, apollo, cache)
    s = build_signale(clay_s, signale, apollo, cache)
    v = build_validation(m, s)

    _write(DATA / "enrichment_markt.csv", m)
    _write(DATA / "enrichment_signale.csv", s)
    _write(DATA / "validation_sample.csv", v)

    import collections
    print(f"enrichment_markt.csv    {len(m):>3} Kontakte an "
          f"{len({r['company_id'] for r in m})} Accounts")
    print(f"  E-Mail-Status: {dict(collections.Counter(r['email_status'] for r in m))}")
    print(f"  Telefon: {sum(1 for r in m if r['telefon'])}/{len(m)}")
    print(f"  Copy-Warnungen: {sum(1 for r in m if r['copy_warnung'])}")
    print(f"enrichment_signale.csv  {len(s):>3} Kontakte an "
          f"{len({r['company_id'] for r in s})} Accounts")
    print(f"  E-Mail-Status: {dict(collections.Counter(r['email_status'] for r in s))}")
    print(f"  Telefon: {sum(1 for r in s if r['telefon'])}/{len(s)}")
    print(f"validation_sample.csv   {len(v):>3} Zeilen, "
          f"{sum(1 for r in v if r['urteil'] == 'ok')} ohne Befund")

    # Verwaiste Zeilen laut melden.
    #
    # Der Clay-Export ist ein STANDBILD: Er wurde gezogen, bevor SThree und
    # die anderen Personaldienstleister auf die Ausschlussliste kamen. Die
    # Longlist kennt sie seitdem nicht mehr, der Export schon.
    #
    # Solche Zeilen werden nicht stillschweigend geloescht - dann waere nicht
    # nachvollziehbar, dass es sie gab - sondern mit
    # in_longlist = "NEIN - nicht zuordenbar" mitgefuehrt. Ohne diese Meldung
    # sieht man das aber nur, wenn die Stichprobe zufaellig darauf faellt.
    verwaist = ([r for r in m if r["in_longlist"].startswith("NEIN")]
                + [r for r in s if r["in_longlist_signale"].startswith("NEIN")])
    if verwaist:
        print(f"  ! {len(verwaist)} Kontakt(e) ohne Longlist-Bezug - "
              f"nicht ansprechen:")
        for r in verwaist:
            print(f"      {r['firma']} ({r['email'] or 'ohne Mail'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
