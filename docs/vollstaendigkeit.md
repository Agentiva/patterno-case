# Vollständigkeit: wie viel des Marktes die Liste abdeckt

Aufgabe 1c fragt drei Dinge: wie groß der Markt insgesamt ist, wie viel die
Liste davon abdeckt, und **woher man das weiß**. Die Antwort im README war
monatelang „keine Vollständigkeitsschätzung — dafür fehlt eine zweite,
unabhängige Quelle."

Die Begründung war richtig, der Schluss daraus falsch. Es gibt tatsächlich
keine zweite Liste, gegen die man abgleichen könnte. Aber die Frage lautet
*woher weißt du das*, nicht *nenne eine Zahl* — sie verlangt eine Methode mit
ausgewiesenen Grenzen. Eine Verweigerung ist keine.

Reproduzierbar mit `make vollstaendigkeit`, Rohwerte in
`data/vollstaendigkeit.csv`.

---

## Das Ergebnis in einem Satz

**Die Liste erfasst rund ein Drittel der Unternehmen, die im sichtbaren
deutschen Vergabegeschehen IT-Aufträge gewinnen oder darauf bieten — und diese
36 % sind die optimistische Lesart, nicht die mittlere.**

| | Beobachtet | Geschätzte Population | Abdeckung |
|---|---|---|---|
| Chapman, 3 Zeitschnitte | 2.443 | 4.394 – 4.799 | 51 – 56 % |
| **Chao1, 12 Monatsgelegenheiten** | **2.443** | **≥ 6.798** (untere 95-%-Grenze 6.206) | **≤ 36 %** |

Die beiden Zahlen widersprechen sich nicht. Sie messen dasselbe mit
unterschiedlich strengen Annahmen, und die Differenz ist selbst das Ergebnis —
dazu unten.

---

## Warum es überhaupt ohne zweite Quelle geht

Fang-Wiederfang braucht keine zweite Liste, sondern zwei unabhängige
**Beobachtungsgelegenheiten**. Die stecken im Korpus: Zwölf Monate lassen sich
teilen. Eine Firma, die in beiden Hälften bietet, ist ein Wiederfang.

```
n1  Firmen in Periode 1
n2  Firmen in Periode 2
m   Firmen in beiden      ->   N = (n1+1)(n2+1)/(m+1) - 1     (Chapman)
```

Chapman statt des bekannteren Lincoln-Petersen, weil letzterer bei kleinem `m`
nach oben verzerrt und bei `m = 0` nicht definiert ist.

### Drei Schnitte, nicht einer

Ein einzelner Schnitt lässt sich nicht von einem Trend unterscheiden. Deshalb
drei mit unterschiedlicher Anfälligkeit:

| Schnitt | n1 | n2 | beide | N | 95-%-Intervall |
|---|---|---|---|---|---|
| Halbjahre | 1.554 | 1.314 | 425 | 4.799 | 4.480 – 5.118 |
| Monate abwechselnd | 1.531 | 1.399 | 487 | 4.394 | 4.135 – 4.654 |
| Quartale abwechselnd | 1.464 | 1.449 | 470 | 4.509 | 4.234 – 4.784 |

**Streuung 9 %.** Hätten die drei Schnitte weit auseinandergelaufen, wäre das
das Ergebnis gewesen — „die Annahme ist zu stark verletzt, die Zahl taugt
nicht". Dass sie übereinstimmen, macht sie belastbar.

---

## Der Fehler, der eine plausible Zahl geliefert hätte

Die erste Fassung schnitt ohne Vorfilter und kam auf **636 gegen 2.108 Firmen**
in den Halbjahren — ein Fangunterschied von Faktor drei. Der Schätzer hat
trotzdem gerechnet und eine Zahl ausgegeben, die nach nichts Besonderem aussah.

Die Ursache liegt in der Korpusform. Geladen wird nach `pubMonth` — dem Monat
der Veröffentlichung. Geschnitten wurde nach `release.date`, und das ist nicht
dasselbe: Ein Paket vom März 2026 enthält auch Nachmeldungen und Zuschläge zu
Verfahren von 2025.

```
2024-10 bis 2025-08      1 bis   28 Releases je Monat   <- Nachmeldungen
2025-09                            319                  <- Anlauf
2025-10 bis 2026-09  1.136 bis 1.745                    <- 12 volle Monate
```

Der dünne Schwanz landete komplett in Periode 1. Jetzt werden nur Monate ab der
Hälfte des Medianmonats verwendet; ausgeschlossen sind 8 Monate mit zusammen
389 Releases. Die **Longlist** nutzt weiterhin den vollen Korpus — die
Filterung betrifft nur die Schätzung.

Dazu gehört ein zweiter, kleinerer Nennerfehler: `N` entsteht aus 12 Monaten,
die Liste enthält aber 15 Firmen, die nur in den Nachmeldemonaten auftauchen.
Die gegen `N` zu rechnen hätte eine zu hohe Abdeckung geschenkt. Nenner ist
deshalb 2.443, nicht 2.458.

---

## Warum Chao1 die ehrlichere Zahl ist

Chapman setzt **gleiche Fangwahrscheinlichkeit** voraus. Diese Annahme ist hier
systematisch verletzt: SVA mit 131 Verfahren im Jahr erscheint mit Sicherheit
in beiden Hälften, ein Systemhaus mit einem einzigen Verfahren nur zufällig in
einer.

Die Richtung der Verzerrung ist bekannt. Ungleiche Fangwahrscheinlichkeit treibt
`m` nach oben und `N` damit nach **unten** — Chapman überschätzt also die
Abdeckung. Genau das zeigt der Vergleich.

Chao1 gibt die Gleichheitsannahme auf. Er nutzt 12 monatliche Gelegenheiten
statt zwei und liest die Population aus der Häufigkeitsverteilung:

```
in genau  1 Monat gesehen   f1 = 1.781      <- 73 % aller beobachteten Firmen
in genau  2 Monaten         f2 =   363
           3 Monaten               127
           4 Monaten                54
           5 Monaten                36

N = S + f1(f1-1) / (2(f2+1))  =  6.798
```

Die Logik ist anschaulich: **Viele Firmen, die nur einmal gesehen wurden,
heißen, dass viele gar nicht gesehen wurden.** Dass 73 % der Liste in genau
einem von zwölf Monaten auftaucht, ist die Signatur einer stark
unterabgetasteten Population.

Chao1 ist mathematisch als **Untergrenze** definiert — nicht „wahrscheinlich zu
niedrig", sondern beweisbar, und zwar bei beliebig ungleicher
Fangwahrscheinlichkeit. Eine Untergrenze für `N` ist eine **Obergrenze für die
Abdeckung**. Deshalb steht oben „≤ 36 %" und nicht „= 36 %".

---

## Was diese Zahl NICHT enthält

Beide Schätzer messen, wie viele Firmen im **sichtbaren** Vergabegeschehen
fehlen. Sie sagen nichts über das, was der Datenservice strukturell nicht
enthält. Das ist keine Stichprobenlücke, sondern ein blinder Fleck, und die
beiden gehören nicht in dieselbe Zahl.

**Unterschwellenvergaben.** Rund 90 % aller öffentlichen Aufträge in
Deutschland liegen unterhalb der EU-Schwellenwerte (2026: 216.000 € netto für
Liefer- und Dienstleistungen) und unterliegen keiner EU-weiten
Veröffentlichungspflicht. Der Datenservice deckt einen Teil davon ab — er
aggregiert 123 Portale, darunter Landes- und kommunale —, aber nicht alle.

Gemessen am eigenen Korpus:

```
Releases mit Wertangabe       3.083 von 17.185   (17,9 %)
  davon unter 216.000 EUR       712              (23,1 %)
  davon ab   216.000 EUR      2.371              (76,9 %)
  Median                      720.000 EUR
  25./75. Perzentil           242.795 / 3.300.000 EUR
```

**Der Korpus ist deutlich zur Oberschwelle verschoben.** Und die 23,1 % sind
selbst noch zu optimistisch: Sie sind an den 17,9 % gemessen, die überhaupt
einen Wert nennen, und Wertangaben sind kein Zufall — EU-Verfahren müssen den
Auftragswert veröffentlichen, nationale oft nicht. Der wahre
Unterschwellenanteil im Korpus liegt also höher, um wie viel ist nicht
messbar.

Für Patterno ist das die interessanteste Lücke des ganzen Case: Die
Unterschwelle ist der Bereich, in dem die kleinen und mittleren Systemhäuser
arbeiten — also der ICP-Korridor 50–2.000 Mitarbeitende. Deshalb steht
Unterschwellen-Ingestion an erster Stelle im Zwei-Wochen-Plan.

---

## Warum es keinen externen Nenner gibt

Naheliegend wäre, gegen eine Branchenzahl zu rechnen. Ich habe zwei geprüft,
und beide zählen eine andere Menge:

| Quelle | Zahl | Warum sie nicht passt |
|---|---|---|
| WZ 62 (IT-Dienstleistungen und Software), Destatis über Statista, 2023 | **95.196** Unternehmen | Viel zu breit. Enthält jede Einzelentwicklerin, jedes Webstudio, jedes SaaS-Haus. |
| „IT-Systemhäuser", Listflix-Firmendatenbank, 27.09.2026 | **1.171** Unternehmen | Zählt nach **Selbstbeschreibung**, nicht nach Tätigkeit. Und: 97 % sind Kleinst- und Kleinunternehmen (24,1 % Kleingewerbe, 26,9 % Kleinst-, 46,1 % Kleinunternehmen), nur 2,9 % Mittelstand und Großunternehmen. |

Die zweite Zahl ist **kleiner** als meine Schätzung von ≥ 6.798 — und das ist
kein Widerspruch, sondern der Beleg, dass beide etwas anderes messen. Ich zähle
Unternehmen, die **nachweislich** einen öffentlichen IT-Auftrag gewonnen haben
oder darauf geboten haben. Darunter sind Softwarehäuser, Telkos,
Unternehmensberatungen, Hardwarehändler und Ingenieurbüros, die sich selbst nie
„Systemhaus" nennen würden. Listflix zählt, wer das Wort im Register oder auf
der Website führt — überwiegend Betriebe unter zehn Mitarbeitenden, also
unterhalb des ICP.

**Genau deshalb ist Fang-Wiederfang hier die richtige Methode und nicht die
zweitbeste:** Die Population, um die es geht, wird von keiner Statistik
gezählt, weil sie über ein Verhalten definiert ist und nicht über eine
Branchenkennung.

Was das für die Liste heißt, steht in
[clay_sculptor_systemhaus.md](clay_sculptor_systemhaus.md): Von 20 Stichproben
gehören 6 nicht ins ICP. Auf ≥ 6.798 hochgerechnet wären rund 4.800 davon
Systemhäuser im gesuchten Sinn — eine Zahl, die ich bewusst **nicht** in die
Tabelle oben schreibe, weil sie eine Quote aus 20 Handprüfungen auf
sechstausend Zeilen streckt.

---

## Was die Schätzung besser machen würde

1. **Längerer Korpus.** 24 statt 12 Monate verdoppeln die Gelegenheiten und
   senken `f1` — der größte Hebel, und er kostet nur Rechenzeit.
2. **Unterschwellen-Ingestion für drei Bundesländer.** Verschiebt nicht die
   Schätzung, sondern die Grundmenge. Die Zahl würde steigen *und* die
   Abdeckung, weil beide heute denselben blinden Fleck teilen.
3. **TED als zweite Beobachtungsgelegenheit.** TED und der Datenservice
   überlappen stark, aber nicht vollständig. Der Überlappungsgrad wäre ein
   echter zweiquellen-Schätzer statt eines Zeitschnitts — das ist die
   methodisch sauberste Verbesserung.
4. **Gelabeltes Ground-Truth-Set.** 50 Systemhäuser von Hand aus
   Branchenverzeichnissen ziehen und prüfen, wie viele die Pipeline findet.
   Das misst direkt, statt zu schätzen.
