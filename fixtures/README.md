# Fixtures

Gespeicherte API-Antworten, damit `make demo` **ohne Netzzugang und ohne
API-Keys** laeuft. Das ist fuer eine Live-Demo wichtig, in der man sich nicht
auf fremde APIs verlassen will.

Die Daten sind **echt**, nicht synthetisch. Bis zum 23.09.2026 lagen hier
generierte Testdaten, weil die Zielsysteme aus der Bauumgebung nicht
erreichbar waren; seit dem ersten Live-Lauf sind es echte Antworten. Das
Generierungsskript ist entfernt - in einem Repo, dessen Prinzip "jede Zeile
mit Beleg" ist, haben erfundene Firmennamen nichts verloren.

Schema der Quellen:
- `ba_jobs.json` -> `JobSearchResponse` aus https://github.com/bundesAPI/jobsuche-api (openapi.yaml v2.1.0)
- `vergabe_dovs.json` -> OCDS-Releases, `releases[].awards[].suppliers[]`

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

`git clone` in ein leeres Verzeichnis, danach nur gegen die eingecheckten
Samples - also genau das, was ein Pruefer erlebt (27.09.2026):

```
Lauf 1   neu 458   geaendert 0   unveraendert   0
Lauf 2   neu   0   geaendert 0   unveraendert 245
```

Eine aeltere Fassung dieser Datei nannte hier `geaendert 4` und `geaendert 6`.
Das waren keine echten Korrekturen, sondern Korrekturbekanntmachungen
desselben Verfahrens, die sich einen Schluessel teilten und sich in JEDEM
Lauf neu ueberschrieben. Der Fehler ist behoben (siehe docs/fehler.md, Nr. 5);
die Zahlen oben sind nachgemessen.
