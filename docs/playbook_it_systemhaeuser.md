# PLAYBOOK · PATTERNO · IT-SYSTEMHÄUSER

**Patterno GmbH — Neukunden-Akquise über belegte Vergabeteilnahme**

> „Den Auftrag sollte der Beste gewinnen. Nicht der Geduldigste."

Zwei-Use-Case-Strategie: **Marktabdeckung** (`longlist_markt.csv`) ·
**Anlassbasierte Ansprache** (`longlist_signale.csv`)

Kernprodukte: Patterno HIT (Finden) · Patterno BID (Prüfen & Gewinnen) ·
AI Chat (Angebote erstellen)

Deutschland · Ansprache Deutsch (Sie-Form) · Version 1.0 · September 2026
· Datenstand 23.09.2026

---

## Was dieses Playbook anders macht

Das bestehende Patterno-Playbook (Pharma, Bau/TGA) definiert ICPs über
**Branche und Größe** und verlangt in Kapitel 9 pro Account 5–10 Minuten
Handrecherche nach einem Vergabeanlass.

Dieses Playbook dreht das um. Die Segmentierung kommt nicht aus einer
Branchenannahme, sondern aus **amtlichen Vergabedaten**: Wer an öffentlichen
Ausschreibungen teilnimmt, steht dort mit Namen, Datum und Bekanntmachungs-PDF.
Teilnahme ist damit ein Faktum, kein Attribut — und der Vergabeanlass, den
Kapitel 9 fordert, ist keine Rechercheaufgabe mehr, sondern eine Spalte.

| | bestehendes Playbook | dieses Playbook |
|---|---|---|
| Segmentierung | Branche + Mitarbeiterzahl | belegte Vergabeteilnahme |
| Vergabeanlass | 5–10 min Handrecherche je Account | `proof_url` + `why_now` je Zeile |
| Priorisierung | Branchenzugehörigkeit | Häufigkeit, Aktualität, Breite |
| Aktualisierung | manuell | wöchentlicher Lauf, nur Neues |

---

## 1. Unternehmensübersicht

Patterno GmbH, Hamburg, gegründet 2025 von Maurice Funk und Leon Brunner.
KI-Ausschreibungssoftware — ausdrücklich eine **Bietersoftware**, gebaut für
Unternehmen, die Aufträge gewinnen wollen, nicht für Vergabestellen, die
veröffentlichen. Über 100 Teams nutzen die Plattform. Betrieb und
Datenhaltung ausschließlich in Frankfurt am Main, ISO-27001-zertifiziert.

| Merkmal | Ausprägung |
|---|---|
| Kernprodukte | Patterno HIT (Finden), Patterno BID (Prüfen und Gewinnen), AI Chat, Tender Intelligence |
| Abdeckung | über 4.500 Vergabeportale, 29 Länder — u. a. TED, DTVP, Vergabe24, Staatsanzeiger, eVergabe, Landesportale |
| Preismodell | Starter ab 89 €, Team ab 269 €, Scale ab 449 €, Enterprise ab 2.249 € pro Monat (netto, jährlich) |
| Kontakt | info@patterno.de · +49 40 74302651 · patterno.de |

*Angaben aus dem bestehenden Playbook (Stand September 2026). Kennzahlen und
Referenznamen vor namentlicher Nennung im Outreach intern verifizieren.*

### Warum IT-Systemhäuser als drittes Segment tragen

Das bestehende Playbook stellt IT & Digitalisierung in Kapitel 4 bewusst
zurück, mit der Begründung: *„Großer Markt, aber Botschaft ohne
Spezialisierung austauschbar."* Die Reaktivierungsbedingung lautet: *„Eine
IT-Spezialisierung (z. B. EVB-IT-Logik) im Produkt existiert."*

Dieses Playbook liefert einen zweiten, unabhängigen Weg zur Spezifität.
Nicht über eine Produktfunktion, sondern über die **Daten in der Ansprache**:
Wenn die erste Zeile ein konkretes Verfahren mit Datum, Auftraggeber und
verlinkter Bekanntmachung nennt, ist die Botschaft nicht mehr austauschbar —
egal ob es eine IT-Spezialisierung im Produkt gibt.

---

## 2. Das Marktumfeld: IT-Vergaben in Deutschland

### Gemessen, nicht geschätzt

Grundlage ist der Datenservice Öffentlicher Einkauf (oeffentlichevergabe.de),
OCDS-Monatsexporte, CC0-lizenziert. Zeitraum 10/2025 – 09/2026:

```
283.597   Bekanntmachungen gelesen
 17.185   mit IT-CPV-Dominanz (≥ 50 % der Lose IT)
  2.458   Unternehmen mit belegter Teilnahme
  5.127   belegte Verfahrensteilnahmen insgesamt
```

| Kennzahl | Wert |
|---|---|
| Verfahren je Unternehmen | Median 1, Maximum **131** (SVA System Vertrieb Alexander) |
| Auftraggeber je Unternehmen | Median 1, Maximum **92** |
| Alter des jüngsten Belegs | Median 177 Tage |
| Unternehmen mit mehr als einem Auftraggeber | 626 |

### Was die Zahlen aus dem bestehenden Playbook hier bedeuten

- **88 Prozent unter der EU-Schwelle** — bestätigt sich in der Praxis: Von
  17.185 IT-Bekanntmachungen stammt der überwiegende Teil aus kommunalen und
  Landesquellen, die auf TED nicht erscheinen. Der Datenservice deckt sie ab,
  eine reine TED-Recherche nicht.
- **19 Prozent finden zu spät** (KOINNO 2025) — genau dagegen zielt Use Case 2:
  Der Signaltyp `rahmenvertrag_laeuft_aus` meldet 6–9 Monate vor Vertragsende,
  also bevor die Neuausschreibung überhaupt veröffentlicht ist.
- **16 bis 30 Stunden je Bewerbung** — bei 5.127 belegten Teilnahmen in zwölf
  Monaten ist das der Hebel, über den das Gespräch läuft.

### Der Befund, der das Segment definiert

Von 441 Bekanntmachungen, die sowohl Bieter als auch Gewinner benennen, sind
beide Listen in **438 Fällen identisch**. Der deutsche Vergabefeed
veröffentlicht unterlegene Wettbewerber praktisch nicht.

Das hat zwei Konsequenzen für die Ansprache:

1. Wir sehen, **wer teilnimmt** — nicht, wer verliert. Das Systemhaus, das
   zwölfmal bietet und nie gewinnt, bleibt unsichtbar, obwohl es der beste
   Patterno-Kunde wäre.
2. Deshalb ist die **Häufigkeit** der wichtigste Indikator: Wer 17 Verfahren
   in zwölf Monaten bestreitet, hat einen Angebotsprozess — und damit den
   Schmerz, den Patterno löst, unabhängig vom Ausgang.

---

## 3. Produkte und Wertversprechen

### Allgemeine Produktbeschreibung

Patterno ist eine KI-Ausschreibungssoftware für Unternehmen, die sich an
öffentlichen Ausschreibungen beteiligen. Die Plattform bündelt Ausschreibungen
aus über 4.500 Vergabeportalen in 29 Ländern — darunter TED, DTVP, Vergabe24,
Staatsanzeiger, eVergabe.de, Subreport ELViS und die Landesportale — und
bewertet jede einzelne Ausschreibung per Qualifizierter KI-Suche im Volltext
gegen das Profil des Kunden. Das Ergebnis ist eine tägliche Trefferliste mit
wenigen, dafür passenden Verfahren. Für ein IT-Systemhaus heißt das: Statt
Landesportale, Kommunalplattformen und TED einzeln zu sichten, liegt morgens
eine Liste vor, die nach dem eigenen CPV-Profil, dem Einzugsgebiet und der
Auftragsgröße gefiltert ist.

Im zweiten Schritt liest die KI die Vergabeunterlagen: über 100 Seiten in rund
30 Sekunden, mit automatischer Erkennung von Fristen, Auftragswert,
Losstruktur, Eignungsanforderungen und K.-o.-Kriterien — jeder Befund verlinkt
auf die Fundstelle im Originaldokument. Im dritten Schritt erstellt der AI Chat
Angebotsunterlagen, Eigenerklärungen, Kalkulationstabellen und Begleitschreiben
direkt aus Ausschreibungs- und Unternehmensdaten.

Im IT-Segment trifft dieser Standard auf ein Vergabegeschehen, das sich
über drei CPV-Säulen verteilt: **IT-Dienstleistungen** (CPV 72, 3.299
Nennungen in zwölf Monaten), **Softwarepakete und Informationssysteme**
(CPV 48, 1.494) und **Datenverarbeitungsgeräte** (CPV 30, 926), ergänzt um
Telekommunikation (CPV 64) sowie Wartung und Installation (CPV 50/51). Die
Verfahren tragen Titel wie „Softwareprogrammierung und -beratung —
Framework-Vertrag", „Dienstleistungen im Sektor Informationssicherheit" oder
„Rahmenvertrag Magnetbandkassetten" — also Beratung, Entwicklung,
Infrastruktur und Betrieb in einem Segment, das fast durchgängig über
Rahmenvereinbarungen und Mehrlosverfahren vergeben wird. Genau dort liegt der
Nutzen der Dokumentenanalyse: Die Losstruktur entscheidet, ob ein Verfahren
überhaupt zum eigenen Portfolio passt, und sie steht selten im Titel.

Anders als für Pharma und Bau hat Patterno für die IT **keine
Branchenspezialisierung** gebaut. Das bestehende Playbook benennt das in
Kapitel 4 als Grund, das Segment zurückzustellen, und formuliert die
Reaktivierungsbedingung: „Eine IT-Spezialisierung (z. B. EVB-IT-Logik) im
Produkt existiert." Diese Lücke wird hier nicht kaschiert — sie ist aber auch
nicht das entscheidende Verkaufsargument. Was die Standardfunktionen in
IT-Vergabeunterlagen finden, ist fachlich anspruchsvoll genug: EVB-IT-Vertragstyp
und -Anlagen, Eignungsnachweise wie BSI-Grundschutz, ISO 27001 oder BSI C5,
Präqualifikation, Nachunternehmerregelungen, Service-Level und Vertragslaufzeiten
samt Verlängerungsoptionen. Die Spezifität dieses Playbooks entsteht deshalb
nicht aus einer Produktfunktion, sondern aus den Daten in der Ansprache
(Kapitel 9).

### Allgemeines Wertversprechen

Patterno verwandelt einen fragmentierten, personalintensiven Suchprozess in
einen automatisierten Entscheidungsprozess. Der Kunde sieht mehr vom Markt
(Abdeckung), sieht ihn früher (tägliche Trefferliste), entscheidet schneller
(Analyse in Sekunden statt Stunden) und bewirbt sich häufiger, ohne
zusätzliches Personal einzustellen.

Der wirtschaftliche Hebel liegt nicht im Software-Preis, sondern in der
Kapazität: Jede Stunde, die heute in Portalsichtung und Unterlagenlesen
fließt, ist eine Stunde, die nicht in Kalkulation, Preisstrategie und
Angebotsqualität geht. Bei einem Angebotsaufwand von 16 bis 30 Stunden je
Bewerbung amortisiert sich die Plattform bereits, wenn sie ein einziges
aussichtsloses Verfahren frühzeitig aussortiert — oder ein passendes
rechtzeitig sichtbar macht.

Im IT-Segment kommt ein zweiter Hebel dazu, der in den Daten sichtbar ist:
**Wiederholung.** 236 Unternehmen bestreiten drei oder mehr Verfahren pro Jahr,
das aktivste 131 — verteilt auf bis zu 92 verschiedene Auftraggeber. Bei
dieser Frequenz ist die Sichtung kein Nebenjob mehr, sondern eine Stelle.
Qualifizierte Bid- und Angebotsmanager sind am Markt jedoch kaum verfügbar.
Automatisierung ist deshalb nicht die günstigere Variante der Einstellung,
sondern häufig die einzig verfügbare.

### Produkt-Übersicht

| Produkt / Funktion | Nutzen für ein IT-Systemhaus |
|---|---|
| **Patterno HIT** | Qualifizierte KI-Suche über 4.500+ Portale, gefiltert nach CPV-Profil (48/72/302/5031/5032/5161/642), Region und Auftragswert |
| **Patterno BID** | Vergabeunterlagen geprüft auf EVB-IT-Bezug, Losstruktur, Eignungsnachweise, BSI-Grundschutz-, ISO-27001- und C5-Anforderungen |
| **AI Chat** | Eigenerklärungen, Referenzlisten, Kalkulationstabellen und Begleitschreiben direkt aus den Vergabedaten |
| **Dokumentenextraktion** | Vergabeunterlagen automatisch aus allen Portalen gezogen und strukturiert — ohne manuellen Download je Portal |
| **Wettbewerbsansicht** | Wer hat im eigenen CPV-Segment und in der eigenen Region zuletzt den Zuschlag bekommen |
| **Pipeline- und Fristen-Tracking** | Rahmenvertragsenden, Bieterfragenfristen und Submissionstermine im Team statt in Einzel-Excels |
| **Tender Intelligence** | Vergabetrends und Preisentwicklung je CPV-Segment als Kalkulationsgrundlage |
| **Sicherheit und Betrieb** | Deutsche Server (Frankfurt), DSGVO-konform, ISO-27001-Infrastruktur, SSO und AVV/NDA im Enterprise-Paket — im öffentlichen IT-Geschäft regelmäßig selbst Prüfkriterium |

### Orientierung: typische Investitionsrahmen

| Paket | Rahmen (Richtwert) | Passung im Segment | Accounts |
|---|---|---|---|
| Starter | ab 89 € / Monat | ein Verfahren im Jahr, gelegentliche Teilnahme — meist Tier C | 1.768 |
| Team | ab 269 € / Monat | 2 Verfahren, eigene Angebotsbearbeitung — Tier B/C | 361 |
| Scale | ab 449 € / Monat | 3–20 Verfahren, mehrere Auftraggeberkreise — **Tier A/B** | 322 |
| Enterprise | ab 2.249 € / Monat | über 20 Verfahren, Dauerbieter mit eigener Bid-Funktion — **Tier A** | 17 |

Preise netto, bei jährlicher Vorauszahlung. Im Erstkontakt dienen die Zahlen
als Gesprächsanker, nicht als Angebot — aktuelle Konditionen vor Nennung
intern bestätigen.

Die Zuordnung ist aus den Daten ableitbar: `participations_total` und
`buyers_total` in `longlist_markt.csv` sagen, wie viele Verfahren und wie
viele Auftraggeberkreise ein Unternehmen tatsächlich bedient. Ein Haus mit
20 Verfahren bei 19 Auftraggebern (d.velop AG) gehört in ein anderes Gespräch
als eines mit einem einzigen Verfahren.

---

## 4. Fokus-Entscheidung: warum zwei Use Cases statt zwei Branchen

Das bestehende Playbook trennt nach Branche, weil dort die Produktspezialisierung
liegt (Pharma-Agenten, VOB-/LV-Prüfung). Innerhalb der IT-Systemhäuser gibt es
diese Trennung nicht — die Produktargumente sind für alle gleich.

Was sich unterscheidet, ist etwas anderes: **ob es gerade einen Anlass gibt.**
Daraus folgen zwei Use Cases mit unterschiedlicher Kadenz, unterschiedlicher
Botschaft und unterschiedlichem Erfolgsmaßstab.

| Kriterium | Use Case 1: Marktabdeckung | Use Case 2: Anlassbasiert |
|---|---|---|
| Datenquelle | `longlist_markt.csv` | `longlist_signale.csv` |
| Umfang | 2.458 Unternehmen | 651 Accounts, 200 über Score-Schwelle |
| Rolle in der Kampagne | Basis — das gesamte adressierbare Universum | Spitze — wer diese Woche einen Grund hat |
| Kadenz | einmalig aufgebaut, quartalsweise aktualisiert | wöchentlicher Lauf |
| Aufhänger | belegte Teilnahmehistorie | konkretes Ereignis mit Datum |
| Erfolgsmaß | Abdeckung und Listenqualität | Antwortquote je Signaltyp |
| Lead-Produkt | Patterno HIT | Patterno BID |

**Die Schnittmenge ist Welle 1:** 236 Unternehmen stehen in Tier A, 148 davon
haben ein frisches Signal, **81 erfüllen beides und liegen über der
Score-Schwelle.** Das ist die Liste, mit der eine Kampagne startet.

### Bewusst ausgeschlossen

| Gruppe | Warum | Umsetzung |
|---|---|---|
| Öffentliche Inhouse-Dienstleister | Dataport, ITZBund, AKDB, Komm.ONE, regio iT, ekom21, KRZN — Auftraggeberseite, nicht Zielkunde | Ausschlussliste in `src/config.py` |
| Vergabeportale und -software | cosinex, Administration Intelligence, subreport, DTVP, Vergabe24, Staatsanzeiger | Ausschlussliste |
| Vergaberechtskanzleien | tauchen in TED als Verfahrensbegleiter auf und wurden dort zunächst fälschlich als Bieter gelesen | Ausschlussliste, zweite Verteidigungslinie |
| Distribution und Handel | Cyberport, notebooksbilliger, Alternate — kein Systemhaus-Motion | Ausschlussliste |
| Personaldienstleister | Hays, FERCHAU, GULP — vermitteln, bieten nicht | Ausschlussliste |
| Vergabestellen als Accounts | Ein offenes Verfahren gehört der Vergabestelle, nicht einem Bieter | eigener Feed `offene_verfahren.csv`, **nie Outbound** |

---

## 5. Use Case 1: Marktabdeckung — `longlist_markt.csv`

**2.458 Unternehmen mit belegter Teilnahme an öffentlichen IT-Vergaben.**

### Segmentbeschreibung

IT-Systemhäuser, IT-Dienstleister und Managed-Service-Provider, die
nachweislich an öffentlichen Ausschreibungen teilnehmen. Das Universum entsteht
nicht aus einem Branchenverzeichnis, sondern aus den Vergabedaten selbst: Jede
Zeile trägt eine Bekanntmachung mit Datum und PDF.

**Wie viel davon ist der Markt?** Gemessen, nicht geschätzt
([vollstaendigkeit.md](vollstaendigkeit.md)): Fang-Wiederfang über zwölf
monatliche Beobachtungsgelegenheiten setzt die Population auf **mindestens
6.798** Unternehmen — die Liste deckt also **höchstens 36 %** ab. 73 % der
erfassten Firmen tauchen in genau einem von zwölf Monaten auf, die Signatur
einer unterabgetasteten Grundmenge.

Daneben liegt ein blinder Fleck, der in dieser Zahl **nicht** enthalten ist:
Rund 90 % der öffentlichen Aufträge in Deutschland sind unterschwellig, im
Korpus liegen aber 77 % der bewerteten Verfahren über der EU-Schwelle. Genau
unterhalb arbeiten die Systemhäuser im ICP-Korridor von 50 bis 2.000
Mitarbeitenden. Für die Ansprache heißt das: Die Liste ist eine belastbare
Basis, aber kein vollständiges Universum — wer hier niemanden findet, hat
daraus keinen Schluss gezogen.

Regionaler Schwerpunkt Tier A: Berlin (23), München (13), Hamburg (12),
Frankfurt am Main (10), Stuttgart (9), Bonn (9), Düsseldorf (9), Köln (9) —
verteilt über alle PLZ-Zonen, kein regionaler Klumpen.

### Buying Center

Aus einem echten Apollo-Lauf gegen fünf Tier-A-Accounts, nicht aus einer
Wunschliste. Die vollständigen Titellisten stehen in
[`apollo_filter.md`](apollo_filter.md).

**Champion — Bid & Tender (Priorität 1)**
Bid Manager, Senior Bid Manager, Bid Managerin, Bid & Proposal Manager,
Proposal Manager, Tender Manager, Tender Managerin, Team Lead Tender Management,
Ausschreibungsmanager, Angebotsmanager, Leiter Angebotswesen, Bietermanagement,
Submission, Vergabemanagement, Referent Ausschreibungen

**Economic Buyer (Priorität 2)**
Geschäftsführer, Geschäftsführender Gesellschafter, Managing Director, Inhaber,
Vorstand, Kaufmännischer Leiter, Prokurist, Vertriebsleiter, Head of Sales,
Head of Public Sector, Leiter Öffentliche Auftraggeber, Niederlassungsleiter

**Nutzer & interne Fürsprecher (Priorität 3)**
Key Account Manager Public Sector, Account Manager Public, Vertriebsbeauftragter
Öffentliche Auftraggeber, Pre-Sales Consultant, Solution Sales Manager,
Projektleiter Öffentliche Auftraggeber

### Die Tier-Logik

Das Tier hängt **ausschließlich an Vergabedaten** — nicht an der
Mitarbeiterzahl. Begründung in [`tiering.md`](tiering.md); kurz: Die Zahl fehlte
bei allen 2.458 Zeilen und war dort, wo sie vorlag, bei 5 von 10 Firmen die des
Konzerns statt die des bietenden Rechtsträgers.

| Tier | Regel | n | Ansprache |
|---|---|---|---|
| **A** | ≥ 3 Verfahren **und** Beleg ≤ 180 Tage | 233 | Welle 1 — laufender Angebotsprozess |
| **B** | ≥ 2 Verfahren, oder 1 Verfahren mit frischem Beleg | 1.261 | Welle 2 — wiederkehrender Bieter |
| **C** | belegt, aber weder häufig noch aktuell | 964 | Nurture, kein aktives Outbound |

Jede Zeile trägt die nachrechenbare Begründung:

> „17 Verfahren in 12 Monaten, jüngster Beleg vor 1 Monat, 15 verschiedene
> Auftraggeber — laufender Angebotsprozess" *(Controlware GmbH)*

### Belegqualität: `tier_status`

| Wert | n | Bedeutung für die Ansprache |
|---|---|---|
| `zuschlag_benannt` | 335 | „Sie haben … gewonnen" — direkt zitierbar |
| `zuschlag_erschlossen` | 1.727 | einziger Bieter → Zuschlag abgeleitet; **Beleg-URL vor Ansprache prüfen** |
| `teilnahme_offen` | 402 | „Sie haben sich beteiligt" — mehr geben die Daten nicht her |
| `schwacher_beleg` | 4 | nicht ansprechen |

Der Unterschied ist nicht akademisch, er entscheidet den ersten Satz. Bei
`zuschlag_erschlossen` ist die Formulierung „Sie haben gewonnen" eine
Schlussfolgerung, keine Tatsache aus der Bekanntmachung.

### Warum dieses Segment investieren würde

- **Der Angebotsprozess existiert nachweislich.** 236 Unternehmen bestreiten
  drei oder mehr Verfahren pro Jahr mit frischem Beleg. Das ist keine Annahme
  über ihre Branche, das steht in den Bekanntmachungen.
- **Der Markt ist fragmentiert, gerade unterschwellig.** Kommunale IT-Vergaben
  liegen auf Landesportalen und Kommunalplattformen, nicht auf TED.
- **Bid-Kapazität ist der Flaschenhals.** Qualifizierte Bid- und
  Angebotsmanager sind am Markt kaum verfügbar; Automatisierung ist bei
  wachsender Verfahrenszahl der einzige realistische Hebel.
- **EVB-IT und UfAB erzeugen formale Fallen.** Eignungsnachweise, BSI-Grundschutz,
  ISO 27001, Präqualifikation — jedes übersehene Kriterium entwertet die
  Kalkulation.
- **Breite kostet Personentage.** Ein Unternehmen mit 92 verschiedenen
  Auftraggebern in zwölf Monaten sichtet entsprechend viele Quellen.

### Schmerzpunkte nach Rolle

**Bid- / Angebotsmanagement (operative Bearbeitung)**
- **Das Ausschlusskriterium steht im Anhang** — eine Zertifizierungsanforderung
  oder ein Nachunternehmerverbot entscheidet über das Angebot und wird beim
  Querlesen übersehen.
- **Fachfremde Lose im Paket** — Sammelvergaben mischen IT mit Bau- oder
  Möbelgewerken; die Passung klärt sich erst im Dokument.
- **Nachweispakete immer wieder neu** — Referenzen, Versicherungssummen,
  BSI-Zertifikate und Eigenerklärungen werden für jedes Verfahren neu
  zusammengestellt.
- **Fristen über verstreute Kanäle** — Submissionstermine, Bieterfragenfristen
  und Nachforderungen kommen über mehrere Portale ohne zentrale Übersicht.
- **Wissen hängt an Einzelpersonen** — die Verfahrenshistorie steckt in ein bis
  zwei Köpfen; Urlaub und Fluktuation sind ein Verfahrensrisiko.

**Vertrieb Public Sector (Marktabdeckung)**
- **Mehrere Portale, mehrere Logins** — kein Kanal zeigt das Gesamtbild.
- **Masse statt Passung** — Schlagwortsuchen liefern Treffer, die Sichtung
  bindet täglich Stunden ohne Wertbeitrag.
- **Rahmenverträge laufen aus, ohne dass es auffällt** — das Vertragsende ist
  öffentlich, wird aber von niemandem systematisch ausgewertet.
- **Kein Bild vom Wettbewerb** — wer in der Region zu welchen Konditionen den
  Zuschlag bekommt, wird nicht ausgewertet.

**Geschäftsführung / Public-Sector-Leitung (Entscheider)**
- **Kalkulationskapazität ist der Flaschenhals**, nicht die Auftragslage.
- **Trefferquote ohne Datengrundlage** — wie viele Angebote zu wie vielen
  Zuschlägen führen, wird selten systematisch ausgewertet.
- **Regionale Ausweitung ohne Mehrpersonal** scheitert an der Recherche.
- **Abhängigkeit von wenigen Auftraggebern** — die Verbreiterung scheitert am
  Überblick, nicht am Können.

### Kernbotschaften

- **Alle Portale, ein Posteingang** — über 4.500 Quellen nach CPV-Profil,
  Region und Auftragswert gefiltert.
- **Go oder No-Go in zwei Minuten** — die KI liest die kompletten
  Vergabeunterlagen und prüft gegen Ihre Eignungskriterien.
- **Jeder Fund mit Fundstelle** — belastbar für Bieterfragen, Kalkulation und
  spätere Nachträge.
- **Bringen Sie Ihre letzte Ausschreibung mit** — in 30 Minuten sehen Sie, was
  Patterno darin findet. Kein Foliensatz, ein Test.

### Beispiel-Zielunternehmen aus Tier A

| Unternehmen | Sitz | Verfahren | Auftraggeber | Belegart |
|---|---|---|---|---|
| Controlware GmbH | Dietzenbach | 17 | 15 | Zuschlag benannt |
| think about IT GmbH | Münster | 21 | 16 | Zuschlag erschlossen |
| sysGen GmbH | Bremen | 20 | 15 | Zuschlag benannt |
| d.velop AG | Gescher | 20 | 19 | Zuschlag erschlossen |
| msg systems ag | Ismaning | 18 | 14 | Zuschlag benannt |
| MR Datentechnik | Nürnberg | 6 | 6 | Zuschlag benannt |
| WBS IT-Service GmbH | Leipzig | 6 | 5 | Zuschlag benannt |

*Prospecting-Ziele mit belegtem Bedarf, keine bestehenden Kundenbeziehungen.
Vor Ansprache prüfen, ob bereits ein Ausschreibungstool im Einsatz ist.*

### Nachrichten-Gerüst — Use Case 1

Die Personalisierungszeile kommt aus der Zeile selbst. Die Felder in eckigen
Klammern sind Spaltennamen aus `longlist_markt.csv`.

**E-Mail 1 — Erstkontakt (Bid- / Angebotsmanagement)**

> **Betreff:** [buyers] und [buyers_total−1] weitere — Ihr Angebotsprozess 2026
>
> Sehr geehrte/r [Name],
>
> Ihr Haus ist in den letzten zwölf Monaten in **[participations_total]
> öffentlichen IT-Vergaben** als Bieter geführt, zuletzt bei „[title]" für
> [buyers] — verteilt auf **[buyers_total] verschiedene Auftraggeber**.
>
> Bei dieser Frequenz entscheidet nicht die Auftragslage über die Trefferquote,
> sondern die Kapazität in der Angebotsbearbeitung. Patterno bündelt über 4.500
> Vergabeportale in einem Posteingang und liest die Vergabeunterlagen — über
> 100 Seiten in rund 30 Sekunden, jeder Befund verlinkt auf die Fundstelle.
>
> Bringen Sie Ihre letzte Ausschreibung mit, dann sehen Sie in 30 Minuten, was
> Patterno darin findet. Passt [Terminvorschlag]?
>
> Beste Grüße, Leon Brunner

**E-Mail 2 — Follow-up (Vertrieb Public Sector)**

> **Betreff:** Re: 88 % der Vergaben stehen nicht auf TED
>
> Sehr geehrte/r [Name],
>
> 88 Prozent der öffentlichen Vergaben liegen unter der EU-Schwelle und sind
> über Landesportale, Kommunalplattformen und Amtsblätter verstreut. Wer nur
> die großen Quellen prüft, sieht die Spitze des Eisbergs.
>
> Ihre bisherigen Auftraggeber — [buyers] — zeigen, dass Sie kommunal und auf
> Landesebene unterwegs sind. Genau dort ist die Streuung am größten.
>
> Hätten Sie diese Woche 20 Minuten?
>
> Beste Grüße, Leon Brunner

**E-Mail 3 — Entscheider (Geschäftsführung / Leitung Public Sector)**

> **Betreff:** [legal_name] — mehr Angebote ohne zusätzlichen Bid Manager
>
> Sehr geehrte/r [Name],
>
> als [Position] kennen Sie den Engpass: Die Auslastung in zwölf Monaten hängt
> an der Zahl der Angebote heute — und der Flaschenhals ist die
> Angebotskapazität. Qualifizierte Bid Manager sind am Markt kaum verfügbar.
>
> Patterno setzt an beiden Enden an: vollständige Marktabdeckung über 4.500
> Portale und eine automatische Dokumentenanalyse, die aussichtslose Verfahren
> aussortiert, bevor Ihr Team Stunden hineinsteckt.
>
> Ich zeige Ihnen das gerne an einer echten Ausschreibung aus Ihrem
> CPV-Segment.
>
> Beste Grüße, Leon Brunner

**LinkedIn — Kontaktanfrage (max. 300 Zeichen)**

> Hallo [Name], Ihr Haus ist 2026 in [participations_total] öffentlichen
> IT-Vergaben als Bieter geführt. Wir bündeln bei Patterno über 4.500
> Vergabeportale und prüfen Vergabeunterlagen automatisch auf K.-o.-Kriterien.
> Ich tausche mich gerne mit Angebotsverantwortlichen aus.

---

## 6. Use Case 2: Anlassbasierte Ansprache — `longlist_signale.csv`

**651 Accounts mit einem Ereignis aus den letzten acht Wochen, 200 über der
Score-Schwelle.**

### Was der Use Case leistet

Use Case 1 sagt, *wen* man ansprechen kann. Use Case 2 sagt, *wer diese Woche
einen Grund hat* — und liefert den Satz gleich mit. Die Pipeline läuft
wöchentlich und gibt beim zweiten Lauf ohne neue Daten **null Zeilen** aus.
Das ist getestet, nicht behauptet.

### Die Signaltypen

| Signal | Gewicht | Accounts* | Was es bedeutet |
|---|---|---|---|
| `rahmenvertrag_laeuft_aus` | 9 | 6 | Vertragsende in 180–270 Tagen — die Neuausschreibung kommt |
| `angebot_ohne_zuschlag` | 8 | 0 | geboten, ein anderer bekam den Zuschlag (in 12 Monaten nur 1 Fall im Markt) |
| `offene_ausschreibung_im_profil` | 8 | 0 | 196 laufende Verfahren mit Frist — nennen aber den Auftraggeber, nicht den Bieter (siehe unten) |
| `bid_rolle_ausgeschrieben` | 7 | 1 | Stellenanzeige für Bid-/Tender-Rolle = akuter Kapazitätsschmerz |
| `zuschlag_gewonnen` | 6 | 634 | frischer Zuschlag — im selben CPV-Segment laufen weitere Verfahren |
| `teilnahme_belegt` | 5 | 10 | Bieter benannt, Ausgang nicht ableitbar |

\* Accounts, bei denen dieses Signal den Score **treibt**. Ein Account kann
mehrere Signaltypen tragen; der Stacking-Bonus greift ab zwei verschiedenen.
124 der 651 Accounts tragen mehr als einen Signaltyp.

**Warum die Stellenanzeige so selten zählt:** In acht Wochen erschienen
bundesweit 79 Anzeigen für Bid-, Tender- und Angebotsrollen — quer über alle
Branchen. Nach dem Abgleich gegen die Vergabedaten blieben **2 mit
IT-Vergabebeleg**; 35 wanderten in den Prüfbestand
(`job_signale_ohne_icp_beleg.csv`). Eine Stellenanzeige belegt einen
Kapazitätsschmerz, aber kein IT-Systemhaus: Ohne Branchenfilter finden sich
darunter Bauunternehmen, Versorger (auf der Auftraggeberseite!) und Biotech.
Der Signaltyp taugt deshalb als Einzelanlass, nicht als Marktargument — und
er zählt nur für Firmen, die über die Vergabedaten bereits als IT belegt sind.

**Die 196 offenen Verfahren sind ein Rohstoff, kein Anlass.** Die Angebotsfrist
laufender Ausschreibungen steht nicht im OCDS-JSON, sondern erst im eForms-XML
(BT-131). Sie wird jetzt gelesen und liegt in `offene_verfahren.csv` — aber eine
laufende Ausschreibung nennt den **Auftraggeber**, nicht den Bieter. Wer sich
bewerben wird, steht erst nach der Frist in den Daten. Nutzbar wird das erst
über die Verbindung zu Use Case 1: *„Die Uni Jena schreibt eine
I-Doit-Verlängerung aus, Frist in 13 Tagen — und Sie haben bei genau dieser
Vergabestelle schon zweimal geboten."* Dieser Join ist billig, aber bewusst
nicht gebaut: Er erzeugt eine Ansprache zu einem Verfahren, an dem das
Unternehmen noch gar nicht teilnimmt. Ob das hilfreich wirkt oder übergriffig,
ist eine Produktentscheidung.

**Der wertvollste ist der seltenste.** `rahmenvertrag_laeuft_aus` ist datiert,
öffentlich belegbar und in keinem Standard-Sales-Tool enthalten — er entsteht
rein rechnerisch aus dem Vertragsende am Los. Genau dieser Signaltyp trifft den
im bestehenden Playbook zitierten Befund *„19 Prozent finden zu spät"*: Er meldet,
bevor die Ausschreibung überhaupt existiert.

### Das Scoring

Multiplikativ, nicht additiv: Gewicht × Aktualität × ICP-Fit × Confidence, plus
Stacking-Bonus bei mehreren Signaltypen. Die Confidence dämpft alles andere —
ein starkes Signal auf einem Account mit wackliger Firmenzuordnung rutscht
nicht nach oben.

Die Enrichment-Schwelle liegt bei **40** und ist an der gemessenen Verteilung
kalibriert, nicht geraten: 200 von 651 Accounts (31 %) liegen darüber, knapp
über dem Zielkorridor von 20–30 %. Maßgeblich war die Klippe zwischen 40 und
45 (200 → 77), nicht die runde Zahl. Die vollständige Score-Zerlegung je Account steht in
`score_trace.csv`.

### Die Top-Accounts mit „Why now"

| Score | Tier | Account | Anlass |
|---|---|---|---|
| 85 | A | SCALTEL GmbH & Co. KG | Rahmenvertrag „Dienstleistung Infrastruktur Netzwerk-Firewall" mit dem Universitätsklinikum Düsseldorf endet am 31.03.2027 |
| 85 | A | Cassini Consulting AG | Rahmenvertrag „IT-Roadmap der Sächsischen Krankenhäuser" mit dem Sächsischen Staatsministerium endet 2027 |
| 68 | A | Semper Prospera GmbH | Rahmenvertrag „Unterstützung ELFE Programmierung Cobol" mit dem Bayerischen Landesamt für Steuern endet 2027 |
| 67 | A | Sopra Steria SE | Zuschlag am 21.09.2026 für „ELS – Archivsystem IGNIS Plus" (Berliner Feuerwehr) |
| 62 | A | sysGen GmbH | Zuschlag am 23.09.2026 für „Rahmenvereinbarung Hochleistungsrechner" (Universitätsklinikum Aachen) |
| 62 | A | CANCOM GmbH | Zuschlag am 23.09.2026 für „Check Point Firewall" (Klinikum St. Georg) |
| 62 | A | Titanom Solutions GmbH | Zuschlag am 18.09.2026 für das Hamburgische Lobbyregister der Bürgerschaft |

### Nachrichten-Gerüste — Use Case 2

Hier ist die Personalisierungszeile **maschinell erzeugt**. Der Satz steht in
der Spalte `why_now`, die Quelle in `quell_url`.

**Signal `rahmenvertrag_laeuft_aus` — der stärkste Aufhänger**

> **Betreff:** [buyer] — Ihr Rahmenvertrag läuft im [Monat/Jahr] aus
>
> Sehr geehrte/r [Name],
>
> [why_now — z. B. „Ihr Rahmenvertrag ‚Dienstleistung Infrastruktur
> Netzwerk-Firewall' mit dem Universitätsklinikum Düsseldorf endet am
> 31.03.2027 — die Neuausschreibung startet erfahrungsgemäß rund sechs Monate
> vorher."]
>
> Quelle: [quell_url]
>
> Das heißt: Die Unterlagen kommen im Herbst. Wer die Vorgängerausschreibung
> daneben legt und die geänderten Klauseln kennt, kalkuliert schneller und
> sicherer als der Wettbewerber, der bei null anfängt.
>
> Patterno liest beide Fassungen, zeigt neue, geänderte und gestrichene
> Anforderungen und verlinkt jeden Befund auf die Fundstelle. In 30 Minuten
> zeige ich Ihnen das an genau diesem Verfahren.
>
> Beste Grüße, Leon Brunner

**Signal `zuschlag_gewonnen` — Anschlussverfahren**

> **Betreff:** Glückwunsch zum Zuschlag — und was als Nächstes kommt
>
> Sehr geehrte/r [Name],
>
> [why_now — z. B. „Sie haben am 23.09.2026 den Zuschlag für ‚Check Point
> Firewall' (Klinikum St. Georg gGmbH) erhalten."]
>
> Im selben CPV-Segment laufen aktuell weitere Verfahren — die Frage ist, ob
> Ihr Team sie rechtzeitig sieht. Bei [participations_total] Verfahren in zwölf
> Monaten ist die Sichtung kein Nebenjob mehr.
>
> Patterno filtert die passenden Verfahren nach Ihrem Profil vor und liest die
> Unterlagen, bevor Ihr Team einsteigt.
>
> Hätten Sie 20 Minuten?
>
> Beste Grüße, Leon Brunner

**Signal `bid_rolle_ausgeschrieben` — Kapazitätsschmerz**

> **Betreff:** Bid Manager gesucht — bis die Stelle besetzt ist
>
> Sehr geehrte/r [Name],
>
> Sie suchen aktuell [Stellentitel]. Bis eine solche Stelle besetzt ist,
> vergehen erfahrungsgemäß Monate — die Verfahren laufen weiter.
>
> [why_now]
>
> Patterno überbrückt genau diese Lücke: Vorqualifizierung der Treffer und
> automatische Dokumentenanalyse. Das ersetzt keine Einstellung, verschafft
> Ihrem Team aber die Zeit bis dahin.
>
> Beste Grüße, Leon Brunner

**Signal `angebot_ohne_zuschlag` — nur mit Fingerspitzengefühl**

> Kein Standard-Gerüst. Eine Niederlage anzusprechen, funktioniert nur, wenn
> die Formulierung den Aufwand würdigt statt das Ergebnis zu benennen:
> „Sie haben sich am [Datum] an [Verfahren] beteiligt — bei einem Verfahren
> dieser Größe stecken schnell zwei Personenwochen im Angebot."
> Diesen Signaltyp nie automatisiert versenden.

---

## 7. Leistungs-Use-Case-Relevanz-Matrix

Legende: **+++** PRIMÄR · **++** HOCH · **+** ERGÄNZEND · **–** nicht relevant

| Leistung | UC 1 Marktabdeckung | UC 2 Anlassbasiert |
|---|---|---|
| Patterno HIT (Qualifizierte KI-Suche) | **+++** | ++ |
| Patterno BID (KI-Dokumentenanalyse) | ++ | **+++** |
| AI Chat (Angebots- und Dokumentenerstellung) | ++ | ++ |
| Fristen- und Pipeline-Management | ++ | **+++** |
| Wettbewerbsansicht / Submissionsergebnisse | ++ | **+++** |
| Tender Intelligence / Marktanalysen | + | ++ |
| Dokumentenextraktion | ++ | ++ |
| EU-weite Abdeckung (29 Länder) | + | + |
| Enterprise-Rahmen (SSO, AVV, API, SLA) | + | ++ |
| Pharma-Agenten / VOB-LV-Prüfung | – | – |

---

## 8. Quick-Reference für Sales-Gespräche

| Use Case | Lead-Leistung | Wichtigste Argumente |
|---|---|---|
| Marktabdeckung | Patterno HIT | 4.500+ Portale in einem Posteingang, 88 % der Vergaben nicht auf TED, Filter nach CPV-Profil und Region |
| Anlassbasiert | Patterno BID | Vorgängervergleich vor der Neuausschreibung, Go/No-Go in 2 Minuten, jeder Befund mit Fundstelle |

### Die drei Argumente für jedes Gespräch

1. **Sie sehen mehr vom Markt** — 88 Prozent der Vergaben stehen nicht auf TED;
   über 4.500 Portale in einem Zugang schließen genau diese Lücke.
2. **Sie entscheiden früher und sicherer** — über 100 Seiten Unterlagen in rund
   30 Sekunden, K.-o.-Kriterien und Fristen automatisch erkannt, jeder Befund
   mit Fundstelle.
3. **Sie bewerben sich häufiger, ohne Personal aufzubauen** — die eingesparte
   Sichtungs- und Lesezeit fließt in Kalkulation und Preisstrategie; bei knappem
   Fachpersonal der einzige realistische Hebel.

### Die Eröffnung, die in beiden Use Cases funktioniert

Kein Foliensatz, ein Test: **„Bringen Sie Ihre letzte Ausschreibung mit — in
30 Minuten sehen Sie, was Patterno darin findet."** Das verlagert das Gespräch
von Versprechen auf Beweis und qualifiziert gleichzeitig: Wer ein echtes
Verfahren mitbringt, hat ein echtes Problem.

---

## 9. Personalisierung: was die Pipeline liefert und was nicht

Das bestehende Playbook nennt dieses Kapitel „das wichtigste des Playbooks" und
veranschlagt 5–10 Minuten Handrecherche je Account. Für dieses Segment liefert
die Pipeline vier der fünf Pflichtpunkte maschinell.

| Pflichtpunkt (Kapitel 9 Original) | Herkunft hier | Aufwand |
|---|---|---|
| 1. Konkreter Vergabeanlass | `why_now` + `proof_url` + `signal_datum` | **0 min** |
| 2. Rolle und Zuständigkeit | Persona-Zuordnung aus dem Apollo-Filter | **0 min** |
| 3. Unternehmensspezifisches Detail | `participations_total`, `buyers`, `buyers_total`, `cpv_profile` | **0 min** |
| 4. Aktueller Auslöser | `signal_type` + `signal_datum` | **0 min** |
| 5. Passgenauer Nutzenbeweis | Signaltyp → Modulzuordnung (Kapitel 6) | **0 min** |
| **Prüfung** | Beleg öffnen, ICP-Passung bestätigen | **1–2 min** |

### Das Qualitäts-Gate bleibt — nur verschiebt es sich

Der Austausch-Test aus dem Original gilt unverändert: Ersetzen Sie den
Firmennamen durch den eines Wettbewerbers. Bleibt der Satz wahr, ist er nicht
personalisiert.

> **Nicht personalisiert:** „Ich habe gesehen, dass Sie IT-Dienstleistungen für
> die öffentliche Hand erbringen." — trifft auf 2.458 Unternehmen zu.
>
> **Personalisiert:** „Ihr Rahmenvertrag ‚Dienstleistung Infrastruktur
> Netzwerk-Firewall' mit dem Universitätsklinikum Düsseldorf endet am
> 31.03.2027." — trifft auf ein Unternehmen zu, mit PDF daneben.

### Drei Prüfungen, die kein Skript übernimmt

**1. Ist es überhaupt ein Systemhaus?**
Die CPV-Klassifikation belegt Teilnahme an IT-Vergaben, nicht das
Geschäftsmodell. Unter den Top-Signalen stehen Siemens (Gebäudeautomation),
ein Quantencomputer-Lieferant und ein Verkehrszählanbieter. **Der
Systemhaus-Klassifikator fehlt noch** — bis dahin ist das eine Sichtprüfung
vor dem Versand.

**2. Hält der Beleg, was die Zeile behauptet?**
Bei `tier_status = zuschlag_erschlossen` (1.727 Zeilen) ist der Zuschlag
abgeleitet, nicht benannt. Die Formulierung „Sie haben gewonnen" ist dort eine
Schlussfolgerung. Beleg-URL öffnen, dann formulieren.

**3. Ist die Domain die richtige?**
Von zwölf automatisch aufgelösten Domains waren acht falsch — `dedalus.at`
statt Bonn, `msg-systems.ro` statt Ismaning, `eominnesota.org` für die EOMI AG
aus Hamburg. Die Impressum-Prüfung nach § 5 DDG fängt das ab; Details in
[`waterfalls.md`](waterfalls.md).

### Sequenz-Takt je Prospect

| Schritt | Kanal | Inhalt | Abstand |
|---|---|---|---|
| 1 | LinkedIn | Vernetzung mit Bezug auf das Verfahren, kein Pitch | Tag 0 |
| 2 | E-Mail 1 | Rollenspezifischer Erstkontakt mit `why_now` | Tag 2–3 |
| 3 | E-Mail 2 | Follow-up mit Marktzahl oder Report | Tag 6–8 |
| 4 | Telefon | Kurzer Anruf mit Bezug auf die Nachricht | Tag 9–12 |
| 5 | E-Mail 3 | Entscheider-Ansprache oder Break-up | Tag 14–18 |

Maximal vier bis fünf Touches je Prospect in 90 Tagen. Bei Opt-out oder klarer
Absage sofortiger Stopp, kanalübergreifend.

**Besonderheit Use Case 2:** Läuft während einer Sequenz ein neues Signal auf
denselben Account auf, ersetzt es den nächsten geplanten Schritt — es zählt
nicht zusätzlich. Sonst summieren sich Signale zu Belästigung.

---

## 10. Einwandbehandlung

| Einwand | Antwortlinie |
|---|---|
| „Wir haben schon ein Vergabeportal / ein Recherche-Abo." | Portale veröffentlichen, Patterno bietet. Die Frage ist nicht, ob Sie Treffer bekommen, sondern wie viele davon passen — und wer die 200 Seiten Unterlagen liest. Bringen Sie eine Ausschreibung mit, dann vergleichen wir Trefferqualität und Analyse direkt. |
| „Unsere Leute kennen ihren Markt." | Bei den großen Verfahren bestätigt sich das regelmäßig. 88 Prozent der Vergaben liegen unterhalb der EU-Schwelle und erscheinen nur regional — genau dort entstehen die Lücken. |
| „Woher haben Sie diese Information?" | Aus der amtlichen Bekanntmachung, hier ist der Link. Der Datenservice Öffentlicher Einkauf ist CC0-lizenziert und öffentlich. Wir werten aus, was ohnehin veröffentlicht ist. |
| „KI in Vergabeunterlagen — das ist uns zu unsicher." | Deshalb entscheidet die KI nichts. Jeder Befund ist auf die Fundstelle im Originaldokument verlinkt, Ihr Team prüft und entscheidet. Die Zeitersparnis entsteht beim Finden, nicht beim Bewerten. |
| „Datenschutz und IT-Freigabe sind aufwändig." | Verarbeitung ausschließlich in Frankfurt am Main, ISO-27001-zertifizierte Infrastruktur, DSGVO-konform, keine Weitergabe an Dritte. Im Enterprise-Paket SSO, AVV, NDA und individuelles SLA. |
| „Dafür haben wir gerade kein Budget." | Nachvollziehbar. Gegenrechnung: 16 bis 30 Stunden gehen im Schnitt in eine Bewerbung. Wenn die Plattform pro Quartal ein aussichtsloses Verfahren früh aussortiert oder ein passendes rechtzeitig sichtbar macht, hat sie sich getragen. |
| „Wir bieten kaum noch öffentlich." | Dann ist die Zeile falsch zugeordnet — ich nehme Sie heraus. Darf ich fragen, ob das eine Entscheidung war oder am Aufwand lag? |

---

## 11. Apollo.io Filter-Empfehlung

Vollständige Titellisten, Firmenfilter und die Clay-Reihenfolge in
[`apollo_filter.md`](apollo_filter.md). Die Kurzfassung:

| Kriterium | Werte |
|---|---|
| **Industrie** | Information Technology & Services, Computer & Network Security, Computer Software, Computer Hardware, Telecommunications |
| **NAICS / SIC** | 5415, 541512, 541513, 541519, 5112 / 7373, 7379, 7371, 5045 |
| **Mitarbeiter** | 50–2.000, Sweet Spot 50–500 |
| **Standort** | Deutschland |
| **Seniority** | manager, senior, head, director, lead · owner/c_suite bei Betrieben unter ca. 250 MA |
| **Keywords** | Systemhaus, IT-Dienstleister, Managed Services, IT-Infrastruktur, Systemintegration, Rechenzentrum, Digital Workplace, IT-Security, SOC, E-Akte, E-Government, Fachverfahren, Schul-IT, Klinik-IT, EVB-IT, UfAB, VgV, Rahmenvertrag, BSI-Grundschutz, ISO 27001, BSI C5, Präqualifikation |
| **Ausschluss** | Ausschreibungssoftware, Vergabesoftware, Vergabeplattform, eVergabe, DTVP, Vergabe24, Staatsanzeiger, subreport, cosinex, Administration Intelligence, Vergabestelle, Beschaffungsamt, Vergabekammer, Vergaberecht, Dataport, ITZBund, AKDB, Komm.ONE, regio iT, ekom21, KRZN, Zweckverband, Zeitarbeit, Personaldienstleister, Distribution, Großhandel |

### Die drei Fallen aus dem Testlauf

1. **Die Einkaufsseite ist der häufigste Fehltreffer.** „Vergabemanager" sitzt
   genauso in der Kommune wie beim Bieter. Die Blacklist läuft **vor** der
   Whitelist.
2. **Eine Stellenanzeige macht kein Systemhaus.** Ohne Branchenfilter kamen
   Max Bögl (Bau), HAMBURG WASSER (Versorger, Auftraggeberseite) und TRON gGmbH
   (Biotech). Von 31 reinen Job-Treffern waren rund 4 IT-Systemhäuser —
   **13 % Präzision.** Personensuche deshalb immer gegen die
   domainverifizierte Longlist, nie freihändig über Titel.
3. **E-Mail-Domain gegen Account-Domain prüfen.** Zwei von 15 angereicherten
   Kontakten hatten eine abweichende Domain (`…@controlware.at`,
   `t.tabu@arktis.net`).

### Grundsätze

- Eingrenzung über Industrie, Jobtitel und Seniority — nicht über künstlich
  verengte Keywords.
- Patternos eigene Produktbegriffe bleiben **Ausschluss**-Keywords; sie finden
  Wettbewerber, keine Bieter.
- Öffentliche Auftraggeber konsequent ausschließen — sie sind das Gegenüber
  der Zielkunden.
- Drei bis fünf Entscheider je Zielunternehmen: eine operative Rolle, eine
  kaufmännische, eine entscheidende.
- Nur geschäftliche Adressen, keine `info@`-Sammelpostfächer als primärer Kanal.

---

## 12. Hinweise zur Nutzung

- **Welle 1 sind 58 Accounts** — Tier A **und** Score ≥ 40. Nicht mit 2.458
  starten; die Listenbreite ist Reserve, keine Kampagne.
- **Erst scoren, dann anreichern.** Signale kosten nichts, Kontaktdaten schon.
  Personensuche nur für Accounts über der Score-Schwelle — rund **6,3
  Apollo-Credits je qualifiziertem Lead**, Rechnung in
  [`operating_model.md`](operating_model.md).
- **Beleg-URL vor Versand öffnen.** Bei `zuschlag_erschlossen` ist der Zuschlag
  abgeleitet. Ein falsch behaupteter Zuschlag kostet mehr Glaubwürdigkeit als
  zehn ungeöffnete Mails.
- **Kein Outbound aus `offene_verfahren.csv`.** Das sind Vergabestellen — das
  Gegenüber der Zielkunden.
- **Kein Outbound aus `job_signale_ohne_icp_beleg.csv`.** 36 Zeilen mit
  Bid-Rolle, aber ohne IT-Vergabebeleg. Prüfbestand, kein Versand.
- **Signal schlägt Sequenzschritt.** Ein neues Signal ersetzt den nächsten
  geplanten Touch, es addiert sich nicht.
- **Erfolgsmessung je Signaltyp getrennt.** Die Gewichte in `config.py` sind
  begründet, aber unbelegt. Nach rund 200 Kontakten zeigt die Antwortquote je
  Signaltyp, ob `rahmenvertrag_laeuft_aus` seine 9 verdient.
- **Bei unter 3 Prozent Antwortquote** ist in der Regel die Personalisierung
  das Problem, nicht die Liste — hier zusätzlich: die fehlende
  Systemhaus-Prüfung.

### Compliance (DACH)

UWG § 7 und DSGVO erfordern bei Kaltansprache besondere Sorgfalt. Empfohlene
Reihenfolge: LinkedIn-Kontakt → Telefon bei klarem Branchenbezug → E-Mail mit
vollständigem Impressum und Ein-Klick-Opt-out. Ausschließlich geschäftliche
Adressen, je Kampagne eine dokumentierte Interessenabwägung, Abmeldungen sofort
und kanalübergreifend beachten. Maximal vier bis fünf Kontaktversuche je
Prospect in 90 Tagen.

Die Vergabedaten selbst sind unproblematisch: Der Datenservice Öffentlicher
Einkauf steht unter CC0. Die Firmendaten stammen aus amtlichen
Veröffentlichungen, nicht aus Scraping.

### Offene Punkte vor Kampagnenstart

- **Systemhaus-Klassifikator** — CPV belegt Teilnahme, nicht Geschäftsmodell.
  Bis dahin Sichtprüfung je Account.
- **Domain-Resolution** — von 2.458 Zeilen sind erst 11 angereichert; der Rest
  läuft über Clay.
- **Absender je Use Case festlegen** (Leon Brunner, Maurice Funk oder eine
  dedizierte Vertriebsrolle) inklusive Signatur.
- **Zielpakete festlegen:** Tier A mit hoher Verfahrensfrequenz → Scale bis
  Enterprise; Tier B mit Einzelstandort → Starter bis Team.
- **Freigabe der Referenznennungen** (Recordati, Oracom) für den namentlichen
  Einsatz.
- **Entscheidung über Österreich und Schweiz** — die aktuelle Datenbasis ist
  rein deutsch.

---

## Datengrundlage

| Datei | Inhalt | Stand |
|---|---|---|
| `data/longlist_markt.csv` | 2.458 Unternehmen mit Beleg, Tier und `proof_url` | 24.09.2026 |
| `data/longlist_signale.csv` | 651 Accounts mit Score, Signaltyp und `why_now` | 24.09.2026 |
| `data/score_trace.csv` | Score-Zerlegung je Account, Join über `company_id` | 23.09.2026 |
| `data/offene_verfahren.csv` | Vergabestellen-Feed, Join-Input, **kein Outbound** | 23.09.2026 |
| `data/job_signale_ohne_icp_beleg.csv` | Bid-Rollen ohne IT-Vergabebeleg, **kein Outbound** | 23.09.2026 |

Quellen: Datenservice Öffentlicher Einkauf (CC0), TED Search API v3,
Bundesagentur für Arbeit Jobsuche. Marktzahlen zu Publikationsquote,
Rechercheaufwand und Angebotsdauer aus dem bestehenden Patterno-Playbook
(Destatis Vergabestatistik 2024, KOINNO Vergabereport 2025, EU Single Market
Scoreboard 2024).

Beleg-URLs stichprobenhaft geprüft: **30 von 30 erreichbar**, alle als PDF
(`python3 -m src.verify_proofs --sample 30`).
