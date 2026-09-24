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

### Die vierte Quelle fehlt

Der Case verlangt **≥ 4 wiederkehrende Quellen, davon ≥ 2 ohne
Stellenanzeigen**. Die zweite Bedingung ist erfüllt (DÖE und TED). Die erste
nicht: Es sind drei.

Geplant und spezifiziert, aber nicht gebaut: **Vergabekammer-Entscheidungen**.
Ein Nachprüfungsantrag ist der einzige öffentliche Beleg dafür, dass ein
Unternehmen verloren hat *und* es ihm weh tut — genau die Lücke, die der
Vergabefeed offenlässt (siehe unten). Das steht als Punkt im Zwei-Wochen-Plan.

## Signaltypen

| Signal | Gewicht | Quelle | Treiber-Accounts |
|---|---|---|---|
| `nachpruefung_vergabekammer` | 10 | — nicht implementiert | 0 |
| `rahmenvertrag_laeuft_aus` | 9 | DÖE, Lot-`contractPeriod` | 6 |
| `angebot_ohne_zuschlag` | 8 | DÖE, Bieter neben fremdem Gewinner | 1 |
| `offene_ausschreibung_im_profil` | 8 | — Feld fehlt im OCDS-Mapping | 0 |
| `bid_rolle_ausgeschrieben` | 7 | BA-Jobsuche | 1 |
| `zuschlag_gewonnen` | 6 | DÖE + TED | 651 |
| `teilnahme_belegt` | 5 | DÖE, Ausgang offen | 11 |

**Jeder Lauf listet auf, welcher Typ gefeuert hat und welcher nicht.** Das ist
kein Komfort, sondern eine Lehre: `rahmenvertrag_laeuft_aus` las monatelang
`awards[].contractPeriod` — ein Feld, das dieser Feed nicht führt. Null Treffer,
keine Fehlermeldung. Ein leeres Signal sieht in jeder Statistik aus wie „diese
Woche kein Anlass". Das Vertragsende hängt am Los: `tender.lots[].contractPeriod`,
15.716 Treffer in 20.000 Releases.

`offene_ausschreibung_im_profil` feuert bis heute nicht: Das OCDS-Mapping des
Feeds führt weder `tenderPeriod` noch eine Angebotsfrist auf laufenden
Verfahren. Die Frist steht im eForms-XML (BT-131), nicht im JSON.

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
Lauf 1 (leerer Store)   neu 1.694   geändert  21   unverändert   1
Lauf 2 (direkt danach)  neu     0   geändert   6   unverändert 395
```

Die 6 Änderungen sind echte Korrekturen im Überlappungsfenster.

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
- **Stacking** +2,0 ab zwei verschiedenen Signaltypen (128 von 669 Accounts)

`icp_fit` und `match_confidence` wirken auf **[0,40 … 1,00]** statt [0 … 1].
Sonst löscht eine Confidence von 0,65 ein Signal der Stärke 10 faktisch aus,
und die Rangfolge misst Datenqualität statt Anlass.

Die vollständige Zerlegung je Account steht in `data/score_trace.csv`, Join
über `company_id`. Jeder Score ist damit aufklappbar statt Blackbox.

**Schwelle 40**, kalibriert an der gemessenen Verteilung, nicht geraten:

```
30 → 354 Accounts (55 %)     40 → 186 (29 %)  ← gewählt
35 → 237 (37 %)              45 →  38 ( 6 %)
```

Ziel war 20–30 %: genug Volumen für eine Woche Outbound, ohne den Longtail
mitzubezahlen.

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
