# Betriebsmodell: Clay, Supabase, Attio — und was Kosten pro Lead wirklich heißt

## Aufgabenteilung

Die Pipeline in diesem Repo ist kein Clay-Ersatz. Sie macht den Teil, den Clay
nicht gut macht, und übergibt dann.

| Schritt | Wo | Warum dort |
|---|---|---|
| Vergabedaten holen, CPV prüfen, Firmen extrahieren | **Python (dieses Repo)** | 283.597 Bekanntmachungen pro Jahr, ZIP-Entpacken, CPV-Dominanzprüfung — in Clay wäre das pro Zeile ein HTTP-Call und damit teuer und langsam |
| Delta-Erkennung, Signal-Historie | **Supabase (Postgres)** | Ein Signal muss wiederfindbar sein: „haben wir das letzte Woche schon gemeldet?" Das ist eine Datenbankfrage, keine Tabellenzeile |
| Domain-Resolution, Personensuche, E-Mail | **Clay** | Genau dafür ist Clay gebaut: Waterfalls über mehrere Anbieter, ohne dass wir pro Anbieter einen Client schreiben |
| Account- und Kontaktstamm, Sequenz-Trigger | **Attio** | CRM ist das System of Record. Die Pipeline schreibt hinein, liest aber nicht daraus |

Die Schnittstelle zwischen den vieren ist bewusst eine einzige Tabelle:
`signals` in Supabase. Jede Zeile trägt `signal_id`, `content_hash`,
`first_seen_run`, `last_seen_run`. Clay zieht daraus per View nur, was seit
dem letzten Lauf neu oder geändert ist — deshalb kostet ein wöchentlicher
Lauf auch in Woche 40 nicht mehr als in Woche 1.

## Der Datenfluss in einem Satz pro Pfeil

```
DÖE / TED / BA-Jobsuche
   │  (Python, wöchentlich, idempotent)
   ▼
signals  ──►  accounts  ──►  scores          [Supabase]
   │                            │
   │                            │  nur Accounts über Schwelle
   │                            ▼
   │                      Clay-Tabelle  ──►  Domain-Waterfall
   │                                    ──►  Persona-Suche (Apollo-Filter, siehe apollo_filter.md)
   │                                    ──►  E-Mail + Status
   │                                          │
   ▼                                          ▼
offene_verfahren (Join-Input)            Attio: Account + Kontakt + „Why now"
```

Ein Punkt daran ist nicht kosmetisch: **Angereichert wird erst nach dem
Scoring.** Signale sind kostenlos, Anreicherung nicht. Wer zuerst anreichert
und dann filtert, bezahlt den gesamten Longtail mit.

## Kosten pro qualifiziertem Lead

Erst die Definition, sonst ist die Zahl wertlos.

> **Qualifizierter Lead** = ein Account der Longlist, für den (a) die Teilnahme
> an öffentlichen Vergaben mit URL belegt ist, (b) ein Signal aus den letzten
> 8 Wochen vorliegt, (c) eine verifizierte Domain existiert und (d) mindestens
> ein Kontakt mit E-Mail-Status `verified` gefunden wurde.

Alles andere ist eine Zeile, kein Lead.

### Was tatsächlich Geld kostet

| Posten | Preis | Grundlage |
|---|---|---|
| DÖE, TED, BA-Jobsuche | **0 €** | CC0 bzw. offene APIs, keine Lizenz, kein Scraper |
| Domain-Resolution Stufe 1–3 | **0 €** | Apollo Organizations Lookup ist creditfrei; Impressum ist ein GET |
| Firmographics | 1 Credit je Treffer | Apollo Bulk Organization Enrichment |
| Personensuche | 1 Credit je Suche | Apollo People Search, bis zu 3 Personas je Account |
| Kontakt-Match inkl. E-Mail | 1 Credit je Treffer | Apollo People Bulk Match |
| Rechenzeit | ~3 min/Woche | ein Container, kein Cluster |

### Gemessene Ausbeute je Stufe

Die Quoten stammen aus dem Lauf vom 23.09.2026, nicht aus einer Schätzung —
Details und Stichprobengrößen in [waterfalls.md](waterfalls.md).

| Stufe | Quote | Stichprobe |
|---|---|---|
| Firmographics je Domain | 100 % | 11/11 |
| Kontakt-Match je gesuchter Person | 100 % | 15/15 |
| E-Mail-Status `verified` je Kontakt | 87 % | 13/15 |

Die Domain-Resolution ist die Engstelle, und hier steht bewusst keine
einzelne Zahl: Die erste Messung ergab 77 %, war aber an bekannten Marken
gemessen und im Longtail zu zwei Dritteln falsch. Ohne belastbare Messung
an einer Zufallsstichprobe rechne ich mit **60 %** und schreibe dazu, dass
es eine Annahme ist.

### Die Rechnung

Für 100 Accounts über der Score-Schwelle, 3 Personas je Account:

```
Domain-Resolution      100 Accounts ×  0 Credits  =   0
Firmographics           60 Domains  ×  1 Credit   =  60
Personensuche           60 Domains  ×  3 Suchen   = 180
Kontakt-Match          ~90 Treffer  ×  1 Credit   =  90
                                                   ─────
                                                    330 Credits
```

Daraus werden rund **52 qualifizierte Leads** (60 Domains × 87 % E-Mail-Quote,
abzüglich Accounts ohne Persona-Treffer).

**≈ 6,3 Credits je qualifiziertem Lead.**

In Euro hängt das am Apollo-Tarif; bei den üblichen Bündelpreisen liegt ein
Credit im niedrigen Cent-Bereich, der Lead damit **deutlich unter 1 €** an
Datenkosten. Der ehrliche Teil: Die Datenkosten sind hier nicht der Engpass.
Der Engpass ist die Review-Queue — jede Domain, die keine Stufe besteht,
kostet ein paar Minuten Menschenzeit, und die ist teurer als jedes Credit.
Deshalb ist die Verbesserung der Domain-Resolution der einzige Hebel, der
die Stückkosten wirklich bewegt.

### Was die Zahl nicht enthält

- Arbeitszeit für Review und Kalibrierung
- Attio- und Clay-Lizenzen (laufen ohnehin, kein Grenzkostenposten)
- Zustellbarkeit: Ein `verified`-Status ist kein Öffnungsereignis

## Wiederanlauf und Betrieb

### Zwei Kadenzen, nicht eine

Gebaut als GitHub Action (`.github/workflows/pipeline.yml`), ohne ein einziges
Secret — die drei Signalquellen und der Datenservice brauchen keinen API-Key.

| | Was läuft | Kosten |
|---|---|---|
| **montags 05:12 UTC** | Signale, Tier-Alterung, Abgabedateien | ~50 s, ~100 MB |
| **am 3. des Monats** | Longlist komplett neu, Domains neu auflösen | ~1,3 GB |

**Warum Aufgabe 1 nicht wöchentlich läuft.** Der Datenservice liefert
Monatspakete (`pubMonth`). Elf der zwölf Monate im Korpus sind eingefroren, nur
der laufende wächst. Ein Wochenlauf lädt also 1,3 GB, um einen Monat zu
aktualisieren.

**Warum sie trotzdem nicht nur quartalsweise reicht.** Ein Tier-Kriterium
wandert täglich: die Aktualität des Belegs. Gemessen zwischen dem 24. und dem
27.09.2026 — drei Tage — wanderten **22 Firmen ein Tier abwärts** (A 233 →
228). Das rechnet `retier` ohne einen Download nach, und genau deshalb läuft es
im Wochenjob mit. Wer nur quartalsweise einstuft, spricht Firmen mit einem
Beleg an, der inzwischen ein halbes Jahr alt ist.

**Warum der 3. und nicht der 1.** Am Monatsersten ist das Paket des Vormonats
noch nicht vollständig. Ohne zwei Tage Puffer baut der Lauf eine Liste aus elf
Monaten und meldet trotzdem Erfolg.

**Die Schwachstelle, die ich nicht gelöst habe.** Der Delta-Store liegt im
Actions-Cache, und GitHub räumt Caches nach sieben Tagen ohne Zugriff weg — ein
Wochenrhythmus liegt genau auf dieser Kante. Fällt der Cache weg, ist das
Ergebnis nicht falsch, aber ein Lauf meldet einmalig alles als „neu". Wer das
ins Outbound gibt, spricht Firmen doppelt an. Belastbar wäre der Store in einem
Bucket oder in Supabase; solange er im Cache liegt, gilt: dem ersten Lauf nach
einer Lücke im Laufprotokoll nicht blind glauben.

- **Zeitplan:** wöchentlich, montags früh. Vergabebekanntmachungen erscheinen
  über die Woche verteilt; montags ist der Vorlauf auf die Frist am größten.
- **Idempotenz:** Ein zweiter Lauf ohne neue Daten gibt 0 Zeilen aus. Das ist
  getestet, nicht behauptet — `make demo` zweimal hintereinander.
- **Überlappungsfenster:** 14 Tage. Nachträglich korrigierte Bekanntmachungen
  werden dadurch erneut gelesen und als `changed` erkannt.
- **Beobachtbarkeit:** Jede Quelle schreibt eine Zeile in `runs` mit
  gelesenen/neuen/geänderten Zeilen und Fehlertext. `python3 -m src.cli runlog`
  zeigt das Protokoll.
- **Fehlerverhalten:** Fällt eine Quelle aus, beendet sich der Lauf mit
  Exit-Code 1 und benennt die Quelle. Ein Totalausfall sieht in den Zahlen
  sonst exakt aus wie ein sauberer zweiter Lauf — überall Null.
