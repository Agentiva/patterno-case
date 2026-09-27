# Patterno Case — IT-Systemhäuser mit öffentlichem Vergabegeschäft

Longlist und Signal-Engine auf amtlichen Vergabedaten. Kein Scraper, keine
Lizenzkosten, jede Zeile mit Beleg-URL.

```bash
pip install -r requirements.txt
make longlist                      # Aufgabe 1: 12 Monate Vergabedaten → Longlist
make run                           # Aufgabe 2: Signale gegen die echten APIs
make demo                          # offline, 2× hintereinander = 0 neue Zeilen
make domains                       # Domains aus der Quelle + Tiers nachziehen
make vollstaendigkeit              # Fang-Wiederfang: wie viel fehlt?
make package                       # Abgabedateien + Stichproben-Audit
```

## Die Entscheidung, aus der alles folgt

Nicht ein Firmenverzeichnis auf Public-Sector-Bezug filtern, sondern
**Vergabedaten auf Systemhaus-Eignung**. Verzeichnis-first liefert „könnte
relevant sein", Vergabedaten-first „hat am 15.09.2026 den Zuschlag bekommen,
hier ist das PDF". Teilnahme ist ein Faktum, kein Attribut.

## Ergebnis

12 Monate Datenservice Öffentlicher Einkauf (CC0): **283.597 Bekanntmachungen
→ 17.185 mit IT-CPV-Dominanz → 2.458 Unternehmen mit Beleg.**

| | |
|---|---|
| **Tier** (nur aus Vergabedaten: Häufigkeit, Aktualität, Breite, Belegart) | A 228 · B 1.249 · C 981 |
| **Domain** aus der amtlichen Quelle, mit Prüfschicht | 1.487 / 2.458 · **60,5 %**, Quelle und Konfidenz je Zeile |
| **Signale** 8 Wochen, 3 Quellen | 629 Accounts, 172 über Schwelle 40 |
| **Idempotenz** live | Lauf 1: 1.850 neu · Läufe 2–4: **0 neu, 0 geändert** |
| **Eigenes Audit** 30 Zufallszeilen | 24/24 prüfbare Belege erreichbar · 5× TED nicht prüfbar · 2 Zeilen ohne Longlist-Bezug |
| **Kontakte** | 69 Personen an 30 Accounts, E-Mail-Status je Zeile mit Quelle |
| **Abdeckung** Fang-Wiederfang, 12 Monatsgelegenheiten | Population ≥ 6.798 → **≤ 36 %** abgedeckt ([Methode](docs/vollstaendigkeit.md)) |

ICP-Annahmen, Ausschlusslisten und Gewichte stehen an **einer** Stelle:
`src/config.py`.

## Was funktioniert

- **CPV-Dominanzprüfung** (≥ 50 % IT-Lose). Vorher zog eine
  Handwerkskammer-Rahmenvereinbarung jeden Werkzeuglieferanten in die Liste.
- **Vier Belegarten statt einer.** In 4.309 Bekanntmachungen ohne
  Gewinnerangabe hat **3.987 mal genau ein Bieter** geboten — der hat gewonnen,
  nur anders gemappt. Pauschal „hat verloren": 1.727 erfundene Eigenschaften.
- **Getrennte Fehlerkübel.** Vergabestellen, Job-Signale ohne IT-Beleg und
  unsichere Auflösungen (85) landen je in eigenen Dateien — nie im Outbound.
  TED-Belege sind maschinell nicht prüfbar (HTTP 202) und werden als eigene
  Kategorie geführt.
- **Jeder Lauf meldet, welcher Signaltyp nicht gefeuert hat.**
- **Domain aus derselben Bekanntmachung wie der Beleg.** eForms führt einen
  `contactPoint` je Bieterpartei: 75,3 % roh, ohne einen Credit. Nach der
  Prüfschicht 60,5 % — die Differenz sind Fremdadressen (**29 Firmen tragen die
  E-Mail der Beschaffungsstelle Hamburg**), Konzerndomains und kaputte Felder.
  Clay bestätigt unabhängig 32 von 33
  ([waterfalls.md](docs/waterfalls.md)).

## Was nicht funktioniert

- **Unterlegene Bieter sind unsichtbar.** In 438 von 441 Fällen ist die
  Bieterliste die Gewinnerliste. Wer zwölfmal bietet und nie gewinnt, steht
  einmal drin.
- **Drei Signalquellen statt vier.** Vergabekammer-Entscheidungen sind
  vermessen ([Prompt](docs/clay_claygent_vergabekammer.md)), nicht gebaut.
- **`offene_ausschreibung_im_profil` feuert, liefert keine Accounts.** Frist
  aus dem eForms-XML (BT-131), **196 offene Verfahren** — aber eine laufende
  Ausschreibung nennt den *Auftraggeber*, nicht den Bieter. Join fehlt.
- **Kein Systemhaus-Klassifikator.** CPV belegt Teilnahme, nicht
  Geschäftsmodell: Von 20 Stichproben stehen 18 in Tier A, **6 gehören nicht
  ins ICP** (Siemens Gebäudeautomation, Sensorhersteller,
  Personaldienstleister). [Prompt](docs/clay_sculptor_systemhaus.md) steht,
  gelaufen ist er nicht.
- **971 Firmen ohne Domain (39,5 %).** 631 davon führt die Quelle nicht, der
  Rest ist bewusst offen gelassen statt geraten.
- **Höchstens ein Drittel abgedeckt.** 73 % der Firmen tauchen in genau
  *einem* von zwölf Monaten auf — unterabgetastet. Daneben der größere blinde
  Fleck: ~90 % der öffentlichen Aufträge sind unterschwellig, im Korpus liegen
  77 % der bewerteten Verfahren **darüber**. Dort arbeitet der ICP-Korridor.

## Die Fehler

Sechs Stück, jeder hat seinen eigenen Selbsttest bestanden — ein HTTP-200, ein
erfolgreicher Lauf, eine plausible Zahl. Der teuerste: Ich habe den
Domain-Waterfall bei Apollo begonnen, ohne zu prüfen, ob die Vergabedaten die
Domain selbst führen. Sie führen sie — kostenlos, neben dem Beleg. Ursachen und
Gegenmaßnahmen: [fehler.md](docs/fehler.md).

**Kosten:** Quellen 0 €, Anreicherung ≈ **6,3 Apollo-Credits je
qualifiziertem Lead** ([operating_model.md](docs/operating_model.md)).

**Zeitaufwand:** Quellen 25 · Longlist 55 · Signal-Engine 45 · Fehlersuche an
echten Daten 40 · Enrichment und Audit 30 · Doku 25 Minuten.

## Die nächsten zwei Wochen

1. **Unterschwellen-Ingestion für drei Bundesländer** — Patternos eigener Moat
   und die größte gemessene Lücke der Liste.
2. **Verlierer-Inferenz** über wiederholte Teilnahmemuster.
3. **Rahmenvertrags-Ablauf als produktisiertes Signal.**
4. **Attio-Sync plus Montags-Digest.**
5. **Eval-Harness mit gelabeltem Ground-Truth-Set** — 50 handgeprüfte
   Systemhäuser, um die Abdeckung zu *messen* statt zu schätzen.

---

**Abgabe** — `data/`: `longlist_markt.csv` (1c) · `enrichment_markt.csv` (1d)
· `longlist_signale.csv` (2c) · `enrichment_signale.csv` (2d) ·
`validation_sample.csv` · `score_trace.csv` · `domains_amtlich.csv` ·
`vollstaendigkeit.csv`. Nicht fürs
Outbound: `offene_verfahren.csv`, `job_signale_ohne_icp_beleg.csv`.
**`docs/`** — [signals.md](docs/signals.md) ·
[waterfalls.md](docs/waterfalls.md) · [tiering.md](docs/tiering.md) ·
[vollstaendigkeit.md](docs/vollstaendigkeit.md) ·
[operating_model.md](docs/operating_model.md) ·
[apollo_filter.md](docs/apollo_filter.md) ·
[clay_sculptor_systemhaus.md](docs/clay_sculptor_systemhaus.md) ·
[fehler.md](docs/fehler.md) ·
[playbook_it_systemhaeuser.md](docs/playbook_it_systemhaeuser.md).
