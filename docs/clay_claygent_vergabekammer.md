# Claygent: Vergabekammer-Nachprüfungen

Die vierte Signalquelle. Ein Nachprüfungsantrag ist der einzige öffentliche
Vorgang, bei dem ein Unternehmen **Geld dafür ausgibt**, zu zeigen, dass ihm
eine verlorene Ausschreibung weh tut — Anwalt plus Kammergebühr.

## Warum hier Claygent und sonst nirgends

Bei den drei bestehenden Quellen wäre AI-Recherche Verschwendung: saubere
HTTP-Aufrufe, strukturiertes JSON, deterministisch parsebar. Hier liegt der
Fall anders:

| | |
|---|---|
| **Verstreut** | 15+ Kammern, keine API, HTML und PDF gemischt |
| **Browser nötig** | bundeskartellamt.de antwortet HTTP-Clients mit **403**, Browsern mit 200. Claygent ist browserbasiert. |
| **Unstrukturierter Text** | „Antragstellerin, Aktenzeichen, Ausgang" aus Rechtsprosa zu ziehen, ist genau eine LLM-Aufgabe |

## Die Richtung, die funktioniert

Falsch wäre, Entscheidungen zu **suchen** und dann Firmen zuzuordnen — das
sind tausende Zeilen, die meisten ohne ICP-Bezug.

Richtig ist die Umkehrung: **pro Account fragen, ob er in einem Verfahren
vorkommt.**

```
233 Tier-A-Accounts  ×  3 Credits  =  ~700 Credits
```

Die Trefferquote wird niedrig sein. Aber jeder Treffer ist das stärkste
Signal im System — und die 700 Credits fallen einmal an, nicht wöchentlich.

---

## Der Prompt

Spaltentyp **Claygent / Web research**. Eingabe über `/` einfügen:
`{{Company Name}}`, `{{Company Domain}}`, `{{city}}`.

```
Du prüfst, ob ein bestimmtes Unternehmen in einem deutschen
Vergabe-Nachprüfungsverfahren als Partei aufgetreten ist.

UNTERNEHMEN: {{Company Name}}
DOMAIN:      {{Company Domain}}
SITZ:        {{city}}

WONACH DU SUCHST
Entscheidungen von Vergabekammern (erste Instanz) und von
OLG-Vergabesenaten (Beschwerdeinstanz). Suche mit dem Firmennamen in
Kombination mit: Vergabekammer, Nachprüfungsantrag, Nachprüfungsverfahren,
Vergabesenat, "Verg", GWB Vergaberecht.

Quellen, in dieser Reihenfolge:
1. bundeskartellamt.de — Entscheidungen der Vergabekammern des Bundes
2. Landesportale und Justizportale der Länder
3. openjur.de, dejure.org, rechtsprechung-im-internet.de
4. Fachmedien wie vergabeblog.de
5. Pressemitteilungen des Unternehmens selbst

DIE ROLLE ENTSCHEIDET ALLES
Ein Unternehmen kann in drei Rollen auftreten. Ordne sie genau zu:

"antragstellerin"
  Das Unternehmen hat den Nachprüfungsantrag GESTELLT. Es hat geboten,
  den Zuschlag nicht bekommen und dagegen Rechtsschutz gesucht.
  Das ist der wertvollste Fall.

"beigeladene"
  Das Unternehmen sollte den Zuschlag bekommen, und ein Mitbewerber
  greift die Entscheidung an. Der Zuschlag steht auf der Kippe.

"antragsgegnerin"
  Das Unternehmen ist die VERGABESTELLE, also der öffentliche
  Auftraggeber. Dann gehört es nicht in diese Liste — melde es
  ausdrücklich, das ist ein Hinweis auf eine Fehleinordnung.

WANN ES KEIN TREFFER IST
- Der Firmenname steht nicht wörtlich in der Entscheidung. Ein ähnlicher
  Name, eine Schwestergesellschaft oder ein Konzernname reichen NICHT.
- Die Entscheidung ist anonymisiert ("die Antragstellerin" ohne
  Firmierung). Dann ist sie nicht zuordenbar, auch wenn der Fall zur
  Branche passt.
- Das Verfahren ist kein Vergabe-Nachprüfungsverfahren, sondern ein
  anderer Rechtsstreit (Arbeitsrecht, Wettbewerbsrecht, Insolvenz).
- Das Unternehmen wird nur beiläufig erwähnt, ohne Parteistellung.

In all diesen Fällen: "gefunden": "nein". Das ist ein brauchbares
Ergebnis, kein Misserfolg.

WAS DU NICHT TUN DARFST
Erfinde kein Aktenzeichen. Aktenzeichen haben feste Formate, etwa
"VK 1-45/26" oder "VII-Verg 12/25". Wenn du keines im Text findest, lass
das Feld leer und setze "gefunden": "nein".

Leite nichts aus dem Firmennamen, der Branche oder der Größe ab. Wenn du
nichts findest, ist das die Antwort.

AUSGABE
Antworte ausschließlich mit diesem JSON:

{
  "gefunden": "ja | nein",
  "rolle": "antragstellerin | beigeladene | antragsgegnerin | keine",
  "aktenzeichen": "z. B. VK 1-45/26, sonst leer",
  "kammer": "z. B. Vergabekammer des Bundes",
  "entscheidungsdatum": "YYYY-MM-DD, sonst leer",
  "ausgang": "stattgegeben | zurueckgewiesen | erledigt | unbekannt",
  "verfahrensgegenstand": "worum ging die Ausschreibung",
  "auftraggeber": "wer hatte ausgeschrieben",
  "firmenname_im_text": "wie das Unternehmen in der Entscheidung
                         geschrieben steht",
  "beleg_zitat": "wörtliches Zitat, das die Parteistellung zeigt",
  "beleg_url": "URL der Fundstelle",
  "weitere_verfahren": 0,
  "konfidenz": 0.0 bis 1.0
}

"weitere_verfahren" ist die Anzahl zusätzlicher Verfahren desselben
Unternehmens, die du gesehen hast. Mehrere Nachprüfungen sind ein
stärkeres Signal als eine.
```

---

## Einrichtung in Clay

**Conditional Run** — nicht über alle Zeilen laufen lassen:

```
{{tier}} = "A" AND {{im_icp}} = "ja"
```

Der Systemhaus-Check aus
[clay_sculptor_systemhaus.md](clay_sculptor_systemhaus.md) läuft **vorher**.
Sonst bezahlst du Recherche für Siemens Gebäudeautomation.

**Folgespalten:**

| Spalte | Formel |
|---|---|
| `vk_signal` | `if({{VK.rolle}} = "antragstellerin", "nachpruefung_eingereicht", if({{VK.rolle}} = "beigeladene", "nachpruefung_beigeladen", ""))` |
| `vk_gewicht` | `if({{vk_signal}} = "nachpruefung_eingereicht", 10, if({{vk_signal}} = "nachpruefung_beigeladen", 8, 0))` |
| `icp_fehler` | `if({{VK.rolle}} = "antragsgegnerin", "PRUEFEN: ist Vergabestelle", "")` |

Die letzte Spalte ist keine Spielerei. Findet Claygent das Unternehmen als
**Antragsgegnerin**, ist es ein öffentlicher Auftraggeber und hat in einer
Bieter-Longlist nichts verloren — ein kostenloser Test der Ausschlusslisten.

---

## Das Zeitfenster — sonst verpufft das Signal

Eine Kammerentscheidung kommt **Monate nach** dem Verfahren. Die
Aktualitätsdämpfung der Pipeline geht nach 56 Tagen auf 0,2 herunter:

```
RECENCY_BUCKETS = [(14, 1.0), (28, 0.8), (42, 0.6), (56, 0.4)]
RECENCY_FLOOR   = 0.2
```

Ein Beschluss von vor vier Monaten würde damit fast wegskaliert — das
stärkste Signal fiele unter die Schwelle. **Dieser Signaltyp braucht ein
eigenes Fenster**, etwa 270 Tage mit flacherer Dämpfung.

Ohne diese Anpassung baust du die Quelle, sie feuert, und niemand sieht es.
Das ist derselbe Fehler wie der nie feuernde Rahmenvertrags-Signaltyp, nur
eine Ebene höher.

---

## Erst messen, dann skalieren

Lass den Prompt zuerst über **20 Tier-A-Accounts** laufen und zähle:

1. Wie viele Treffer insgesamt?
2. Wie viele davon halten der Handprüfung stand — Firmenname wörtlich,
   Aktenzeichen im richtigen Format, URL erreichbar?
3. Wie viele Fehlalarme (falsche Firma, anderer Rechtsstreit,
   erfundenes Aktenzeichen)?

**Unter 80 % Präzision nicht ausrollen.** Ein erfundener Nachprüfungsantrag
in einer Outbound-Mail ist schlimmer als gar kein Signal: Du behauptest
gegenüber einem Bid Manager etwas über sein eigenes Verfahren, und er weiß
es besser.

Die Erwartung beim Volumen ist bewusst niedrig. Das Audit
(`make vk-audit`, `data/vk_quellenaudit.csv`) hat gezeigt, dass viele
Beschlüsse anonymisiert sind. Wenn von 20 Accounts zwei einen Treffer
liefern, ist das ein Erfolg — es sind zwei Gespräche, die sonst nicht
stattgefunden hätten.

---

## Was Claygent hier nicht löst

**Unterlegene Bieter allgemein.** Wer bietet und verliert, ohne zu klagen,
bleibt unsichtbar — diese Daten werden nirgends veröffentlicht. In 438 von
441 Bekanntmachungen ist die Bieterliste identisch mit der Gewinnerliste.
Kein Web-Research findet, was nie veröffentlicht wurde.

Der Nachprüfungsantrag ist deshalb kein vollständiger Ersatz, sondern ein
schmaler, aber sehr scharfer Ausschnitt: Er zeigt nicht alle Verlierer,
sondern die, denen es genug weh tat, um dafür zu zahlen.
