# Domain-Waterfall: amtliche Quelle zuerst, Clay für die Lücke

Die Spalte `domain` ist ein Pflichtfeld aus Aufgabe 1c. Sie entsteht in zwei
Schritten, und die Reihenfolge ist der ganze Punkt.

```
Stufe 0   contactPoint der Bieterpartei in der Bekanntmachung
          1.487 / 2.458 · 60,5 %   ·  0 Credits  ·  Quelle + Konfidenz je Zeile
             │
             ▼  was hier leer bleibt:
Stufe 2   KI-Recherche in Clay
            971 / 2.458 · 39,5 %   ·  ~1–3 Credits je Zeile
```

<!-- Stufe 1 (Apollo Lookup) und Stufe 3 (Impressum) stehen in
     waterfalls.md; hier geht es um die beiden Stufen, die das Feld
     tatsächlich füllen. -->

---

## Warum die amtliche Quelle zuerst kommt

Das ist keine Sparmaßnahme, sondern eine Qualitätsentscheidung. eForms führt
je Partei einen Kontaktblock — **das Unternehmen hat diese Adresse der
Vergabestelle selbst gemeldet**, und sie steht in derselben Bekanntmachung wie
der Zuschlagsbeleg.

Eine KI, die aus „Apple" auf `apple.com` schließt, leitet ab. Die Bekanntmachung
weiß es.

| | Stufe 0 | Stufe 2 |
|---|---|---|
| Herkunft | amtliche Bekanntmachung, CC0 | Sprachmodell + Websuche |
| Kosten | 0 € | ~1–3 Credits je Zeile |
| Beleg | `proof_url` dieselbe wie beim Zuschlag | Website-URL, von der KI genannt |
| `domain_source` | `amtlich_bestaetigt` / `amtlich_namensbezug` | `clay_ai` |
| Rang im Modell | **0,95 / 0,90** | **0,55** |

<!-- Der Rang ist eine Obergrenze, keine Punktschätzung - siehe unten. -->

---

## Stufe 2 in Clay — Schritt für Schritt

### 1 · Die Datei erzeugen

```bash
make clay-todo          # → data/clay_domain_todo.csv
```

Enthält **nur** die Zeilen ohne Domain, sortiert nach Tier und
Verfahrenshäufigkeit:

```
971 Zeilen · Tier A 47 · Tier B 510 · Tier C 414
```

| Spalte | Wofür |
|---|---|
| `company_id` | **Rückschlüssel für `retier` — nicht entfernen** |
| `legal_name` | Eingabe für den Prompt |
| `ort`, `plz` | Eingabe für den Prompt — **der Diskriminator**, siehe unten |
| `tier`, `verfahren_12m` | Priorisierung: erst A, dann B |
| `cpv_kurz` | Kontext: welche Art IT |
| `proof_url` | Gegenprobe von Hand — passt die gefundene Firma zum Verfahren? |

### 2 · Spalte anlegen

**Spaltentyp:** Claygent / AI Web Research · **Name:** `Domain finden`

**Conditional Run — der eigentliche Waterfall-Mechanismus:**

```
{{domain}} is empty
```

Lädst du stattdessen die vollständige Longlist hoch, lautet die Bedingung
genauso — dann läuft die Spalte über dieselben 971 Zeilen und lässt die 1.487
amtlichen unberührt.

### 3 · Der Prompt

```text
Finde die offizielle Unternehmenswebsite (Domain) des unten genannten
deutschen Unternehmens.

UNTERNEHMEN: {{legal_name}}
ORT:         {{ort}}
PLZ:         {{plz}}
BRANCHE:     IT-Dienstleistung, CPV {{cpv_kurz}}

VORGEHEN
1. Suche nach dem Firmennamen zusammen mit dem Ort.
2. Öffne die gefundene Website und suche das Impressum.
3. Prüfe im Impressum DREI Dinge:
   a) Steht dort derselbe Firmenname inklusive Rechtsform?
   b) Steht dort derselbe Ort?
   c) Ist es eine deutsche Gesellschaft (GmbH, AG, KG, GmbH & Co. KG, SE)?

DER ORT ENTSCHEIDET
Der Firmenname allein reicht NICHT. Internationale Marken führen ihren
Namen im Impressum jeder Landesgesellschaft, und gleiche oder ähnliche
Namen kommen in Deutschland mehrfach vor.

Echte Fehler aus einem früheren namensbasierten Lauf — genau diese sollst
du vermeiden:
  EOMI AG, Hamburg          wurde zu  eominnesota.org  (eine US-Organisation)
  msg systems ag, Ismaning  wurde zu  msg-systems.ro   (Rumänien)
  Netlight Consulting, FFM  wurde zu  domainflotta.hu  (Ungarn)
  Dedalus HealthCare, Bonn  wurde zu  dedalus.at       (Österreich)

Stimmt der Ort im Impressum nicht mit dem Ort oben überein, ist es die
falsche Gesellschaft — auch wenn der Name passt.

RECHTSTRÄGER, NICHT KONZERN
Gesucht ist die Gesellschaft, die oben genannt ist. Führt die Suche auf
eine Konzernmutter oder eine Schwestergesellschaft, nimm trotzdem die
Domain, die das Impressum des genannten Rechtsträgers nennt, und setze
"zeigt_auf": "konzern".

WAS DU NICHT TUN DARFST
Rate keine Domain aus dem Firmennamen. "Muster IT GmbH" wird NICHT zu
"muster-it.de", nur weil das plausibel klingt. Wenn du die Website nicht
findest oder das Impressum die Prüfung nicht besteht, ist das Ergebnis
"gefunden": "nein". Eine leere Zelle ist brauchbar, eine falsche Domain
kostet eine Outbound-Mail an das falsche Unternehmen.

Gib keine Domain von Verzeichnissen, Bewertungsportalen, LinkedIn,
North Data, Bundesanzeiger, Wikipedia oder Stellenbörsen aus. Gesucht ist
die eigene Website des Unternehmens.

AUSGABE
Antworte ausschließlich mit diesem JSON:

{
  "gefunden": "ja | nein",
  "domain": "nur der Host ohne https:// und ohne www, z. B. bechtle.com",
  "impressum_url": "URL des geprüften Impressums",
  "firmenname_im_impressum": "exakt wie dort geschrieben",
  "ort_im_impressum": "exakt wie dort geschrieben",
  "ort_stimmt": "ja | nein | kein Impressum gefunden",
  "zeigt_auf": "rechtstraeger | konzern | unklar",
  "konfidenz": 0.0 bis 1.0
}
```

### 4 · Folgespalten

| Spalte | Formel |
|---|---|
| `domain` | `if({{Domain finden.ort_stimmt}} = "ja", {{Domain finden.domain}}, "")` |
| `domain_source` | `if({{Domain finden.gefunden}} = "ja", "clay_ai", "")` |
| `domain_confidence` | `{{Domain finden.konfidenz}}` |
| `domain_pruefen` | `if({{Domain finden.zeigt_auf}} = "konzern", "PRUEFEN: Konzerndomain", if({{Domain finden.ort_stimmt}} = "nein", "PRUEFEN: Ort weicht ab", ""))` |

<!-- Die erste Formel ist der wichtigste Filter: Ohne Ortsbestätigung
     wird die Domain gar nicht erst übernommen. -->

**`domain_source = "clay_ai"` ist nicht optional.** Ohne dieses Feld behandelt
`retier` die Angabe mit dem Standardrang 0,70 — also wie eine
Anbieterdatenbank statt wie eine Vermutung.

### 5 · Zurückspielen

```bash
python3 -m src.cli retier --from data/clay_export_domains.csv
python3 -m src.cli export
```

`retier` erkennt `company_id` und `domain_source` automatisch. Der Lauf meldet:

```
Domains gesamt: <vorher + neu> von 2458
Domain bestaetigt   n   (zweite Quelle nennt dieselbe Domain)
Domain abgewiesen   n   (vorhandene Quelle ist besser belegt - siehe domain_note)
```

---

## Warum eine KI-Vermutung eine amtliche Domain nie überschreiben kann

Der Quellenrang ist eine **Obergrenze**, keine Punktschätzung:

```python
SOURCE_RANK = {
    "amtlich_bestaetigt":  0.95,   # url und Mail der Bekanntmachung stimmen überein
    "amtlich_namensbezug": 0.90,   # eine amtliche Quelle, Domainstamm passt zum Namen
    "enrichment":          0.70,   # Clay/Apollo, Anbieterdatenbank
    "clay_ai":             0.55,   # KI-Recherche  ← schwächste Quelle
}

rank = min(konfidenz_der_zeile, SOURCE_RANK[quelle])
```

Eine Zeile kann durch ihre Konfidenz **schlechter** werden als ihre Quelle,
aber nie besser.

Die erste Fassung nahm die mitgelieferte Konfidenz, wenn eine da war. Das ist
gefährlich, sobald ein Sprachmodell die Quelle ist: Ein Modell, das `apple.com`
aus „Apple" ableitet, meldet dafür 0,95 — und hätte damit eine amtlich
bestätigte Domain überschrieben. Dieser Fehlermodus ist gemessen, nicht
theoretisch: 8 von 12 namensbasierten Auflösungen lagen im Longtail falsch,
jede davon mit voller Zuversicht geliefert.

---

## Was du nach dem Lauf prüfst

Nicht die Trefferquote — die **Präzision**. Zieh **20 Treffer** und prüfe von
Hand:

1. Öffnet die Domain eine erreichbare Website?
2. Nennt das Impressum denselben Firmennamen **inklusive Rechtsform**?
3. Nennt das Impressum denselben Ort?
4. Passt die Firma zum Verfahren in `proof_url`?

**Unter 85 % Präzision nicht ausrollen**, sondern erst den Prompt an den
Fällen korrigieren, die danebenliegen.

Die Erwartung ist bewusst gedämpft: Stufe 0 hat die *einfachen* Fälle schon
abgeräumt. Was in diesen 971 Zeilen übrig ist, sind überwiegend kleine
Unternehmen mit dünner Webpräsenz — genau die Gruppe, in der die frühere
Messung 77 % auf 33 % fallen ließ, sobald man den Longtail statt der bekannten
Marken maß.

<!-- Deshalb steht in README und operating_model bewusst "60 % mit dem
     Hinweis, dass es eine Annahme ist" statt einer schön gerechneten
     Gesamtquote. -->

## Kosten

| | |
|---|---|
| Claygent je Zeile | 1–3 Credits, je nach Suchtiefe |
| Testsatz 20 Zeilen | 20–60 Credits |
| Tier A (47 Zeilen) | ~140 Credits |
| Tier A + B (557 Zeilen) | ~1.700 Credits |
| Alle 971 | ~2.900 Credits |

**Tier C zuerst weglassen.** 414 der 971 offenen Zeilen sind Tier C — dort
läuft ohnehin kein aktives Outbound. Mit Tier A und B deckst du den
ansprechbaren Teil zu ~57 % der Kosten ab.
