# Patterno Case — IT-Systemhäuser mit öffentlichem Vergabegeschäft

Longlist und Signal-Engine auf amtlichen Vergabedaten. Kein Scraper, keine
Lizenzkosten, jede Zeile mit Beleg-URL.

```bash
pip install -r requirements.txt
make demo                          # offline, 2× hintereinander = 0 neue Zeilen
make run                           # gegen die echten APIs
make retier FROM=clay-export.csv   # Domains/Kontaktdaten einspielen
make package                       # Abgabedateien + Stichproben-Audit
```

## Die Entscheidung, aus der alles folgt

Die Liste entsteht nicht aus einem Firmenverzeichnis, das ich auf
Public-Sector-Bezug filtere, sondern aus **Vergabedaten, die ich auf
Systemhaus-Eignung filtere**. Verzeichnis-first liefert „könnte relevant
sein". Vergabedaten-first liefert „hat am 15.09.2026 den Zuschlag bekommen,
hier ist das PDF". Teilnahme ist ein Faktum, kein Attribut.

## Ergebnis

12 Monate Datenservice Öffentlicher Einkauf (CC0): **283.597 Bekanntmachungen
→ 17.185 mit IT-CPV-Dominanz → 2.468 Unternehmen mit Beleg.**

| | |
|---|---|
| **Tier** (nur aus Vergabedaten: Häufigkeit, Aktualität, Breite, Belegart) | A 235 · B 1.267 · C 966 |
| **Signale** 8 Wochen, 3 Quellen | 653 Accounts, 202 über Schwelle 40 |
| **Idempotenz** live | Lauf 1: 1.694 neu · Lauf 2: **0 neu** |
| **Eigenes Audit** 30 Zufallszeilen | 25/25 prüfbare Belege erreichbar, 0 tot |
| **Kontakte** | 69 Personen an 30 Accounts, E-Mail-Status je Zeile mit Quelle |

ICP-Annahmen, Ausschlusslisten und Gewichte stehen an **einer** Stelle:
`src/config.py`.

## Was funktioniert

- **CPV-Dominanzprüfung** (≥ 50 % IT-Lose). Vorher zog eine einzige
  Handwerkskammer-Rahmenvereinbarung jeden Werkzeuglieferanten in die Liste.
- **Vier Belegarten statt einer.** In 4.309 Bekanntmachungen ohne
  Gewinnerangabe hat **3.987 mal genau ein Bieter** geboten — der hat gewonnen,
  nur anders gemappt. Pauschal als „hat verloren" geführt wären das 1.727
  erfundene Eigenschaften mit amtlicher URL daneben.
- **Getrennte Fehlerkübel.** Vergabestellen, Job-Signale ohne IT-Beleg und
  unsichere Auflösungen (87) landen je in einer eigenen Datei — nie im Outbound.
- **Jeder Lauf meldet, welcher Signaltyp nicht gefeuert hat.**

## Was nicht funktioniert

- **Unterlegene Bieter sind unsichtbar.** In 438 von 441 Fällen ist die
  Bieterliste die Gewinnerliste. Das Systemhaus, das zwölfmal bietet und nie
  gewinnt, steht einmal in zwölf Monaten drin.
- **Drei Signalquellen statt der geforderten vier.**
  Vergabekammer-Entscheidungen sind spezifiziert, nicht gebaut.
- **Zwei Signaltypen feuern nicht:** `offene_ausschreibung_im_profil` (das
  OCDS-Mapping führt keine Angebotsfrist) und `nachpruefung_vergabekammer`.
- **Kein Systemhaus-Klassifikator.** CPV belegt Teilnahme, nicht
  Geschäftsmodell — unter den Top-Signalen stehen Siemens (Gebäudeautomation)
  und ein Sensorhersteller. Sichtprüfung vor Versand ist Pflicht.
- **Keine Vollständigkeitsschätzung.** Dafür fehlt eine zweite, *unabhängige*
  Quelle; Vergabedaten und Branchenrankings überrepräsentieren beide große
  Firmen. Lieber keine Zahl als eine unbelastbare.
- **TED-Belege maschinell nicht prüfbar** — HTTP 202 auf jede serverseitige
  Anfrage. Der Prüfer weist sie als dritte Kategorie aus, nicht als „ok".

## Vier Fehler, die jeder erfolgreich aussah

1. **Beleg-URL erfunden.** `/ui/de/notice/<ocid>` ist eine SPA: HTTP 200 auf
   *jede* URL, dieselbe 1.309-Byte-Hülle, 404 erst im Browser. Ein
   Statuscheck hätte den Fehler *bestätigt*.
2. **Das wertvollste Signal feuerte nie.** `rahmenvertrag_laeuft_aus` las
   `awards[].contractPeriod` — 0 Treffer. Das Vertragsende hängt am Los: 15.716.
3. **TED schnitt stumm ab.** 2.000 von 2.435 Notices, Lauf meldete Erfolg; im
   Folgelauf galten 131 als „neu". Jetzt Abgleich gegen `totalNoticeCount`.
4. **Trefferquote ohne Stichprobenangabe ist wertlos.** Domain-Resolution maß
   77 % — an bekannten Marken. Im Longtail 8 von 12 falsch, darunter
   `eominnesota.org` für die EOMI AG aus Hamburg.

**Kosten:** Quellen 0 €, Anreicherung ≈ **6,3 Apollo-Credits je
qualifiziertem Lead** ([operating_model.md](docs/operating_model.md)). Der
Treiber ist nicht das Credit, sondern jede Domain in der Review-Queue.

**Zeitaufwand:** Quellenprüfung 25 · Longlist 55 · Signal-Engine 45 ·
Fehlersuche an echten Daten 40 · Enrichment und Audit 30 · Doku 25 Minuten.

## Die nächsten zwei Wochen

1. **Unterschwellen-Ingestion für drei Bundesländer** — das ist Patternos
   eigener Moat.
2. **Verlierer-Inferenz** über wiederholte Teilnahmemuster.
3. **Rahmenvertrags-Ablauf als produktisiertes Signal.**
4. **Attio-Sync plus Montags-Digest.**
5. **Eval-Harness mit gelabeltem Ground-Truth-Set** zur Messung von Präzision
   über Zeit — hier gehört auch die Vollständigkeitsschätzung hin.

---

**Abgabe** — `data/`: `longlist_markt.csv` (1c) · `enrichment_markt.csv` (1d,
48 Kontakte/24 Accounts) · `longlist_signale.csv` (2c) ·
`enrichment_signale.csv` (2d, 21/10) · `validation_sample.csv` (eigenes Audit)
· `score_trace.csv`. Nicht fürs Outbound: `offene_verfahren.csv`,
`job_signale_ohne_icp_beleg.csv`.
**`docs/`**: [signals.md](docs/signals.md) (Quellen, Delta, Scoring) ·
[operating_model.md](docs/operating_model.md) ·
[waterfalls.md](docs/waterfalls.md) · [tiering.md](docs/tiering.md) ·
[apollo_filter.md](docs/apollo_filter.md) ·
[playbook_it_systemhaeuser.md](docs/playbook_it_systemhaeuser.md).
