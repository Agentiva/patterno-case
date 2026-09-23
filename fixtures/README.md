# Fixtures

Die JSON-Dateien hier sind **synthetisch** und mit `make_fixtures.py` erzeugt.
Firmennamen sind frei erfunden.

Zweck: `make demo` laeuft ohne Netzzugang und ohne API-Keys. Das ist fuer eine
Live-Demo wichtig, in der man sich nicht auf fremde APIs verlassen will.

Die Struktur entspricht dem **verifizierten** Schema der echten Quellen:
- `ba_jobs.json` -> `JobSearchResponse` aus https://github.com/bundesAPI/jobsuche-api (openapi.yaml v2.1.0)
- `vergabe_dovs.json` -> OCDS-Releases, `releases[].awards[].suppliers[]`

Die Testdaten decken bewusst die Kanten ab, an denen eine Pipeline bricht:
Bietergemeinschaft, oeffentlicher Inhouse-Dienstleister, Wettbewerber,
einkaufsseitige Stellenanzeige, Rahmenvertrag kurz vor Ablauf, Umlaute.

`make run` (live) ueberschreibt die Dateien mit echten API-Antworten.

---
## Stand 23.09.2026: echte Daten

`make run` lief erstmals gegen die Live-APIs. Die Fixtures wurden dabei mit
echten Antworten ueberschrieben und sind nicht mehr synthetisch.

### Was eingecheckt ist und was nicht

| Datei | im Repo | Inhalt |
|---|---|---|
| `*.sample.json` | ja | geschichtete Stichprobe, erzeugt von `make_samples.py` |
| `vergabe_dovs.json` | nein (.gitignore) | 3 Monate Signalfenster |
| `vergabe_dovs.longlist.json` | nein (.gitignore) | 12 Monate, auf IT gefiltert, ~78 MB |
| `ted.json`, `ba_jobs.json` | nein (.gitignore) | letzte Live-Antwort |

Die Vollfixtures wiegen zusammen ueber 150 MB und gehoeren nicht ins Repo.
`load_fixture()` faellt automatisch auf das Sample zurueck, wenn die
Vollfixture fehlt - ein frischer Clone kann also sofort `make demo` fahren.

### Warum die Samples geschichtet sind, nicht zufaellig

Die interessanten Pfade sind selten. Ein Zufallsschnitt aus 17.185 Releases
enthaelt mit hoher Wahrscheinlichkeit keinen auslaufenden Rahmenvertrag
(7 Treffer in 8 Wochen) und keinen unterlegenen Bieter (1 Treffer in 12
Monaten). `make demo` haette dann genau einen Signaltyp gezeigt und den
Rest der Pipeline unbewiesen gelassen.

`make_samples.py` zieht deshalb je Pfad eine Mindestzahl:

```
zuschlag_mit_gewinner   60    awards[].suppliers benannt
alleinbieter            60    genau ein tenderer, kein supplier
mehrbieter              40    mehrere tenderer
rahmenvertrag_ablauf    40    Los mit Vertragsende im Nachfassfenster
konsortium              15    Bietergemeinschaft im Namensfeld
rest                    60
```

Ergebnis: Die Offline-Demo feuert dieselben vier Signaltypen wie der
Live-Lauf.

### Getestet wie ein frischer Clone

Mit beiseitegeschobenen Vollfixtures, also nur gegen die Samples:

```
Lauf 1   neu 417   geaendert 4   unveraendert   1
Lauf 2   neu   0   geaendert 6   unveraendert 233
```
