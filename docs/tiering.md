# Tiering: warum die Mitarbeiterzahl nicht eingeht

## Der Fehler, der korrigiert wurde

Die erste Fassung stufte nach Mitarbeitenden ein — Zielkorridor 50–2.000,
so steht es im ICP. Das klang vernünftig und war unbrauchbar:

```
tier         B: 2.464   C: 4
```

2.464 von 2.468 Zeilen auf demselben Tier. Kein Urteil, sondern ein
**fehlender Wert in Verkleidung**: `employees` kommt erst aus dem
Enrichment, war beim Bau der Liste immer leer, also fiel jede Firma in
denselben Zweig.

*(Die Liste zählte damals 2.468 Firmen, heute 2.458 — dazwischen kamen die
Personaldienstleister auf die Ausschlussliste. Die historischen Zahlen bleiben
hier stehen, wie sie gemessen wurden.)*

Der zweite Befund wog schwerer. Dort, wo die Zahl vorlag, war sie bei
**5 von 10 Firmen die des Konzerns** statt die des bietenden Rechtsträgers:

| Zuschlag an | Apollo meldet | tatsächlich |
|---|---|---|
| Bechtle GmbH & Co. KG | 17.000 | die Bechtle AG, nicht das regionale Systemhaus |
| Computacenter AG & Co. oHG (Kerpen) | 21.000, Sitz UK | die britische Konzernmutter |
| adesso SE | 12.000 | Konzern |
| CANCOM GmbH | 5.300 | Konzern |
| SVA System Vertrieb Alexander | 3.200 | über ICP-Oberkante |

Ein Tier darf nicht an einem Fremddatum hängen, das meistens fehlt und oft
das falsche Unternehmen beschreibt.

## Woran das Tier jetzt hängt

Ausschließlich an dem, was aus den Vergabedaten belegt ist — und das ist
mehr, als es klingt:

| Merkmal | Spanne in den Daten |
|---|---|
| **Häufigkeit** — Verfahren in 12 Monaten | 1 bis 131 |
| **Aktualität** — Alter des jüngsten Belegs | Median 177 Tage |
| **Breite** — verschiedene Auftraggeber | 626 Firmen mit > 1 |
| **Belegart** — Zuschlag benannt, erschlossen, offen | 6 Stufen |

### Die Regel

```
mixed_lot_only                                    → C
kein starker Beleg (P3/P4/P5)                     → C
kein Public-Sector-Beleg (P6)                     → D
≥ 3 Verfahren  UND  Beleg ≤ 180 Tage              → A
≥ 2 Verfahren                                     → B
1 Verfahren, aber Beleg ≤ 180 Tage                → B
sonst                                             → C
```

`tier_for()` in `src/longlist/build.py`. Ergebnis über 2.458 Firmen:

```
A   233   (  9 %)   laufender Angebotsprozess
B 1.261   ( 51 %)   wiederkehrender oder aktueller Bieter
C   964   ( 39 %)   Teilnahme belegt, weder häufig noch aktuell
```

Die Begründung steht ausgeschrieben in jeder Zeile und ist nachrechenbar:

> „131 Verfahren in 12 Monaten, jüngster Beleg vor 1 Monat, 24 verschiedene
> Auftraggeber – laufender Angebotsprozess"

### `tier_status`

Sagt nicht mehr „vorläufig/final" — das hing an der Mitarbeiterzahl.
Stattdessen: worauf das Tier beruht.

| Wert | Bedeutung |
|---|---|
| `zuschlag_benannt` | Gewinner ausdrücklich in der Bekanntmachung |
| `zuschlag_erschlossen` | einziger Bieter → Zuschlag abgeleitet |
| `teilnahme_offen` | Bieter benannt, Ausgang nicht ableitbar |
| `schwacher_beleg` | Rahmenvertrag/Referenz ohne Zuschlag |

Damit ist ohne Blick in `proof_type` klar, wie belastbar die Einstufung ist.

## Die Gegenprobe

Von den fünf Firmen, die unabhängig über Apollo als ICP-passend bestätigt
wurden (63–900 MA), landen **drei allein aus den Vergabedaten in Tier A**:

| Firma | MA | Tier | warum |
|---|---|---|---|
| Controlware | 900 | **A** | 17 Verfahren, jüngster Beleg vor 1 Monat |
| MR Datentechnik | 550 | **A** | 6 Verfahren, Beleg vor 19 Tagen |
| WBS IT-Service | 180 | **A** | 6 Verfahren, Beleg vor 5 Tagen |
| iteratec | 500 | B | 4 Verfahren, aber Beleg 7 Monate alt |
| ARKTIS IT solutions | 63 | B | 13 Verfahren, aber Beleg 12 Monate alt |

Die Größe korreliert also mit der Einstufung, ohne dass wir sie brauchen.

## Der ehrliche Preis dieser Entscheidung

Das Tier misst **Ausschreibungsaktivität, nicht Größenpassung.** Bechtle
(104 Verfahren) und SVA (131 Verfahren) landen deshalb in Tier A, obwohl
sie über dem ICP-Korridor liegen. Das ist kein Fehler, sondern die
Konsequenz: Wer ständig bietet, hat den Angebotsprozess, um den es geht.

Die Größenpassung filtert man nachgelagert über `employees` — dort steht
sie, sobald angereichert. Sie ist nur kein Eingangswert der Einstufung mehr.

## Enrichment einspielen

```bash
make retier FROM=clay-export.csv     # Anreicherung + Tiers nachziehen
python3 -m src.cli retier            # nur Tiers nachziehen (ohne Quelle)
```

`--from` ist optional, weil ein Tier-Kriterium mit der Zeit wandert: Der
jüngste Beleg altert jeden Tag. Der Lauf meldet, wie viele Zeilen allein
dadurch das Tier gewechselt haben.

### Was `retier` aus der Quelldatei liest

Gematcht wird in dieser Reihenfolge:

1. `company_id` — der Schlüssel, den die Pipeline selbst vergibt.
   **Diese Spalte in Clay unbedingt mitführen**, dann ist die Zuordnung eindeutig.
2. normalisierter `legal_name` — Rückfallebene
3. `domain` — Rückfallebene

| Spalte | wofür | Einfluss aufs Tier |
|---|---|---|
| `company_id` | Join-Key | — |
| `domain` | Ansprache, Personensuche | **nein** |
| `employees` | Segmentierung, Größenfilter | **nein** |
| `country` | erkennt Konzern-/Auslandstreffer | **nein** |
| `city`, `industry`, `linkedin` | Kontext | **nein** |

Spaltennamen sind flexibel — `FIELD_ALIASES` in `enrich_merge.py` kennt
`employee_count`, `mitarbeiterzahl`, `estimated_num_employees`, `headcount`,
`website`, `url` und weitere. Zahlenformate werden aufgeräumt: `1.234` →
1234, `250-500` → 375 (Mitte), `10.000+` → 10000, `k.A.` → leer. Domains
werden von `https://`, `www.` und Pfaden befreit.

Vorlage zum Abgleichen: [`retier_vorlage.csv`](retier_vorlage.csv).

### Konzernwerte landen nicht in `employees`

Auch wenn die Zahl das Tier nicht mehr beeinflusst, bleibt sie für die
Ansprache entscheidend: Wer 17.000 als Größe des regionalen Systemhauses
liest, schreibt den Konzernvertrieb an statt die Niederlassung, die
geboten hat.

Deshalb prüft `classify_headcount()` weiter auf Sitzland, ICP-Oberkante und
Namensabweichung. Ein auffälliger Wert geht **nicht** nach `employees`,
sondern nach `employees_note`, und `employees_scope` wird auf
`konzern_oder_unklar` gesetzt. Sichtbar, aber nicht als Eigenschaft des
Bieters ausgegeben.

## Wie man erkennt, dass es funktioniert hat

`retier` endet mit Exit-Code 1, wenn **keine** Zeile zugeordnet werden
konnte oder wenn zugeordnete Zeilen weder Domain noch Mitarbeiterzahl
geliefert haben — dann stimmen die Spaltennamen nicht. Ein Lauf, der nichts
bewirkt, darf nicht wie ein Erfolg aussehen.

Geprüft wird dabei die Wirkung **dieses** Laufs, nicht der Gesamtzustand der
Datei. Der erste Entwurf prüfte letzteres, und eine Quelle mit falschen
Spalten lief als Erfolg durch, solange ein früherer Lauf schon etwas
gefüllt hatte.
