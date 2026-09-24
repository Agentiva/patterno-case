# Signal-Engine

Welche Quellen laufen, was sie liefern, wie das Delta funktioniert und wie
gescored wird. Stand 24.09.2026.

## Quellen

| Quelle | Zugang | Kosten | Frequenz | Signale im Lauf |
|---|---|---|---|---|
| **Datenservice Öffentlicher Einkauf** | `oeffentlichevergabe.de/api/notice-exports`, OCDS-Monatspakete | 0 € (CC0) | täglich abrufbar | 775 |
| **TED Search API v3** | `api.ted.europa.eu/v3/notices/search`, ohne Auth | 0 € | täglich | 840 |
| **Bundesagentur für Arbeit Jobsuche** | `rest.arbeitsagentur.de/.../pc/v6/jobs`, Header `X-API-Key` | 0 € | täglich | 79 |

**Warum der Datenservice und nicht nur TED:** TED enthält nur oberschwellige
EU-Vergaben. Der Datenservice deckt Bund, Länder **und Kommunen inklusive
unterschwelliger Verfahren** ab — also genau den Teil, der bei einem kommunal
einkaufenden Segment den Unterschied zwischen Spitze und Eisberg ausmacht.

**Ehrlich zur BA-Jobsuche:** Die API ist community-dokumentiert, nicht
offiziell freigegeben, ohne SLA. Im Lauf vom 23.09. lieferten 4 von N
Abfragen HTTP 500. Sie trägt deshalb kein Signal allein, sondern nur in
Kombination mit einem Vergabebeleg.

### Die vierte Quelle: gemessen, noch nicht gebaut

Der Case verlangt **≥ 4 wiederkehrende Quellen, davon ≥ 2 ohne
Stellenanzeigen**. Die zweite Bedingung ist erfüllt (DÖE und TED), die erste
nicht: Es sind drei.

Die vierte wäre **Vergabekammer-Entscheidungen**. Ein Nachprüfungsantrag ist
der einzige öffentliche Vorgang, bei dem ein Unternehmen *Geld dafür ausgibt*,
zu zeigen, dass ihm eine verlorene Ausschreibung weh tut — Anwalt plus
Kammergebühr. Genau die Lücke, die der Vergabefeed offenlässt.

Statt sie zu bauen, wurde sie erst vermessen —
`python3 -m src.sources.vergabekammer_audit`, Ergebnis in
`data/vk_quellenaudit.csv`.

**Befund 1 — welche Kammern überhaupt zählen.** Der OCDS-Feed nennt je
Verfahren die zuständige Stelle (`parties[].roles = reviewBody`): 12.326
Nennungen, 652 verschiedene Stellen, stark konzentriert.

| Kammer | Verfahren / 12 Monate |
|---|---|
| Vergabekammer des Bundes *(3 Namensvarianten)* | ~2.206 |
| VK Westfalen · VK Berlin · VK Hessen | 593 · 573 · 424 |
| VK Baden-Württemberg · VK Niedersachsen · VK Rheinland | 409 · 355 · 329 |
| VK Südbayern · 1. VK Sachsen | 324 · 313 |

Es sind also nicht 652 Quellen zu bauen, sondern rund 15. Und der Feed sagt
pro Verfahren vorher, welche Kammer zuständig ist — das ist der
Routing-Schlüssel. Die drei Namensvarianten der Bundeskammer sind kein
Schönheitsfehler: Ohne Normalisierung zählt man sie dreifach und priorisiert
falsch.

**Befund 2 — die Hauptquelle braucht einen Browser.** Gemessen am 24.09.2026:

```
bundeskartellamt.de, statische Seiten     HTTP 200, 148 KB
bundeskartellamt.de, Entscheidungssuche   HTTP 403      ← WAF
openjur.de · rechtsprechung-im-internet   HTTP 200
vergabekammer.nrw.de                      nicht auflösbar
```

Der 403 kam vom Server, nicht vom Egress-Proxy — dessen Statusendpunkt
meldete nur einen einzigen Relay-Fehler, und zwar für eine andere Domain. Der
Such-Endpunkt blockt HTTP-Clients gezielt.

Damit ist das **erste belastbare Argument für Apify** in diesem Projekt: Die
drei bestehenden Quellen sind saubere HTTP-Aufrufe und brauchen keine
Scraper-Plattform. Diese eine braucht einen echten Browser.

**Befund 3 — die Frage, die alles entscheidet, ist noch offen.** Viele
veröffentlichte Beschlüsse schreiben „die Antragstellerin" statt des
Firmennamens. Ohne Namen kein Account, ohne Account kein Signal. Das Audit
misst das mit `namensquote()`; die Schwelle steht bei **30 %**, unterhalb
davon wird der Adapter nicht gebaut.

Aktuell ist die Quote **nicht messbar**, weil an keiner Quelle ein Einstieg zu
einzelnen Entscheidungen gefunden wurde — das Skript beendet sich deshalb mit
Exit-Code 1. Die Messfunktion selbst ist getestet: 100 % auf fünf
Namensvarianten (`Controlware GmbH`, `msg systems ag`, `adesso SE`,
`SCALTEL GmbH & Co. KG`), 0 % auf anonymisiertem Text, keine Falsch-Positiven
auf Fließtext.

**Nächster Schritt:** 20 Entscheidungen von Hand ziehen, durch
`namensquote()` schicken, und erst dann entscheiden.

### Was ich stattdessen geprüft und verworfen habe

Naheliegend wäre ein billiger Ersatz aus vorhandenen Daten:
`award.status = "unsuccessful"` — Los oder Verfahren nicht vergeben, die
Bieter haben umsonst kalkuliert. 469 Fälle in 12 Monaten.

**Trägt nicht.** Von 72 Releases mit benannten Bietern sind 69 *gemischt*:
Einige Lose vergeben, andere nicht. Und im Beispiel steht dieselbe Partei als
`supplier` beim nicht vergebenen **und** beim vergebenen Los. Das Feld sagt
also nicht „diese Firma hat verloren". Übrig bleiben 3 saubere Fälle im Jahr —
das ist kein Signal, sondern Rauschen.

Ein Signaltyp, der dreimal im Jahr feuert, sieht in der Konfiguration aus wie
eine Quelle und ist keine.

## Signaltypen

| Signal | Gewicht | Quelle | Im Store | Treiber-Accounts |
|---|---|---|---|---|
| `nachpruefung_vergabekammer` | 10 | — nicht implementiert | 0 | 0 |
| `rahmenvertrag_laeuft_aus` | 9 | DÖE, Lot-`contractPeriod` | 6 | 6 |
| `angebot_ohne_zuschlag` | 8 | DÖE, Bieter neben fremdem Gewinner | 0 | 0 |
| `offene_ausschreibung_im_profil` | 8 | DÖE, eForms-XML BT-131 | 196 | **0 — siehe unten** |
| `bid_rolle_ausgeschrieben` | 7 | BA-Jobsuche | 79 | 1 |
| `zuschlag_gewonnen` | 6 | DÖE + TED | 1.424 | 634 |
| `teilnahme_belegt` | 5 | DÖE, Ausgang offen | 145 | 10 |
| `leitungswechsel_public` | 5 | — keine Quelle angebunden | 0 | 0 |
| `neue_public_referenz` | 4 | — keine Quelle angebunden | 0 | 0 |

Die beiden Zahlenspalten laufen bewusst auseinander. **Im Store** ist, was nach
der Delta-Erkennung persistiert wurde; **Treiber-Accounts** ist, wie oft der Typ
das höchstbewertete Signal eines Accounts in `longlist_signale.csv` stellt.
Dazwischen liegen Firmenauflösung, Ausschlusslisten und Confidence-Schwelle.
Bei `bid_rolle_ausgeschrieben` ist der Trichter am steilsten: 79 Anzeigen für
Bid- und Tenderrollen, davon **2 mit IT-Vergabebeleg**, davon **1** als
Top-Signal seines Accounts. 35 der übrigen liegen als Prüfbestand in
`job_signale_ohne_icp_beleg.csv` — eine Stellenanzeige belegt einen
Kapazitätsschmerz, aber kein IT-Systemhaus.

**`angebot_ohne_zuschlag` steht bei null, obwohl der Lauf ein Rohsignal
erzeugt.** Die drei Bieter-Typen teilen sich den Schlüssel
`{ocid}:bidder:{firma}`, weil sie dieselbe Tatsache beschreiben — diese Firma
hat an diesem Verfahren teilgenommen — und sich nur im Ausgang unterscheiden.
Trägt eine spätere Bekanntmachung zum selben Verfahren einen anderen Ausgang,
gewinnt sie. Das ist gewollt: Die jüngste Bekanntmachung ist die richtige. Es
heißt aber auch, dass dieser Typ nur überlebt, wenn er die letzte Aussage zum
Verfahren ist — und das ist er in diesen zwölf Monaten kein einziges Mal. Die
Begründung dafür steht unter „Was die Daten nicht hergeben".

**Jeder Lauf listet auf, welcher Typ gefeuert hat und welcher nicht.** Das ist
kein Komfort, sondern eine Lehre: `rahmenvertrag_laeuft_aus` las monatelang
`awards[].contractPeriod` — ein Feld, das dieser Feed nicht führt. Null Treffer,
keine Fehlermeldung. Ein leeres Signal sieht in jeder Statistik aus wie „diese
Woche kein Anlass". Das Vertragsende hängt am Los: `tender.lots[].contractPeriod`,
15.716 Treffer in 20.000 Releases.

### `offene_ausschreibung_im_profil` — feuert, aber nicht auf Accounts

Dieser Typ schwieg lange aus demselben Grund: Das OCDS-Mapping des Feeds führt
auf laufenden Verfahren **weder `tenderPeriod` noch sonst eine Angebotsfrist**.
Zweimal wurde daraus der falsche Schluss gezogen, der Feed kenne keine Frist.

Er kennt sie — nur nicht im JSON. Dieselbe Bekanntmachung als XML abgerufen
trägt `cac:TenderSubmissionDeadlinePeriod`, das ist BT-131 aus eForms-DE. Die
URL dafür baute der Adapter schon lange; sie wurde nur nie gelesen
(`src/sources/eforms.py`). **196 offene Verfahren** stehen jetzt in
`data/offene_verfahren.csv`, Trefferquote des XML-Abrufs 60 %.

Und trotzdem steht in der Tabelle oben eine Null bei den Treiber-Accounts. Das
ist kein Restfehler, sondern die Natur des Signals: Eine laufende Ausschreibung
nennt **den Auftraggeber, nicht den Bieter**. Wer sich bewerben wird, steht erst
nach der Frist in den Daten. Die Datei ist deshalb ausdrücklich als
*Join-Input, kein Outbound* beschriftet.

Nutzbar wird sie über die Verbindung zu Longlist 1: „Die Uni Jena schreibt eine
I-Doit-Verlängerung aus, Frist in 13 Tagen — und Firma X hat bei genau dieser
Vergabestelle schon zweimal geboten." **Diesen Join habe ich nicht gebaut.** Er
ist billig (beide Seiten liegen als CSV vor, Schlüssel ist die Vergabestelle
plus CPV-Präfix), aber er ist eine Produktentscheidung: Er erzeugt eine Ansprache
zu einem Verfahren, an dem das Unternehmen noch gar nicht teilnimmt. Ob das
hilfreich wirkt oder übergriffig, entscheidet man nicht im Code. Der Rohstoff
liegt bereit, die Kopplung gehört in den Zwei-Wochen-Plan.

## Delta-Erkennung

```
signal_id    = sha256(source | external_id)
content_hash = sha256 über die inhaltlichen Felder
```

Ein Signal ist **neu**, wenn die `signal_id` unbekannt ist; **geändert**, wenn
die `signal_id` bekannt, der `content_hash` aber anders ist; sonst
**unverändert**. Ausgegeben werden nur neue und geänderte.

**Überlappungsfenster 14 Tage.** Vergabestellen korrigieren Bekanntmachungen
nachträglich. Ohne Überlappung würde eine Korrektur nie gelesen.

Nachgewiesen am Live-Lauf:

```
Lauf 1 (leerer Store)   neu 1.850   geändert   0   unverändert    0
Lauf 2 (direkt danach)  neu     0   geändert   0   unverändert  544
Lauf 3, Lauf 4          neu     0   geändert   0   unverändert  544
```

### Der Fehler, der sich hinter genau dieser Zahl versteckt hat

In einer früheren Fassung stand hier „Lauf 2: 6 Änderungen — echte Korrekturen
im Überlappungsfenster, genau dafür ist das Fenster da". Das war falsch, und es
war die bequeme Erklärung.

Die sechs Zeilen änderten sich in **jedem** Lauf, auf unveränderter Eingabe. Ein
Vergabeverfahren kann mehrere Bekanntmachungen tragen, typisch eine Korrektur
einen Tag nach dem Original. Beide erzeugten dieselbe `external_id`, aber
verschiedene `content_hashes`, überschrieben sich innerhalb desselben Laufs und
meldeten sich danach dauerhaft als „geändert". 17 Schlüssel, konstant 25 falsche
Änderungen über vier Läufe hinweg.

Eine Delta-Ausgabe, der man nicht glauben kann, ist wertlos — hier hätte sie
jede Woche dieselben Firmen als frisch bewegt gemeldet. Jetzt gewinnt je
`external_id` die jüngste Bekanntmachung, Gleichstand wird über die `notice_id`
aufgelöst, damit das Ergebnis nicht von der Lesereihenfolge abhängt.

Das Überlappungsfenster bleibt richtig, es hat hier nur den Fehler getarnt:
Echte Korrekturen sind in diesem Korpus selten genug, dass sechs davon pro Lauf
plausibel aussahen. Der Beleg dafür, dass das Fenster funktioniert, muss deshalb
anders erbracht werden — nicht daran, dass sich etwas ändert, sondern daran,
dass sich bei gleicher Eingabe **nichts** ändert.

**Beobachtbarkeit:** Jede Quelle schreibt eine Zeile in `runs` mit
gelesenen/neuen/geänderten Zeilen und Fehlertext — `python3 -m src.cli runlog`.
Fällt eine Quelle aus, endet der Lauf mit Exit-Code 1 und benennt sie. Ohne
das sieht ein Totalausfall in den Zahlen exakt aus wie ein sauberer zweiter
Lauf: überall Null.

## Scoring

Multiplikativ, nicht additiv:

```
score = min(Gewicht × Aktualität × ICP-Fit × Confidence + Stacking, cap) / cap × 100
```

- **Aktualität** in Stufen: ≤14 Tage 1,0 · ≤28 0,8 · ≤42 0,6 · ≤56 0,4, Boden 0,2
- **ICP-Fit** aus dem Tier: A 1,0 · B 0,8 · C 0,6 · D 0,3
- **Confidence** aus der Firmenauflösung
- **Stacking** +2,0 ab zwei verschiedenen Signaltypen (124 von 651 Accounts)

`icp_fit` und `match_confidence` wirken auf **[0,40 … 1,00]** statt [0 … 1].
Sonst löscht eine Confidence von 0,65 ein Signal der Stärke 10 faktisch aus,
und die Rangfolge misst Datenqualität statt Anlass.

Die vollständige Zerlegung je Account steht in `data/score_trace.csv`, Join
über `company_id`. Jeder Score ist damit aufklappbar statt Blackbox.

**Schwelle 40**, kalibriert an der gemessenen Verteilung, nicht geraten:

```
30 → 372 Accounts (57 %)     40 → 200 (31 %)  ← gewählt
35 → 261 (40 %)              45 →  77 (12 %)
```

Ziel war 20–30 %: genug Volumen für eine Woche Outbound, ohne den Longtail
mitzubezahlen. Nach dem Dubletten-Fix liegt die Schwelle bei 31 % — knapp
darüber, weil das Bereinigen die Verteilung leicht verschoben hat. Zwischen 40
und 45 liegt weiterhin eine Klippe (200 → 77); dort endet die Gruppe mit
mehreren oder höher gewichteten Signalen. Den Wert deshalb nicht nachjustiert:
Die Klippe ist die inhaltliche Grenze, die 30 % waren nur der Zielkorridor.

## Was die Daten nicht hergeben

**Unterlegene Bieter sind unsichtbar.** Von 441 Bekanntmachungen, die Bieter
*und* Gewinner benennen, sind beide Listen in **438 Fällen identisch**. Das
Systemhaus, das zwölfmal bietet und nie gewinnt — der beste Patterno-Kunde —
steht in zwölf Monaten genau **einmal** in diesen Daten.

Daraus folgt die wichtigste Designentscheidung: Nicht der Ausgang zählt,
sondern die **Häufigkeit**. Wer 17 Verfahren im Jahr bestreitet, hat einen
Angebotsprozess — unabhängig davon, wie viele davon er gewinnt.

**Die Falle dabei:** In 4.309 Bekanntmachungen ohne Gewinnerangabe haben
**3.987 genau einen Bieter**. Der hat gewonnen; die Plattform hat ihn nur in
die Bieterrolle gemappt. Wer die pauschal als „hat geboten und verloren"
führt, verkauft eine erfundene Eigenschaft mit amtlicher Beleg-URL daneben.
Deshalb vier getrennte Belegarten (`tier_status`), nicht eine.

## Betrieb

- **Takt:** wöchentlich, montags früh — der Vorlauf auf die Frist ist dann am größten.
- **Laufzeit:** rund 50 Sekunden für alle drei Quellen live.
- **Fenster:** 8 Wochen Signalfenster, 12 Monate Longlist-Korpus.
- **Offline:** `make demo` läuft gegen geschichtete Fixtures ohne Netz und
  ohne Keys; zweiter Lauf gibt 0 neue Zeilen aus.
