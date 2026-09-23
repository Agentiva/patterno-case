# Tiering: warum es ein eigener Schritt ist

## Das Problem

Die erste Fassung hat die Longlist gebaut **und** in einem Zug eingestuft.
Das Ergebnis sah so aus:

```
tier         B: 2.464   C: 4
```

2.464 von 2.468 Zeilen auf demselben Tier. Das ist kein Urteil, das ist ein
**fehlender Wert in Verkleidung**: `employees` war beim Bau der Liste immer
leer, also fiel jede Firma in denselben Zweig von `tier_for()` und bekam die
Begründung „Mitarbeiterzahl nicht ermittelt".

Ein Tier, das nichts unterscheidet, ist als Priorisierung wertlos — und
gefährlicher als gar kein Tier, weil es wie eine Bewertung aussieht.

Der Grund ist zeitlicher Natur. Das Tiering braucht zwei Dinge, die zu
verschiedenen Zeitpunkten entstehen:

| Zutat | Herkunft | verfügbar |
|---|---|---|
| Belegart, Verfahrenszahlen | Vergabedaten | sofort |
| Domain, Mitarbeiterzahl | Clay / Apollo | Stunden bis Tage später |

## Die Lösung: drei Schritte statt einem

```
1. python3 -m src.cli longlist --live --months 12
      -> 2.468 Firmen, Beleg + proof_url
      -> tier vorläufig, tier_status = vorlaeufig_ohne_mitarbeiterzahl

2. Clay oder src/enrich/apollo.py
      -> Domain + Mitarbeiterzahl je Firma

3. python3 -m src.cli retier --from <export.csv>
      -> endgültige Tiers, tier_status = final
   python3 -m src.cli export
      -> die Signal-Liste übernimmt die neuen Tiers
```

Kurzform: `make retier FROM=clay-export.csv` (macht Schritt 3 und den Export).

Die Spalte **`tier_status`** steht in jeder Zeile und sagt, welcher Fall
zutrifft. Ein Reviewer sieht damit sofort, welche Einstufungen auf einer
echten Mitarbeiterzahl beruhen und welche nur auf der Belegart.

## Was `retier` erwartet

Eine CSV (Clay-Export) oder JSON (Ausgabe von `src/enrich/apollo.py`).
Gematcht wird in dieser Reihenfolge:

1. `company_id` — der Schlüssel, den die Pipeline selbst vergibt. Kommt er
   zurück, ist die Zuordnung eindeutig. **Diese Spalte in Clay mitführen.**
2. normalisierter `legal_name` — Rückfallebene
3. `domain` — Rückfallebene

Spaltennamen sind flexibel, `FIELD_ALIASES` in `enrich_merge.py` kennt die
üblichen Schreibweisen (`employees`, `employee_count`, `mitarbeiterzahl`,
`estimated_num_employees`, `headcount`, `size` …). Minimal reicht:

| Spalte | Pflicht | Beispiel |
|---|---|---|
| `company_id` | ja (sonst Name) | `controlware` |
| `domain` | nein | `controlware.de` |
| `employees` | für das Tiering ja | `900` |
| `country` | empfohlen | `Germany` |
| `city` | nein | `Dietzenbach` |

Vorlage zum Abgleichen: [`retier_vorlage.csv`](retier_vorlage.csv).

Zahlenformate werden aufgeräumt: `1.234` → 1234, `250-500` → 375 (Mitte),
`10.000+` → 10000, `k.A.` → leer. Domains werden von `https://`, `www.` und
Pfaden befreit.

## Die Konzernfalle — warum nicht jede Zahl ins Tiering darf

Apollo löst eine Domain auf den **Konzern** auf, die Vergabe ging aber an den
**Rechtsträger**. Gemessen am echten Lauf über 10 gematchte Firmen:

| Zuschlag an | gemeldet | übernommen? |
|---|---|---|
| Controlware GmbH | 900 | ja → **Tier A** |
| Arktis IT solutions GmbH | 63 | ja → **Tier A** |
| MR Datentechnik | 550 | ja → **Tier A** |
| WBS IT-Service GmbH | 180 | ja → **Tier A** |
| iteratec GmbH | 500 | ja → **Tier A** |
| SVA System Vertrieb Alexander | 3.200 | nein — über ICP-Oberkante |
| CANCOM GmbH | 5.300 | nein — über ICP-Oberkante |
| adesso SE | 12.000 | nein — über ICP-Oberkante |
| Bechtle GmbH | 17.000 | nein — Konzernwert |
| Computacenter | 21.000 | nein — **Sitz UK**, Zuschlag ging an die deutsche oHG |

Fünf von zehn Werten sind für das Tiering unbrauchbar. Sie werden
**nicht** übernommen, sondern in `employees_scope = konzern_oder_unklar`
markiert; die gemeldete Zahl bleibt in `employees_note` erhalten und geht
also nicht verloren. `tier_status` bleibt bei diesen Zeilen `vorlaeufig`.

Der Grund ist nicht Pedanterie: Wer 17.000 für ein regionales Systemhaus
übernimmt, stuft es aus dem ICP heraus und schreibt den Konzernvertrieb an
statt die Niederlassung, die tatsächlich geboten hat.

**Lieber „nicht ermittelt" als falsch eingestuft.**

## Die Tiering-Regel

`tier_for()` in `src/longlist/build.py` — eine reine Funktion auf Werten,
damit sie an beiden Stellen identisch läuft.

| Bedingung | Tier |
|---|---|
| nur über Sammelvergabe mit fachfremden Gewerken belegt | C |
| starker Beleg **und** 50–2.000 MA | **A** |
| starker Beleg, aber < 50 MA | C |
| starker Beleg, aber > 2.000 MA | B |
| starker Beleg, MA unbekannt | B *(vorläufig)* |
| Public-Sector-Bezug ohne Zuschlag | C |
| nur Branchen-/Größenpassung | D |

Starke Belege sind `P1_zuschlag_24m`, `P2_zuschlag_48m`,
`P1B_bieter_unterlegen`, `P1C_alleinbieter`, `P1D_ausgang_offen`.

## Wie man erkennt, dass es funktioniert hat

`retier` gibt die Tier-Verteilung vorher/nachher aus und beendet sich mit
Exit-Code 1, wenn **keine einzige** Zeile eine nutzbare Mitarbeiterzahl
bekommen hat — dann stimmen die Spaltennamen der Quelldatei nicht. Ein Lauf,
der nichts bewirkt, darf nicht wie ein Erfolg aussehen.
