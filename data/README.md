# Was in diesem Ordner liegt

Vier Dateien sind die Abgabe. Der Rest ist entweder ihr Beleg, ihr Eingang
oder ein Fehlerkübel — und keine davon gehört ins Outbound.

## Die Abgabe

| Datei | Case | Zeilen | Inhalt |
|---|---|---|---|
| `longlist_markt.csv` | **1c** | 2.458 | Firmenname, Domain, Tier, Beleg-URL |
| `enrichment_markt.csv` | **1d** | 48 Kontakte / 24 Accounts | Person, Rolle, LinkedIn, E-Mail + Status, Telefon |
| `longlist_signale.csv` | **2c** | 629 | Signaltyp, Datum, Quell-URL, Score, `why_now` |
| `enrichment_signale.csv` | **2d** | 21 Kontakte / 10 Accounts | wie 1d, plus „Why now" je Account |

## Der Beleg dahinter

Diese Dateien behauptet niemand — sie sind nachrechenbar.

| Datei | Wofür |
|---|---|
| `score_trace.csv` | Score-Zerlegung je Account als JSON. Jeder Score in `longlist_signale.csv` ist damit aufklappbar statt Blackbox. Join über `company_id`. |
| `validation_sample.csv` | Mein **eigenes** Audit: 30 Zufallszeilen, Beleg-URL live geprüft auf Status, Content-Type und Größe. |
| `domains_amtlich.csv` | Domain-Waterfall Stufe 0: je Zeile Kandidat, Quelle, Konfidenz und Befund. Zeigt auch die 106 verworfenen Fremdadressen. |
| `vollstaendigkeit.csv` | Fang-Wiederfang, vier Schätzer. Antwort auf „wie vollständig ist die Liste". |
| `vk_quellenaudit.csv` | Quellenaudit der **nicht gebauten** vierten Signalquelle. Messung statt Behauptung. |

## Eingang — wird gelesen, nicht erzeugt

| Datei | Wer liest sie |
|---|---|
| `clay_markt_export.csv`, `clay_signale_export.csv` | `make package` — die Kontakte aus Clay |
| `enrichment_kontakte_tierA.csv` | `make package` — liefert die `verifiziert_apollo`-Status |
| `eforms_fristen.json` | `src/sources/eforms.py` — Cache der Angebotsfristen (BT-131), 1.681 Einträge. Ohne ihn holt jeder Lauf hunderte XML-Dokumente neu. |
| `apollo_cache/` | `src/enrich/apollo.py` — die Antworten des Apollo-Laufs vom 23.09. Macht ihn wiederholbar, ohne erneut Credits auszugeben. |

## Fehlerkübel — bewusst getrennt, **nie** ins Outbound

Was nicht sauber ist, wird nicht gelöscht, sondern sichtbar in eine eigene
Datei geschrieben. Gelöschte Zeilen kann niemand prüfen.

| Datei | Zeilen | Warum separat |
|---|---|---|
| `offene_verfahren.csv` | 203 | Laufende Ausschreibungen mit Frist. Nennen den **Auftraggeber**, nicht den Bieter → Join-Input |
| `job_signale_ohne_icp_beleg.csv` | 34 | Bid-Rolle ausgeschrieben, aber kein IT-Vergabebeleg → ICP vor Ansprache prüfen |
| `clay_domain_todo.csv` | 971 | Die Zeilen ohne Domain, fertig für den Clay-Import (Waterfall Stufe 2) |

Dazu die Review-Queue in `state.sqlite`: 85 Firmenauflösungen unter
Confidence 0,70. Die werden **nicht geraten**.

## Nicht im Repo

`state.sqlite` steht in `.gitignore`. Sie ist der Delta-Store — er entscheidet,
was „neu seit dem letzten Lauf" heißt, und entsteht beim ersten `make demo`
von selbst.

---

**Achtung beim Nachbauen:** `make demo`, `make run` und `make export`
überschreiben `longlist_signale.csv`, `offene_verfahren.csv`,
`score_trace.csv` und `job_signale_ohne_icp_beleg.csv`. Wer die abgegebenen
Stände zurückhaben will:

```bash
git checkout data/
```
