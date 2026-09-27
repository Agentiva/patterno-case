"""Vollstaendigkeitsschaetzung per Fang-Wiederfang, aus dem Korpus selbst.

=== WARUM DAS VORHER NICHT DASTAND ===
Aufgabe 1c fragt drei Dinge: wie gross der Markt insgesamt ist, wie viel die
Liste davon abdeckt, und woher man das weiss. Die Antwort im README war
monatelang: "Keine Vollstaendigkeitsschaetzung - dafuer fehlt eine zweite,
unabhaengige Quelle."

Die Begruendung war richtig und die Antwort trotzdem falsch. Richtig war: Es
gibt keine zweite Liste deutscher IT-Systemhaeuser mit Vergabebezug, gegen die
man abgleichen koennte; Branchenrankings ueberrepraesentieren grosse Firmen
genauso wie Vergabedaten. Falsch war der Schluss daraus. Die Frage lautet
"woher weisst du das", nicht "nenne eine Zahl" - sie verlangt eine Methode mit
ausgewiesenen Grenzen, und eine Verweigerung ist keine.

=== DIE METHODE ===
Fang-Wiederfang braucht keine zweite Quelle, sondern zwei unabhaengige
BEOBACHTUNGSGELEGENHEITEN. Die stecken im Korpus: 12 Monate lassen sich in
zwei Haelften schneiden. Eine Firma, die in beiden Haelften bietet, ist ein
Wiederfang.

    n1  Firmen in Periode 1
    n2  Firmen in Periode 2
    m   Firmen in beiden

Lincoln-Petersen schaetzt daraus die Gesamtpopulation:  N = n1 * n2 / m
Verwendet wird der Chapman-Schaetzer, der bei kleinem m weniger verzerrt ist:

    N = (n1+1)(n2+1)/(m+1) - 1

=== WAS DIE ZAHL NICHT IST, UND WARUM SIE TROTZDEM TAUGT ===
Fang-Wiederfang setzt GLEICHE FANGWAHRSCHEINLICHKEIT voraus. Diese Annahme
ist hier verletzt, und zwar systematisch: SVA mit 131 Verfahren im Jahr wird
mit Sicherheit in beiden Haelften auftauchen, ein Systemhaus mit einem
einzigen Verfahren nur zufaellig in einer.

Die Richtung dieser Verzerrung ist bekannt. Ungleiche Fangwahrscheinlichkeit
treibt m nach oben (die Vielbieter erscheinen zwangslaeufig doppelt) und
damit N nach UNTEN. Der Schaetzer liefert also eine UNTERGRENZE der
Population, keine Punktschaetzung.

Das ist kein Mangel, solange man es sagt. Eine belastbare Untergrenze mit
genannter Verzerrungsrichtung ist eine Antwort; "kann ich nicht wissen" ist
keine.

Gegen die Verzerrung laufen zwei Massnahmen:

  1. Drei verschiedene Schnitte statt eines. Halbjahre, abwechselnde Monate
     und abwechselnde Quartale haben unterschiedliche Trendanfaelligkeit.
     Laufen die Ergebnisse weit auseinander, ist die Annahme so stark
     verletzt, dass die Zahl nichts taugt - das waere dann der Befund.

  2. Chao1 ueber 12 monatliche Gelegenheiten statt zwei. Dieser Schaetzer
     ist genau fuer den Fall gebaut, in dem die Fangwahrscheinlichkeit
     UNGLEICH ist, und er ist mathematisch als Untergrenze definiert - nicht
     nur "wahrscheinlich zu niedrig", sondern beweisbar. Er zaehlt, wie
     viele Firmen in genau einem und in genau zwei Monaten auftauchen:

         Chao1 = S + f1^2 / (2*f2)

     Die Logik dahinter ist anschaulich: Viele Firmen, die nur EINMAL
     gesehen wurden, heissen, dass noch viele gar nicht gesehen wurden.
     Verwendet wird die bias-korrigierte Form, die bei kleinem f2 stabil
     bleibt:  S + f1*(f1-1) / (2*(f2+1)).

=== WAS DIESE ZAHL NICHT ABDECKT ===
Sie schaetzt, wie viele Firmen im SICHTBAREN Vergabegeschehen fehlen. Sie
sagt nichts ueber das, was der Datenservice strukturell nicht enthaelt -
Unterschwellenvergaben unterhalb der Veroeffentlichungspflicht. Das ist eine
andere Art von Luecke: kein Stichprobenfehler, sondern ein blinder Fleck.
Der gehoert getrennt ausgewiesen und nicht in dieselbe Zahl gerechnet.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from src.config import CPV_IT_PREFIXES
from src.longlist.build import companies_from_awards

DATA = Path("data")
FIXTURE = Path("fixtures/vergabe_dovs.longlist.json")


def cpv_ok(codes) -> bool:
    return any(str(c).startswith(p) for c in codes for p in CPV_IT_PREFIXES)


def chapman(n1: int, n2: int, m: int) -> tuple[float, float, float]:
    """Chapman-Schaetzer mit 95-%-Intervall.

    Rueckgabe: (N, untere Grenze, obere Grenze)

    Chapman statt Lincoln-Petersen, weil letzterer bei kleinem m nach oben
    verzerrt und bei m = 0 nicht definiert ist. Die Varianz nach Seber.
    """
    if m <= 0:
        return float("nan"), float("nan"), float("nan")
    N = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = ((n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m)
           / ((m + 1) ** 2 * (m + 2)))
    se = math.sqrt(var) if var > 0 else 0.0
    return N, N - 1.96 * se, N + 1.96 * se


def chao1(haeufigkeit: dict[str, int]) -> tuple[float, float, int, int]:
    """Chao1 (bias-korrigiert) mit unterer 95-%-Grenze.

    haeufigkeit: Firmenschluessel -> in wie vielen Monaten gesehen.

    Rueckgabe: (N, untere Grenze, f1, f2)

    Chao1 ist eine UNTERGRENZE, und das ist hier der Punkt. Lincoln-Petersen
    setzt gleiche Fangwahrscheinlichkeit voraus und ist bei Verletzung
    unbestimmt verzerrt. Chao1 gibt die Heterogenitaet auf und liefert
    stattdessen eine Aussage, die auch bei beliebig ungleicher
    Fangwahrscheinlichkeit gilt: mindestens so viele.
    """
    S = len(haeufigkeit)
    f1 = sum(1 for v in haeufigkeit.values() if v == 1)
    f2 = sum(1 for v in haeufigkeit.values() if v == 2)
    N = S + f1 * (f1 - 1) / (2 * (f2 + 1))
    # Varianz nach Chao (1987) fuer die bias-korrigierte Form.
    f0 = N - S
    if f0 > 0:
        var = (f0 * (f1 / (2 * (f2 + 1))) ** 2
               + f0 * ((f1 / (f2 + 1)) ** 2) / 2
               + f0 ** 2 / (f2 + 1) / 4)
        se = math.sqrt(abs(var))
    else:
        se = 0.0
    return N, N - 1.96 * se, f1, f2


def _monat(rel: dict) -> str:
    return (rel.get("date") or "")[:7]


def _firmen(releases: list[dict]) -> set[str]:
    """Firmenschluessel einer Release-Menge - mit DERSELBEN Funktion wie die
    Longlist. Eine eigene Extraktion hier waere eine zweite Wahrheit und
    wuerde genau die Zahl verfaelschen, die geschaetzt werden soll."""
    return set(companies_from_awards(releases, cpv_ok).keys())


def volle_monate(releases: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    """Nur Monate mit vollstaendiger Abdeckung behalten.

    === WARUM DAS NOETIG IST ===
    Der Korpus wird nach `pubMonth` geladen - dem Monat, in dem die
    Bekanntmachung VEROEFFENTLICHT wurde. Geschnitten wird hier aber nach
    `release.date`, und das ist nicht dasselbe: Ein Paket vom Maerz 2026
    enthaelt auch Nachmeldungen und Zuschlaege zu Verfahren von 2025 oder
    frueher.

    Gemessen an diesem Korpus:

        2024-10 bis 2025-08    1 bis 28 Releases je Monat   <- Nachmeldungen
        2025-09                              319            <- Anlauf
        2025-10 bis 2026-09        1.136 bis 1.745          <- volle Monate

    Die erste Fassung hat ohne diesen Filter geschnitten. Der duenne Schwanz
    landete komplett in Periode 1, und die Halbjahre kamen auf 636 gegen
    2.108 Firmen - ein Fangunterschied von Faktor 3, der nichts mit der
    Population zu tun hat, sondern mit der Korpusform. Der Schaetzer haette
    trotzdem eine plausibel aussehende Zahl geliefert.

    Schwelle: die Haelfte des Medianmonats. Bewusst grob - es geht darum,
    Anlauf und Nachmeldungen zu entfernen, nicht darum, saisonale
    Schwankungen wegzurechnen.
    """
    zaehler: dict[str, int] = {}
    for r in releases:
        mo = _monat(r)
        if mo:
            zaehler[mo] = zaehler.get(mo, 0) + 1
    if not zaehler:
        raise SystemExit("Keine Releases mit Datum im Korpus")

    werte = sorted(zaehler.values())
    median = werte[len(werte) // 2]
    schwelle = median / 2
    voll = sorted(mo for mo, n in zaehler.items() if n >= schwelle)
    raus = sorted(mo for mo, n in zaehler.items() if n < schwelle)
    gefiltert = [r for r in releases if _monat(r) in set(voll)]
    return gefiltert, voll, raus


def schnitte(releases: list[dict]) -> dict[str, tuple[list, list]]:
    """Drei Aufteilungen des Korpus in zwei Beobachtungsgelegenheiten."""
    monate = sorted({_monat(r) for r in releases if _monat(r)})
    if len(monate) < 4:
        raise SystemExit(f"Korpus umfasst nur {len(monate)} Monate - zu kurz")

    mitte = len(monate) // 2
    erste, zweite = set(monate[:mitte]), set(monate[mitte:])
    gerade = {mo for i, mo in enumerate(monate) if i % 2 == 0}
    q_a = {mo for i, mo in enumerate(monate) if (i // 3) % 2 == 0}

    return {
        # Einfachster Schnitt, aber trendanfaellig: Wenn im zweiten Halbjahr
        # mehr ausgeschrieben wurde, wirkt das wie ein Fangunterschied.
        "Halbjahre": ([r for r in releases if _monat(r) in erste],
                      [r for r in releases if _monat(r) in zweite]),
        # Abwechselnde Monate: robust gegen Jahrestrend, anfaellig gegen
        # Saison (Dezember und August sind vergabearm).
        "Monate abwechselnd": ([r for r in releases if _monat(r) in gerade],
                               [r for r in releases if _monat(r) not in gerade]),
        # Abwechselnde Quartale: mittelt die Saison heraus, behaelt aber
        # genug Abstand zwischen den Gelegenheiten.
        "Quartale abwechselnd": ([r for r in releases if _monat(r) in q_a],
                                 [r for r in releases if _monat(r) not in q_a]),
    }


def main() -> int:
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    releases = d if isinstance(d, list) else (d.get("releases") or [])
    ll = list(csv.DictReader(open(DATA / "longlist_markt.csv", encoding="utf-8-sig")))
    beobachtet = len(ll)

    print(f"Korpus: {len(releases)} IT-Releases")
    voll_rel, voll, raus = volle_monate(releases)
    print(f"Volle Monate: {len(voll)} ({voll[0]} bis {voll[-1]}), "
          f"{len(voll_rel)} Releases")
    if raus:
        print(f"Ausgeschlossen: {len(raus)} Monate mit Nachmeldungen "
              f"({raus[0]} bis {raus[-1]}), "
              f"{len(releases) - len(voll_rel)} Releases")
    # Der Nenner muss zur Schaetzung passen.
    #
    # N entsteht aus den 12 vollen Monaten. Die Longlist enthaelt zusaetzlich
    # Firmen, die nur in den Nachmeldemonaten auftauchen. Die gegen N zu
    # rechnen waere ein Nennerfehler: Man vergleicht eine Beobachtung aus
    # einem groesseren Zeitraum mit einer Schaetzung aus einem kleineren und
    # bekommt eine zu hohe Abdeckung geschenkt.
    beobachtet_voll = len(_firmen(voll_rel))
    print(f"Beobachtet in der Longlist:      {beobachtet} Firmen "
          f"(voller Korpus)")
    print(f"davon in den 12 vollen Monaten:  {beobachtet_voll} Firmen "
          f"<- Nenner der Abdeckung")
    print(f"nur aus Nachmeldemonaten:        {beobachtet - beobachtet_voll}\n")

    zeilen = []
    for name, (a, b) in schnitte(voll_rel).items():
        fa, fb = _firmen(a), _firmen(b)
        n1, n2, m = len(fa), len(fb), len(fa & fb)
        N, lo, hi = chapman(n1, n2, m)
        abdeckung = beobachtet_voll / N if N and N == N else float("nan")
        print(f"{name}")
        print(f"  Periode 1        {n1:6}")
        print(f"  Periode 2        {n2:6}")
        print(f"  in beiden        {m:6}   ({m/min(n1,n2):.1%} der kleineren Periode)")
        print(f"  N (Chapman)      {N:6.0f}   95-%-Intervall {lo:.0f} - {hi:.0f}")
        print(f"  Abdeckung        {abdeckung:6.1%}\n")
        zeilen.append({"schnitt": name, "n1": n1, "n2": n2, "beide": m,
                       "n_geschaetzt": round(N), "ki_unten": round(lo),
                       "ki_oben": round(hi), "beobachtet": beobachtet_voll,
                       "abdeckung": f"{abdeckung:.3f}"})

    # Chao1 ueber 12 monatliche Gelegenheiten. Dafuer muss je Firma gezaehlt
    # werden, in wie vielen Monaten sie auftaucht - deshalb ein Durchlauf je
    # Monat mit derselben Extraktionsfunktion.
    print("Chao1 ueber 12 monatliche Gelegenheiten")
    haeufigkeit: dict[str, int] = {}
    for mo in voll:
        for key in _firmen([r for r in voll_rel if _monat(r) == mo]):
            haeufigkeit[key] = haeufigkeit.get(key, 0) + 1
    N_c, lo_c, f1, f2 = chao1(haeufigkeit)
    verteilung = {k: sum(1 for v in haeufigkeit.values() if v == k)
                  for k in range(1, 6)}
    print(f"  Firmen in genau 1 Monat   f1 = {f1}")
    print(f"  Firmen in genau 2 Monaten f2 = {f2}")
    print(f"  Verteilung 1-5 Monate        {verteilung}")
    print(f"  N (Chao1, Untergrenze)    {N_c:6.0f}   untere 95-%-Grenze {lo_c:.0f}")
    print(f"  Abdeckung                 {beobachtet_voll / N_c:6.1%}\n")
    zeilen.append({"schnitt": "Chao1 (12 Monate)", "n1": f1, "n2": f2,
                   "beide": len(haeufigkeit), "n_geschaetzt": round(N_c),
                   "ki_unten": round(lo_c), "ki_oben": "",
                   "beobachtet": beobachtet_voll,
                   "abdeckung": f"{beobachtet_voll / N_c:.3f}"})

    # Streuung der drei Schnitte. Laufen sie weit auseinander, ist die
    # Gleichheitsannahme so stark verletzt, dass die Zahl nichts taugt -
    # und DAS ist dann das Ergebnis, nicht der Mittelwert.
    schaetzer = [z["n_geschaetzt"] for z in zeilen
                 if not z["schnitt"].startswith("Chao1")]
    spanne = (max(schaetzer) - min(schaetzer)) / min(schaetzer)
    print(f"Streuung der drei Schnitte: {min(schaetzer)} bis {max(schaetzer)} "
          f"({spanne:.0%})")
    if spanne > 0.35:
        print("  ! Die Schnitte widersprechen sich zu stark. Die Annahme "
              "gleicher Fangwahrscheinlichkeit ist zu deutlich verletzt;")
        print("  ! als Punktschaetzung ist das nicht brauchbar, nur als "
              "Untergrenze aus dem niedrigsten Schnitt.")
    else:
        print("  Die Schnitte stimmen ueberein - fuer eine Untergrenze "
              "belastbar.")

    out = DATA / "vollstaendigkeit.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0]), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(zeilen)
    print(f"\n{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
