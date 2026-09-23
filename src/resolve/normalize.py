"""Normalisierung und Entity-Resolution.

Das ist die eigentliche Ingenieursarbeit des Case. Der Fall selbst sagt:
"Die Zuordnung ist oft schwieriger, als sie aussieht. Rechtliche Namen,
Marken, Tochtergesellschaften und Bietergemeinschaften lassen sich nicht
immer eindeutig aufloesen."

Stufe 1 (hier): deterministische Normalisierung + Blocking-Key.
Stufe 2 (hier): Bietergemeinschaften aufsplitten.
Stufe 3 (hier): Ausschlusslisten.
Stufe 4 (extern, siehe docs/waterfalls.md): Domain-Resolution ueber Clay/Apollo,
        Handelsregister, Impressum-Verifikation, LLM-Check.

Alles was unter RESOLUTION_MIN_CONFIDENCE liegt, wird NICHT geraten,
sondern in die review_queue geschrieben.
"""
from __future__ import annotations

import re
import unicodedata

from src.config import EXCLUSION_LISTS, RESOLUTION_MIN_CONFIDENCE

# Rechtsformen, die fuer den Namensvergleich irrelevant sind.
# Reihenfolge: laengste zuerst, sonst frisst "gmbh" das "gmbh & co. kg".
LEGAL_FORMS = [
    "gmbh & co. kgaa", "gmbh & co kgaa", "gmbh & co. kg", "gmbh & co kg",
    "ag & co. kg", "ag & co kg", "se & co. kgaa", "se & co kgaa",
    "gesellschaft mit beschraenkter haftung",
    "kommanditgesellschaft", "aktiengesellschaft",
    "ggmbh", "gmbh", "kgaa", "mbh", "ohg", "kg", "ag", "se", "ug",
    "e.k.", "ek", "e.v.", "ev", "partg", "gbr", "ltd", "plc", "bv", "nv",
]

# Marker fuer Bietergemeinschaften / ARGE.
CONSORTIUM_MARKERS = [
    " arge ", "arbeitsgemeinschaft", "bietergemeinschaft", " bg ",
    " consortium", " konsortium",
]
CONSORTIUM_SPLIT = re.compile(r"\s*(?:\+|/|;|\bund\b|\bu\.\b|&amp;)\s*", re.IGNORECASE)


def fold(text: str) -> str:
    """Umlaute und Diakritika auf ASCII falten. ae/oe/ue/ss explizit,
    weil 'Mueller' und 'Müller' derselbe Betrieb sind."""
    if not text:
        return ""
    t = text.lower().strip()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(src, dst)
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def normalize_company(name: str) -> str:
    """Kanonische Form fuer den Vergleich. NICHT fuer die Anzeige verwenden."""
    t = fold(name)
    t = t.replace("&", " und ")
    t = re.sub(r"[.,\"'`()\[\]]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for form in LEGAL_FORMS:
        f = fold(form).replace("&", " und ")
        f = re.sub(r"[.,]", " ", f)
        f = re.sub(r"\s+", " ", f).strip()
        if t.endswith(" " + f):
            t = t[: -(len(f) + 1)].strip()
    t = re.sub(r"\s*-\s*", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def blocking_key(name: str, plz: str | None = None) -> str:
    """Guenstiger Vorfilter fuers Matching: erste 2 Tokens + PLZ-Praefix.
    Verhindert den O(n^2)-Vergleich ueber die ganze Liste."""
    norm = normalize_company(name)
    head = "-".join(norm.split()[:2])
    region = (str(plz)[:2] if plz else "??")
    return f"{head}|{region}"


def split_consortium(name: str) -> tuple[list[str], bool]:
    """Bietergemeinschaften aufsplitten.

    Ein Zuschlag an eine ARGE nennt mehrere Firmen in EINEM Feld. Wer das
    nicht aufloest, verliert jedes Mitglied oder erzeugt eine Phantomfirma.
    Rueckgabe: (Mitglieder, ist_konsortium)
    """
    low = f" {fold(name)} "
    is_consortium = any(m in low for m in CONSORTIUM_MARKERS)
    if not is_consortium:
        return [name.strip()], False

    cleaned = re.sub(
        r"(?i)\b(arge|arbeitsgemeinschaft|bietergemeinschaft|konsortium|consortium)\b[:\-]?",
        " ", name,
    )
    parts = [p.strip(" -,;") for p in CONSORTIUM_SPLIT.split(cleaned)]
    parts = [p for p in parts if len(p) > 2]
    return (parts or [name.strip()]), True


def check_exclusion(name: str) -> tuple[bool, str | None]:
    """Gegen die Ausschlusslisten pruefen. Rueckgabe: (ausgeschlossen, Grund)."""
    norm = normalize_company(name)
    for reason, entries in EXCLUSION_LISTS.items():
        for entry in entries:
            if normalize_company(entry) in norm:
                return True, reason
    return False, None


def name_similarity(a: str, b: str) -> float:
    """Token-Jaccard auf den normalisierten Namen. Bewusst simpel und
    erklaerbar: im Review muss nachvollziehbar sein, warum zwei Namen
    als gleich galten."""
    ta, tb = set(normalize_company(a).split()), set(normalize_company(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# Vertrauen in die QUELLE, unabhaengig von den Einzelfeldern.
# Ein Gewinnername aus einer amtlichen Zuschlagsbekanntmachung ist ein Faktum,
# kein Schaetzwert - auch dann, wenn die Bekanntmachung keinen Ort mitliefert.
# Ohne diesen Prior bestraft das Modell eine Quelle dafuer, dass sie ein Feld
# nicht fuehrt, und alle 516 TED-Treffer landen faelschlich in der
# Review-Queue (am 23.09.2026 genau so passiert).
SOURCE_PRIOR = {
    "vergabe_dovs": 0.75,   # amtlich, eForms/OCDS, mit Adressblock
    "ted": 0.72,            # amtlich, aber ohne Gewinnerort
    "ba_jobs": 0.50,        # Arbeitgeber-Freitext, kein Register, kein Bezug
}
DEFAULT_PRIOR = 0.50


def resolution_confidence(
    name_sim: float,
    place_match: bool,
    has_register_id: bool = False,
    impressum_verified: bool = False,
    source: str | None = None,
) -> float:
    """Transparenter, additiver Score statt Blackbox.

    Basis ist das Quellenvertrauen, darauf kommen die verifizierbaren
    Einzelmerkmale. Jede Komponente ist im Export sichtbar, damit eine
    Stichprobenpruefung nachvollziehen kann, woher die Zahl stammt.
    """
    base = SOURCE_PRIOR.get(source or "", DEFAULT_PRIOR)
    score = base * min(name_sim, 1.0)
    if place_match:
        score += 0.10
    if has_register_id:
        score += 0.15          # HRB/Registergericht ist der haerteste Beleg
    if impressum_verified:
        score += 0.15          # Impressum nennt denselben Namen -> Domain sitzt
    return round(min(score, 1.0), 3)


def needs_review(confidence: float) -> bool:
    return confidence < RESOLUTION_MIN_CONFIDENCE
