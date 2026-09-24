# Patterno Case — IT-Systemhäuser mit öffentlichem Vergabegeschäft

Longlist und Signal-Engine, gebaut auf amtlichen Vergabedaten. Kein Scraper,
keine Lizenzkosten, jede Zeile mit Beleg-URL.

```bash
pip install -r requirements.txt
make demo          # offline gegen Fixtures, zweimal hintereinander = 0 neue Zeilen
make run           # gegen die echten APIs
python3 -m src.cli longlist --live --months 12
make retier FROM=clay-export.csv    # Domain/Mitarbeiterzahl einspielen
python3 -m src.verify_proofs --sample 30
```

---

## Die eine Entscheidung, aus der alles folgt

Die Aufgabe fragt: *Wie belegst du **mit Daten**, dass ein Unternehmen an
öffentlichen Vergaben teilnimmt, statt es nur anzunehmen?*

Deshalb baue ich die Liste nicht aus einem Firmenverzeichnis, das ich auf
Public-Sector-Bezug filtere, sondern aus **Vergabedaten, die ich auf
Systemhaus-Eignung filtere**. Verzeichnis-first liefert „könnte relevant
sein". Vergabedaten-first liefert „hat am 15.09.2026 den Zuschlag für
den Konzernrahmenvertrag bekommen, hier ist das PDF".

Teilnahme ist damit ein Faktum mit Datum und Quelle, kein Attribut.

## ICP-Annahmen

Alle fachlichen Annahmen stehen in `src/config.py` — an einer Stelle, damit
sie im Review geändert werden können, ohne Code zu lesen.

| Annahme | Wert | Begründung |
|---|---|---|
| Branche | IT-Systemhaus / IT-Dienstleister | CPV 48, 72, 302, 5031, 5032, 5161, 642 |
| **CPV-Dominanz** | ≥ 50 % der Lose IT | ohne das zieht eine Handwerkskammer-Sammelvergabe jeden Werkzeuglieferanten mit herein |
| Größe | 50–2.000 MA, Sweet Spot 50–500 | darunter kein eigener Angebotsprozess, darüber eigene Bid-Abteilung |
| Region | Deutschland | Zuschlag an einen deutschen Rechtsträger |
| **Ausgeschlossen** | Inhouse-Dienstleister (Dataport, ITZBund, AKDB, Komm.ONE …), Vergabeportale, Vergaberechtskanzleien, Distributoren, Personaldienstleister | Auftraggeberseite oder Wettbewerber — in jeder „Vergabe"-Suche der häufigste Fehltreffer |

**Buying Center:** Champion = Bid-/Tender-/Angebotsmanagement · Economic Buyer
= Geschäftsführung, Vertriebsleitung, Leitung Public Sector · Nutzer =
KAM Public Sector, Pre-Sales, Projektleitung. Die konkreten Titel stammen aus
einem echten Apollo-Lauf, nicht aus einer Wunschliste →
[docs/apollo_filter.md](docs/apollo_filter.md).

## Aufgabe 1 — Longlist

**Quelle:** Datenservice Öffentlicher Einkauf, OCDS-Monatsexporte, CC0, 0 €.
Deckt Bund, Länder **und Kommunen inklusive unterschwelliger Verfahren** ab —
den Teil, der auf TED gar nicht erscheint. TED ergänzt EU-weit.

12 Monate (10/2025 – 09/2026):

```
283.597 Bekanntmachungen gelesen
 17.185 mit IT-CPV-Dominanz
  2.468 Unternehmen mit belegter Teilnahme
```

### Beweishierarchie statt Ja/Nein

Jede Zeile trägt `proof_type`, `proof_url`, `proof_date` und `proof_confidence`.
Die angekündigte Stichprobenprüfung ist damit ein Klick.

| Beleg | Bedeutung | n |
|---|---|---|
| `P1_zuschlag_24m` | Zuschlag, Gewinner ausdrücklich benannt | 329 |
| `P1C_alleinbieter` | einziger Bieter einer Zuschlagsbekanntmachung → Zuschlag **erschlossen** | 1.727 |
| `P1D_ausgang_offen` | Bieter unter mehreren, kein Gewinner benannt | 402 |
| `P2_zuschlag_48m` | Zuschlag 24–48 Monate zurück | 5 |
| `P3_rahmenvertrag` | laufender Rahmenvertrag | 4 |
| `P1B_bieter_unterlegen` | geboten, ein anderer bekam den Zuschlag | 1 |

**Warum vier Belegarten und nicht eine:** `tender.tenderers` nennt Bieter,
`awards[].suppliers` nennt Gewinner. In 4.309 Bekanntmachungen ohne
Gewinnerangabe haben **3.987 genau einen Bieter** — der hat gewonnen, die
Plattform hat ihn nur anders gemappt. Wer die pauschal als „hat geboten und
verloren" führt, verkauft eine erfundene Eigenschaft mit amtlicher Beleg-URL
daneben. Der Unterschied entscheidet den ersten Satz der Ansprache.

### Tiering ohne Mitarbeiterzahl — und warum das besser ist

Die erste Fassung stufte nach Größe ein (50–2.000 MA). Ergebnis: **2.464 von
2.468 Zeilen auf Tier B** — kein Urteil, sondern ein fehlender Wert in
Verkleidung, weil die Mitarbeiterzahl erst aus dem Enrichment kommt. Und wo
sie vorlag, war sie bei **5 von 10 Firmen die des Konzerns** statt die des
bietenden Rechtsträgers (Bechtle 17.000, Computacenter 21.000/UK).

Das Tier hängt deshalb ausschließlich an Vergabedaten:

| Merkmal | Spanne |
|---|---|
| Häufigkeit — Verfahren in 12 Monaten | 1 bis 131 |
| Aktualität — Alter des jüngsten Belegs | Median 177 Tage |
| Breite — verschiedene Auftraggeber | 626 Firmen mit > 1 |
| Belegart | 6 Stufen |

```
A   236   laufender Angebotsprozess     (≥ 3 Verfahren, Beleg ≤ 180 Tage)
B 1.268   wiederkehrend oder aktuell
C   964   belegt, aber weder häufig noch aktuell
```

Jede Zeile trägt die nachrechenbare Begründung („131 Verfahren in 12
Monaten, jüngster Beleg vor 1 Monat, 24 verschiedene Auftraggeber") und
`tier_status`, das sagt, **worauf** das Tier beruht: `zuschlag_benannt`,
`zuschlag_erschlossen`, `teilnahme_offen` oder `schwacher_beleg`.

**Gegenprobe:** Von fünf unabhängig per Apollo als ICP-passend bestätigten
Firmen (63–900 MA) landen drei allein aus den Vergabedaten in Tier A. Die
Größe korreliert, ohne dass wir sie brauchen.

**Der ehrliche Preis:** Das Tier misst Ausschreibungsaktivität, nicht
Größenpassung. Bechtle und SVA stehen in A, weil sie ständig bieten. Die
Größe filtert man nachgelagert über `employees` — sie ist nur kein
Eingangswert der Einstufung mehr. Details in [docs/tiering.md](docs/tiering.md).

**Belege geprüft:** 30 Zufallsstichproben, **30/30 erreichbar**, alle
`application/pdf`. Der Prüfer (`src/verify_proofs.py`) testet Statuscode
**und** Content-Type **und** Größe — ein Statuscode allein hätte den
ursprünglichen Fehler bestätigt statt gefunden (siehe unten).

**Vollständigkeit:** `capture_recapture()` schätzt die Marktgröße nach Chapman
und schreibt den Vorbehalt in die Ausgabe: Vergabedaten und Branchenrankings
sind **nicht unabhängig**, beide überrepräsentieren große Unternehmen. Die
Schätzung ist deshalb eine Untergrenze, nicht ein Punktwert.

## Aufgabe 2 — Signal-Engine

Vier Quellen, davon drei ohne Stellenanzeigen:

| Signal | Quelle | Gewicht | Treffer im 8-Wochen-Lauf |
|---|---|---|---|
| `rahmenvertrag_laeuft_aus` | DÖE, Vertragsende in 180–270 Tagen | 9 | 7 |
| `angebot_ohne_zuschlag` | DÖE, Bieter neben fremdem Gewinner | 8 | 1 |
| `bid_rolle_ausgeschrieben` | BA-Jobsuche | 7 | 81 |
| `zuschlag_gewonnen` | DÖE + TED | 6 | 1.588 |
| `teilnahme_belegt` | DÖE, Ausgang offen | 5 | 152 |

**Delta-Erkennung:** `signal_id = sha256(source|external_id)`,
`content_hash` über die inhaltlichen Felder, 14 Tage Überlappungsfenster für
nachträglich korrigierte Bekanntmachungen.

```
Lauf 1 (leerer Store)   neu 1.694   geändert  21   unverändert   1
Lauf 2 (direkt danach)  neu     0   geändert   6   unverändert 395
```

Die 6 Änderungen in Lauf 2 sind echte Korrekturen im Überlappungsfenster,
keine Artefakte — genau dafür ist das Fenster da.

**Nachvollziehbarkeit:** Jeder Score ist aufklappbar — die vollständige
Zerlegung (Gewicht × Recency × ICP-Fit × Confidence, Stacking, Treiber-Signal)
steht in `data/score_trace.csv`, verbunden über `company_id`. Bewusst als
eigene Datei: als Spalte war sie 74 % der Dateigröße und machte die Tabelle
für Menschen unlesbar.

**Ergebnis:** 669 Accounts mit Signal, **197 über der Score-Schwelle (29 %)**.
Die Schwelle ist an der beobachteten Verteilung kalibriert, nicht geraten;
die Messreihe steht als Kommentar in `src/config.py`.
Top 20 mit „Why now"-Satz in `data/longlist_signale.csv`, sortiert nach Score.

## Was funktioniert

- **Vergabedaten als Primärquelle.** 2.468 belegte Unternehmen aus einer
  kostenlosen CC0-Quelle, jede Zeile mit PDF dahinter.
- **Die CPV-Dominanzprüfung.** Vorher zog eine einzige Handwerkskammer-Rahmen­
  vereinbarung jeden beteiligten Werkzeuglieferanten in die IT-Liste; auffällig
  wurde es erst, weil mehrere Firmen exakt dieselbe Zuschlagszahl hatten.
- **Getrennte Fehlerkübel.** Vergabestellen → `offene_verfahren.csv`,
  Job-Signale ohne IT-Beleg → `job_signale_ohne_icp_beleg.csv`,
  unsichere Auflösungen → Review-Queue. Nichts davon geht ins Outbound.
- **Ehrliche Confidence.** Unter 0,70 wird nicht geraten, sondern in die
  Review-Queue geschrieben. Aktuell 87 Zeilen.

## Was nicht funktioniert

- **Unterlegene Bieter sind unsichtbar.** Von 441 Bekanntmachungen mit Bieter-
  *und* Gewinnerangabe sind beide Listen in **438** identisch. Das Systemhaus,
  das zwölfmal bietet und nie gewinnt — der beste Patterno-Kunde überhaupt —
  steht in 12 Monaten genau **einmal** in diesen Daten.
- **Zwei Signaltypen feuern nicht.** `offene_ausschreibung_im_profil` braucht
  eine Angebotsfrist; das OCDS-Mapping dieses Feeds führt weder
  `tenderPeriod` noch eine Frist auf laufenden Verfahren.
  `nachpruefung_vergabekammer` ist spezifiziert, aber nicht implementiert.
  **Jeder Lauf listet jetzt, welcher Typ gefeuert hat und welcher nicht** —
  ein stummes Signal war der teuerste Fehler dieses Projekts.
- **Der Signalmix ist einseitig.** 651 von 669 Accounts hängen an
  `zuschlag_gewonnen`. Die Rangfolge misst damit vor allem Aktualität.
- **Die Domain-Resolution ist die Engstelle**, nicht die Kosten. Von 2.468
  Zeilen haben erst 11 eine angereicherte Domain; der Rest läuft über Clay.
  Die Tiers stehen davon unabhängig fest — fehlt eine Domain, fehlt der
  Ansprechweg, nicht die Einstufung.
- **ICP-Präzision an der Spitze ist nicht perfekt.** Unter den Top 20 stehen
  Siemens (Gebäudeautomation), ein Sensorhersteller und ein Verkehrszähl-
  anbieter. CPV belegt Teilnahme, nicht Geschäftsmodell — der Systemhaus-
  Klassifikator fehlt noch.
- **TED-Belege kann ich nicht maschinell prüfen.** `ted.europa.eu` antwortet
  auf jede serverseitige Anfrage mit HTTP 202 und 0 Byte (JS-Challenge).
  Der Prüfer weist sie als dritte Kategorie aus — weder bestätigt noch
  widerlegt. Alles zu behaupten, was ich nicht geprüft habe, wäre der
  bequemere Weg gewesen.

## Vier Fehler, die etwas über die Datenqualität sagen

Sie stehen hier, weil jeder von ihnen erfolgreich aussah.

1. **Die Beleg-URL war erfunden.** Ich hatte `/ui/de/notice/<ocid>` gebaut,
   ohne sie je abzurufen. Die Seite ist eine Single-Page-App: Sie antwortet
   auf **jede** URL mit HTTP 200 und derselben 1.309 Byte großen Hülle, die
   404-Meldung rendert erst JavaScript. Ein Statuscheck hätte den Fehler
   *bestätigt*. Richtig ist `/api/notices/<release id>?format=pdf` —
   und `ocid` ≠ `id`.
2. **Das wertvollste Signal feuerte nie.** `rahmenvertrag_laeuft_aus` las
   `awards[].contractPeriod`: 0 Treffer in 20.000 Releases. Das Vertragsende
   hängt am Los — `tender.lots[].contractPeriod`: 15.716 Treffer. Ein leeres
   Feld sieht in jeder Statistik aus wie „diese Woche kein Anlass".
3. **TED schnitt stumm ab.** 8 Seiten × 250 = 2.000 Notices bei 2.435 im
   Fenster. Der Lauf meldete Erfolg, und im nächsten Lauf galten 131 Notices
   als „neu" — die Pipeline sah idempotent falsch aus. Jetzt wird gegen
   `totalNoticeCount` abgeglichen.
4. **Eine Trefferquote ohne Stichprobenangabe ist wertlos.** Die
   Domain-Resolution maß 77 % — an bekannten Marken. Im Longtail waren 8 von
   12 Auflösungen falsch, darunter `eominnesota.org` für die EOMI AG aus
   Hamburg. Die Lehre steckt jetzt als Impressum-Prüfung nach § 5 DDG im Code,
   mit dem Ort aus der Vergabebekanntmachung als Diskriminator.

## Kosten

Quellen 0 €. Anreicherung ≈ **6,3 Apollo-Credits je qualifiziertem Lead**,
Rechnung und Definition in [docs/betriebsmodell.md](docs/betriebsmodell.md).
Der eigentliche Kostentreiber ist nicht das Credit, sondern jede Domain, die
in die Review-Queue fällt und Menschenzeit kostet.

## Zeitaufwand

| Block | ca. |
|---|---|
| Quellenprüfung (TED, DÖE, BA — inkl. Verwerfen der Apify-Scraper) | 25 min |
| Longlist-Pipeline inkl. CPV-Dominanz und Konsortien | 55 min |
| Signal-Engine, Delta-Store, Scoring | 45 min |
| Fehlersuche an echten Daten (die vier oben) | 40 min |
| Enrichment-Waterfalls, Apollo-Filter | 25 min |
| Dokumentation | 20 min |

## Die nächsten zwei Wochen

1. **Vergabekammer-Entscheidungen als vierte echte Quelle.** Ein
   Nachprüfungsantrag ist der einzige öffentliche Beleg dafür, dass jemand
   verloren hat *und* es ihm weh tut. Genau die Lücke, die der Feed offenlässt.
2. **Systemhaus-Klassifikator.** CPV belegt Teilnahme, nicht Geschäftsmodell.
   Website-Signale plus Apollo-Branche, gegen 100 handgelabelte Firmen gemessen.
3. **Domain-Resolution auf eine Zufallsstichprobe messen** und erst dann eine
   Quote nennen. Bis dahin steht im Kostenmodell eine ausgewiesene Annahme.
4. **Angebotsfristen aus dem eForms-XML** nachziehen, damit
   `offene_ausschreibung_im_profil` endlich feuert — im OCDS-Mapping fehlt das
   Feld, im XML (BT-131) steht es.
5. **Scoring gegen Ergebnisse kalibrieren.** Die Gewichte sind begründet, aber
   unbelegt. Nach ~200 Kontakten zeigt die Antwortquote je Signaltyp, ob
   `rahmenvertrag_laeuft_aus` seine 9 verdient.

---

| Datei | Inhalt |
|---|---|
| `data/longlist_markt.csv` | Aufgabe 1 — 2.468 Unternehmen mit Beleg |
| `data/longlist_signale.csv` | Aufgabe 2 — 669 Accounts mit Score und „Why now" |
| `data/score_trace.csv` | Score-Zerlegung je Account, Join über `company_id` |
| `data/offene_verfahren.csv` | Vergabestellen-Feed, Join-Input, **kein Outbound** |
| `data/job_signale_ohne_icp_beleg.csv` | Prüfbestand, **kein Outbound** |
| `docs/waterfalls.md` | Enrichment-Waterfalls mit gemessenen Quoten |
| `docs/apollo_filter.md` | Apollo-Filter für Clay, aus echten Titeln |
| `docs/playbook_it_systemhaeuser.md` | ICP-Playbook für beide Use Cases, im Format des Patterno-Playbooks |
| `docs/tiering.md` | warum Tiering ein eigener Schritt ist, Konzernfalle |
| `docs/betriebsmodell.md` | Clay / Supabase / Attio, Kosten je Lead |
