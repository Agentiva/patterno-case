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

Nicht ein Firmenverzeichnis auf Public-Sector-Bezug filtern, sondern
**Vergabedaten auf Systemhaus-Eignung**. Verzeichnis-first liefert „könnte
relevant sein". Vergabedaten-first liefert „hat am 15.09.2026 den Zuschlag
bekommen, hier ist das PDF". Teilnahme ist ein Faktum, kein Attribut.

## Ergebnis

12 Monate Datenservice Öffentlicher Einkauf (CC0): **283.597 Bekanntmachungen
→ 17.185 mit IT-CPV-Dominanz → 2.458 Unternehmen mit Beleg.**

| | |
|---|---|
| **Tier** (nur aus Vergabedaten: Häufigkeit, Aktualität, Breite, Belegart) | A 233 · B 1.261 · C 964 |
| **Signale** 8 Wochen, 3 Quellen | 651 Accounts, 200 über Schwelle 40 |
| **Idempotenz** live | Lauf 1: 1.850 neu · Läufe 2–4: **0 neu, 0 geändert** |
| **Eigenes Audit** 30 Zufallszeilen | 24/24 prüfbare Belege erreichbar · 5× TED nicht prüfbar · 2 Zeilen ohne Longlist-Bezug |
| **Kontakte** | 69 Personen an 30 Accounts, E-Mail-Status je Zeile mit Quelle |

ICP-Annahmen, Ausschlusslisten und Gewichte stehen an **einer** Stelle:
`src/config.py`.

## Was funktioniert

- **CPV-Dominanzprüfung** (≥ 50 % IT-Lose). Vorher zog eine einzige
  Handwerkskammer-Rahmenvereinbarung jeden Werkzeuglieferanten in die Liste.
- **Vier Belegarten statt einer.** In 4.309 Bekanntmachungen ohne
  Gewinnerangabe hat **3.987 mal genau ein Bieter** geboten — der hat gewonnen,
  nur anders gemappt. Pauschal als „hat verloren" geführt: 1.727 erfundene
  Eigenschaften mit amtlicher URL daneben.
- **Getrennte Fehlerkübel.** Vergabestellen, Job-Signale ohne IT-Beleg und
  unsichere Auflösungen (85) landen je in einer eigenen Datei — nie im Outbound.
- **Jeder Lauf meldet, welcher Signaltyp nicht gefeuert hat.**

## Was nicht funktioniert

- **Unterlegene Bieter sind unsichtbar.** In 438 von 441 Fällen ist die
  Bieterliste die Gewinnerliste. Das Systemhaus, das zwölfmal bietet und nie
  gewinnt, steht einmal in zwölf Monaten drin.
- **Drei Signalquellen statt vier.** Vergabekammer-Entscheidungen sind
  vermessen ([Audit](docs/signals.md),
  [Prompt](docs/clay_claygent_vergabekammer.md)), nicht gebaut.
- **`offene_ausschreibung_im_profil` feuert, liefert keine Accounts.** Die
  Frist steht nicht im OCDS-JSON, sondern im eForms-XML (BT-131) — jetzt
  gelesen, **196 offene Verfahren**. Nur nennt eine laufende Ausschreibung den
  *Auftraggeber*, nicht den Bieter. Der Join gegen Longlist 1 fehlt.
- **Kein Systemhaus-Klassifikator.** CPV belegt Teilnahme, nicht
  Geschäftsmodell: Von 20 Stichproben stehen 18 in Tier A, **6 davon gehören
  nicht ins ICP** (Siemens Gebäudeautomation, Sensorhersteller, ein
  Personaldienstleister). [Prompt](docs/clay_sculptor_systemhaus.md) steht,
  gelaufen ist er nicht.
- **Keine Vollständigkeitsschätzung.** Dafür fehlt eine zweite, *unabhängige*
  Quelle; Vergabedaten und Branchenrankings überrepräsentieren beide große
  Firmen.
- **TED-Belege maschinell nicht prüfbar** (HTTP 202). Der Prüfer weist sie als
  dritte Kategorie aus, nicht als „ok".

## Fünf Fehler, die jeder erfolgreich aussah

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
5. **Das Delta log dauerhaft.** Korrekturbekanntmachungen desselben
   Verfahrens teilten sich einen Schlüssel: 25 Zeilen galten in *jedem* Lauf
   als „geändert". Hier stand dazu „echte Korrekturen im
   Überlappungsfenster" — die Erklärung, die zur Zahl passte. Widerlegt von
   vier identischen Läufen hintereinander.

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

**Abgabe** — `data/`: `longlist_markt.csv` (1c) · `enrichment_markt.csv`
(1d, 48/24) · `longlist_signale.csv` (2c) · `enrichment_signale.csv` (2d,
21/10) · `validation_sample.csv` · `score_trace.csv`. Nicht fürs Outbound:
`offene_verfahren.csv`, `job_signale_ohne_icp_beleg.csv`.
**`docs/`**: [signals.md](docs/signals.md) ·
[operating_model.md](docs/operating_model.md) ·
[waterfalls.md](docs/waterfalls.md) · [tiering.md](docs/tiering.md) ·
[apollo_filter.md](docs/apollo_filter.md) ·
[clay_sculptor_systemhaus.md](docs/clay_sculptor_systemhaus.md) ·
[playbook_it_systemhaeuser.md](docs/playbook_it_systemhaeuser.md).
