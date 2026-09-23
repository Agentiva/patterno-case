"""Stufe 3 der Domain-Resolution: Impressum-Verifikation.

=== WARUM ===
Stufe 1 (Apollo mit Ortsfilter) ist praezise, aber loechrig.
Stufe 2 (ohne Ortsfilter) findet mehr, liefert aber Muell: dedalus.at,
msg-systems.ro, eominnesota.org, domainflotta.hu.

Eine reine Heuristik aus TLD und Namensaehnlichkeit loest das nicht sauber.
Sie lehnte im Test auch korrekte Treffer ab (groth-company.de,
beneering.com), weil ihr der harte Beleg fehlte.

Den gibt es aber: Nach § 5 DDG (frueher § 5 TMG) muss JEDE geschaeftsmaessige
deutsche Website ein Impressum mit Firmierung, Anschrift und in aller Regel
dem Handelsregistereintrag fuehren. Das ist kein Schaetzwert, das ist eine
Rechtspflicht - und damit die belastbarste kostenlose Datenquelle, die wir
fuer diese Frage haben.

Wir holen also das Impressum und pruefen:
  - steht der Firmenname aus der Vergabebekanntmachung drin?
  - steht der Ort aus der Vergabebekanntmachung drin?
  - gibt es einen HRB-Eintrag?

Ein Treffer hier schlaegt jede Heuristik. Kein Treffer heisst nicht
automatisch falsch - manche Seiten sind JS-gerendert oder blockieren
Bots -, deshalb faellt das Ergebnis dann auf die Heuristik zurueck.
"""
from __future__ import annotations

import re
from typing import Iterable

import requests

from src.resolve.normalize import fold, normalize_company

IMPRESSUM_PATHS = ("/impressum", "/de/impressum", "/impressum.html",
                   "/imprint", "/legal-notice", "/kontakt/impressum")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PatternoCaseBot/1.0)"}
TIMEOUT = 12

HRB_RE = re.compile(r"\b(HRB|HRA)\s*[:\-]?\s*(\d{1,7})\b", re.IGNORECASE)


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def fetch_impressum(domain: str) -> tuple[str | None, str]:
    """Gibt (Text, geprueste_URL) zurueck. Text None, wenn nichts erreichbar."""
    for scheme in ("https://", "http://"):
        for path in IMPRESSUM_PATHS:
            url = f"{scheme}{domain}{path}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                                 allow_redirects=True)
            except requests.RequestException:
                continue
            if r.status_code == 200 and len(r.text) > 400:
                return _strip_html(r.text), r.url
        break   # http nur versuchen, wenn https komplett scheitert
    return None, ""


def _core_tokens(name: str) -> list[str]:
    """Aussagekraeftige Namensbestandteile, ohne Rechtsform und Fuellwoerter."""
    stop = {"gmbh", "ag", "kg", "se", "co", "und", "mbh", "ek", "ohg",
            "deutschland", "germany", "group", "gruppe", "holding"}
    return [t for t in normalize_company(name).split()
            if t not in stop and len(t) > 2]


def verify_impressum(domain: str, award_name: str,
                     award_city: str | None = None) -> dict:
    """Harte Verifikation gegen das Impressum."""
    text, url = fetch_impressum(domain)
    if text is None:
        return {"checked": False, "match": False, "confidence_delta": 0.0,
                "url": "", "evidence": "Impressum nicht erreichbar"}

    hay = fold(text)
    tokens = _core_tokens(award_name)
    hits = [t for t in tokens if t in hay]
    name_ratio = len(hits) / len(tokens) if tokens else 0.0

    city_hit = bool(award_city and fold(award_city.split(",")[0].strip()) in hay)
    hrb = HRB_RE.search(text)

    evidence = []
    delta = 0.0
    if name_ratio >= 0.6:
        evidence.append(f"Firmenname im Impressum ({len(hits)}/{len(tokens)} Tokens)")
        delta += 0.45
    elif name_ratio > 0:
        evidence.append(f"Firmenname nur teilweise ({len(hits)}/{len(tokens)})")
        delta += 0.15
    if city_hit:
        evidence.append(f"Ort '{award_city}' im Impressum")
        delta += 0.20
    if hrb:
        evidence.append(f"Handelsregister {hrb.group(1)} {hrb.group(2)}")
        delta += 0.15

    # === WICHTIG: Namensuebereinstimmung ALLEIN reicht nicht ===
    # Bei internationalen Marken steht der Name im Impressum JEDER
    # Landesgesellschaft. Gemessen am 23.09.2026:
    #   msg-systems.ro   -> "msg systems" im Impressum, aber Rumaenien
    #   soprasteria.com  -> "Sopra Steria" im Impressum, aber Konzern
    # Beide haetten als Treffer gegolten. Der ORT aus der Vergabe-
    # bekanntmachung ist der Diskriminator: Er steht nur im Impressum der
    # Gesellschaft, an die der Zuschlag wirklich ging.
    # Ausnahme .de-Domain: dort ist der deutsche Bezug schon durch die TLD
    # belegt, ein fehlender Ort kann an einer abweichenden Zentrale liegen.
    is_de = domain.lower().endswith(".de")
    confirmed = name_ratio >= 0.6 and (city_hit or is_de)
    if name_ratio >= 0.6 and not confirmed:
        evidence.append("ABGELEHNT: Name passt, aber Ort der Vergabe fehlt im "
                        "Impressum und Domain ist nicht .de - vermutlich eine "
                        "andere Landesgesellschaft")
        delta = 0.0

    return {
        "checked": True,
        "match": confirmed,
        "confidence_delta": round(delta, 3),
        "url": url,
        "evidence": "; ".join(evidence) or "keine Uebereinstimmung gefunden",
        "name_ratio": round(name_ratio, 2),
    }


def verify_batch(pairs: Iterable[tuple[str, str, str | None]]) -> list[dict]:
    """pairs: (domain, award_name, award_city)"""
    out = []
    for domain, name, city in pairs:
        res = verify_impressum(domain, name, city)
        res.update({"domain": domain, "award_name": name})
        out.append(res)
    return out
