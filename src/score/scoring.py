"""Scoring: welcher Account ist JETZT dran?

score = signal_weight x recency x icp_fit x resolution_confidence (+ Stacking)

Bewusst multiplikativ und nicht additiv: Ein starkes Signal auf einem
Account, dessen Firmenzuordnung wacklig ist, darf nicht nach oben rutschen.
Die Confidence wirkt als Daempfer auf alles andere - Praezision vor Volumen.

score_components wird als JSON mitexportiert. Jeder Score ist damit
aufklappbar statt Blackbox. Das ist die Antwort auf "Quelle und Confidence
fuer jedes Feld der Logik".
"""
from __future__ import annotations

from datetime import date
from typing import Any

from src.config import (
    DAMPEN_FLOOR, RECENCY_BUCKETS, RECENCY_FLOOR, SCORE_MAX_RAW,
    SIGNAL_WEIGHTS, STACKING_BONUS, TIER_FIT,
)


def recency_factor(event_date: str | None, today: date | None = None) -> float:
    if not event_date:
        return RECENCY_FLOOR
    today = today or date.today()
    try:
        age = (today - date.fromisoformat(event_date[:10])).days
    except ValueError:
        return RECENCY_FLOOR
    if age < 0:                       # Frist in der Zukunft = maximal aktuell
        return 1.0
    for max_age, factor in RECENCY_BUCKETS:
        if age <= max_age:
            return factor
    return RECENCY_FLOOR


def score_account(
    signals: list[dict[str, Any]],
    tier: str = "C",
    today: date | None = None,
) -> tuple[int, dict[str, Any]]:
    """Alle Signale eines Accounts -> ein Score 0-100 + Herleitung.

    Es zaehlt das staerkste Einzelsignal, nicht die Summe: Zehn schwache
    Signale sind kein starkes. Mehrere VERSCHIEDENE Signaltypen bekommen
    dagegen einen Stacking-Bonus, weil unabhaengige Belege sich gegenseitig
    stuetzen.
    """
    if not signals:
        return 0, {"reason": "keine Signale"}

    today = today or date.today()
    fit = TIER_FIT.get(tier, 0.3)

    scored = []
    for s in signals:
        w = SIGNAL_WEIGHTS.get(s.get("signal_type", ""), 1)
        rec = recency_factor(s.get("event_date"), today)
        conf = float(s.get("match_confidence") or 0.5)

        # Fit und Confidence wirken als GEDAEMPFTE Multiplikatoren, nicht roh.
        # Begruendung: Eine wacklige Firmenzuordnung soll ein starkes Signal
        # abwerten, aber nicht ausloeschen - sonst verschwindet ein
        # Nachpruefungsverfahren hinter einer 0.65-Confidence. Die Daempfung
        # bildet die Bandbreite [0.4 .. 1.0] statt [0 .. 1.0] ab.
        fit_d = DAMPEN_FLOOR + (1 - DAMPEN_FLOOR) * fit
        conf_d = DAMPEN_FLOOR + (1 - DAMPEN_FLOOR) * conf

        scored.append({
            "signal_type": s.get("signal_type"),
            "event_date": s.get("event_date"),
            "weight": w,
            "recency": rec,
            "icp_fit_dampened": round(fit_d, 3),
            "confidence": round(conf, 3),
            "confidence_dampened": round(conf_d, 3),
            "raw": round(w * rec * fit_d * conf_d, 3),
            "source_url": s.get("source_url"),
            # Referenz auf das Originalsignal. Ohne die faellt der Why-now-Satz
            # auseinander: Der Text muss aus GENAU dem Signal kommen, das den
            # Score treibt, sonst widersprechen sich Spalte und Satz.
            "_signal": s,
        })

    scored.sort(key=lambda x: x["raw"], reverse=True)
    best = scored[0]
    distinct_types = {s["signal_type"] for s in scored}

    raw = best["raw"]
    stacking = 0.0
    if len(distinct_types) >= 2:
        stacking = STACKING_BONUS * fit
        raw += stacking

    score = int(round(min(raw / SCORE_MAX_RAW, 1.0) * 100))

    driver_signal = best.pop("_signal", None)
    for s in scored:
        s.pop("_signal", None)

    return score, {
        "formula": "min(best(weight x recency x fit_d x conf_d) + stacking, cap) / cap x 100",
        "tier": tier,
        "icp_fit": fit,
        "dampening": "fit und confidence wirken auf [0.4 .. 1.0]",
        "signal_count": len(scored),
        "distinct_signal_types": sorted(distinct_types),
        "stacking_bonus": round(stacking, 3),
        "driver": best,
        "driver_signal": driver_signal,
        "all_signals": scored[:5],
    }


# --- Why-now ------------------------------------------------------------------
# Regel: IMMER das konkrete Artefakt zitieren, nie die Kategorie.
# "Sie sind im oeffentlichen Sektor aktiv" ist wertlos.
# "Ihr Rahmenvertrag mit X endet am 31.03.2027" ist ein Gespraechsanlass.

WHY_NOW_TEMPLATES = {
    "rahmenvertrag_laeuft_aus": (
        "Ihr Rahmenvertrag „{title}“ mit {buyer} endet am {contract_end} "
        "— die Neuausschreibung startet erfahrungsgemäß rund sechs Monate vorher."
    ),
    "nachpruefung_vergabekammer": (
        "Sie haben im Verfahren „{title}“ ein Nachprüfungsverfahren angestrengt "
        "({event_date}) — häufig liegt die Ursache in einem Eignungs- oder "
        "Ausschlusskriterium, das erst spät im Dokument auftaucht."
    ),
    "offene_ausschreibung_im_profil": (
        "{buyer} hat „{title}“ ausgeschrieben, Abgabefrist in {days_to_deadline} Tagen "
        "— passt auf Ihr CPV-Profil."
    ),
    "zuschlag_gewonnen": (
        "Sie haben am {event_date} den Zuschlag für „{title}“ ({buyer}) erhalten "
        "— im selben CPV-Segment laufen aktuell weitere Verfahren."
    ),
    "bid_rolle_ausgeschrieben": (
        "Sie suchen seit {event_date} eine Verstärkung im Angebotsmanagement "
        "({title}{place}) — das Verfahrensvolumen wächst offenbar schneller als das Team."
    ),
}


def build_why_now(signal: dict[str, Any]) -> str:
    stype = signal.get("signal_type", "")
    payload = signal.get("payload") or {}
    if isinstance(payload, str):
        import json as _json
        try:
            payload = _json.loads(payload)
        except ValueError:
            payload = {}

    place = signal.get("org_place")
    ctx = {
        "title": (signal.get("title") or "").strip()[:110] or "dem Verfahren",
        "buyer": payload.get("buyer") or signal.get("org_name_raw") or "der Vergabestelle",
        "event_date": _de_date(signal.get("event_date")),
        "contract_end": _de_date(payload.get("contract_end")),
        "days_to_deadline": payload.get("days_to_deadline", "wenigen"),
        "place": f", Standort {place}" if place else "",
    }
    tpl = WHY_NOW_TEMPLATES.get(stype)
    if not tpl:
        return f"Signal {stype} vom {ctx['event_date']}."
    try:
        return tpl.format(**ctx)
    except (KeyError, IndexError):
        return f"Signal {stype} vom {ctx['event_date']}."


def _de_date(iso: str | None) -> str:
    if not iso:
        return "zuletzt"
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return str(iso)
