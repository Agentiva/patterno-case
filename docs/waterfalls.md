# Enrichment-Waterfalls mit gemessenen Trefferquoten

Alle Zahlen sind an echten Daten gemessen, Stand 27.09.2026. Keine Schaetzungen.

## 1. Domain-Resolution (Firmenname aus Vergabedaten -> Domain)

| Stufe | Methode | Kosten | Ergebnis |
|---|---|---|---|
| **0** | **`contactPoint` der Bieterpartei in der Bekanntmachung selbst** | **0** | **1.487 von 2.458 (60,5 %)** |
| 1 | Apollo Organizations Lookup, voller Name + Ortsfilter Deutschland | 0 | praezise, aber loechrig |
| **2** | **KI-Recherche in Clay, nur fuer Zeilen ohne Domain** | **1–3 Credits/Zeile** | **971 offene Zeilen** — [clay_domain_waterfall.md](clay_domain_waterfall.md) |
| 3 | Impressum abrufen (§ 5 DDG) und gegen Firmenname + Ort der Vergabe pruefen | 0 | harter Beleg |
| 4 | Manuelle Review-Queue | Zeit | Rest |

Die frueheren Stufen 1 und 2 (Apollo mit und ohne Ortsfilter) sind zu einer
zusammengefasst. Die zweite — verkuerzter Name ohne Ortsfilter — war es, die
im Longtail 8 von 12 Zeilen falsch aufloeste; sie steht unten als Messung,
nicht mehr als Arbeitsschritt.

### Stufe 2: der Rang macht sie ungefaehrlich

```python
SOURCE_RANK = {
    "amtlich_bestaetigt":  0.95,
    "amtlich_namensbezug": 0.90,
    "enrichment":          0.70,
    "clay_ai":             0.55,   # KI-Recherche
}
rank = min(konfidenz_der_zeile, SOURCE_RANK[quelle])
```

Der Quellenrang ist eine **Obergrenze**. Eine Zeile kann durch ihre Konfidenz
schlechter werden als ihre Quelle, aber nie besser — deshalb kann eine
KI-Vermutung eine amtliche Domain auch dann nicht ueberschreiben, wenn das
Modell 0,99 dafuer meldet. Verifiziert: Ein Testimport mit
`clay_ai / 0.99` gegen `sva.de` wurde abgewiesen und in `domain_note`
protokolliert; dieselbe Quelle fuellte im selben Lauf eine leere Zelle.

### Stufe 0 gab es zuerst nicht, und das war der teuerste Fehler

Die Spalte `domain` war in der abgegebenen Liste bei **0 von 2.458** Zeilen
gefuellt. Der Plan lief ueber Clay und Apollo — also ueber Stufe 1 — und
deckte 23 Firmen ab. Ich habe den Waterfall von oben nach unten gebaut, ohne
vorher zu fragen, ob die Quelle die Domain schon mitliefert.

Sie tut es. eForms fuehrt je Partei einen Kontaktblock. Gemessen am
12-Monats-Korpus:

```
Bieter- und Gewinnerparteien            5.735
  mit contactPoint.url                  1.468   (25,6 %)
  mit contactPoint.email                4.006   (69,9 %)
```

Auf die 2.458 Firmen der Longlist gerechnet **75,3 % Rohabdeckung** — vor
jeder Pruefung. Das ist nicht nur billiger als Apollo, es ist eine bessere
Quelle: Die Adresse hat das Unternehmen der Vergabestelle selbst gemeldet und
sie steht in derselben Bekanntmachung wie der Zuschlagsbeleg.

### Warum daraus 60,5 % und nicht 75,3 % werden

Rohabdeckung ist keine Abdeckung. Wo `url` und E-Mail-Domain beide vorliegen
(726 Firmen), widersprechen sie sich in **23 %** der Faelle — und die
Abweichungen sind keine Streuung, sondern vier Muster:

| Muster | Beispiel | Behandlung |
|---|---|---|
| Kaputtes Feld | `https` ohne Rest, `milchundzucker` ohne TLD, `vertrieb@btc-ag.com` im URL-Feld, `nortal.cpm` als Tippfehler im Original | Syntaxpruefung |
| Konzern statt Rechtstraeger | Fsas Technologies GmbH → `fujitsu.com`, Eviden Germany → `atos.net` | Streuungstest |
| Zweitdomain desselben Hauses | `materna.de` / `materna.group`, `acp.de` / `techrent.acp-gruppe.com` | Namensbezug entscheidet |
| **Fremde Adresse im Bieterdatensatz** | **29 Firmen tragen `fb.hamburg.de`, 18 tragen `deutschebahn.com`, 12 tragen `rentenbank.de`** | Auftraggeber- und Streuungstest |

Das letzte Muster ist der Grund, warum diese Stufe eine Pruefschicht braucht
und nicht nur einen Feldzugriff. `fb.hamburg.de` ist die Beschaffungsstelle
Hamburg — der **Auftraggeber**. Wer das uebernimmt, schreibt eine
Outbound-Mail an die Vergabestelle und behauptet dabei, sie sei Bieter
gewesen. Bei `deutschebahn.com` steht die Adresse des Kunden im Datensatz des
Lieferanten. Und `beispiel.de` stand bei 5 Firmen — das ist `example.de` auf
Deutsch.

### Die Pruefkette

Vier Tests, alle ohne Netzzugriff, alle nachrechenbar
(`src/resolve/domains.py`):

```
Syntax        Punkt vorhanden, Buchstaben-TLD, kein @, keine Platzhalter
Auftraggeber  Domain kommt im Korpus in einer buyer-Rolle vor
Streuung      Domain beansprucht >= 3 namentlich unverwandte Firmen
Namensbezug   Teilt der Domainstamm ein Token mit dem Firmennamen?
```

**Der Namensbezug schlaegt den Verdacht** — das war eine Korrektur, nicht die
erste Fassung. Die verwarf jede Domain, die im Korpus auch als
Auftraggeberadresse auftrat, und traf damit die Falschen: `Aagon GmbH →
aagon.com`, `Bundesdruckerei → bdr.de`, `DLR → dlr.de`, `DFN → dfn.de`. Diese
Haeuser beschaffen selbst und stehen deshalb auch in einer buyer-Rolle. Ihre
eigene Domain ist dadurch nicht falsch. Erst der Namensbezug trennt die
Gruppen: `aagon.com` bei Aagon passt, `fb.hamburg.de` bei avodaq nicht.

### Ergebnis

```
MIT Domain             1.487 / 2.458   60,5 %
  amtlich_bestaetigt     555           url und Mail stimmen ueberein
  amtlich_namensbezug    927           eine Quelle, Domainstamm passt zum Namen
  aus Clay ergaenzt        5           Luecke gefuellt (u. a. nortal.com)

OHNE Domain              971 / 2.458   39,5 %
  Quelle fuehrt kein Feld  631
  Fremdadresse erkannt     106
  url/Mail widersprechen   101
  unter Confidence-Schwelle 138
```

### Die unabhaengige Gegenprobe

Der Clay-Export deckt 38 der Firmen ab und wurde **nach** Stufe 0 eingespielt.
Clay hat unabhaengig aufgeloest, ueber Apollo statt ueber die Bekanntmachung:

```
32 von 33  nennen dieselbe Domain wie die amtliche Quelle   (97 %)
 1         Konflikt: acp-gruppe.com (Clay) vs. acp.de (amtlich)
 5         fuellen eine Luecke, die Stufe 0 offen gelassen hat
```

Bei dem einen Konflikt hat die amtliche Quelle recht: `acp.de` gehoert dem
Rechtstraeger, der geboten hat, `acp-gruppe.com` der Gruppe. Genau das Muster,
das bei Bechtle und Computacenter schon die Mitarbeiterzahl verdorben hat.

**Deshalb hat `retier` jetzt eine Quellenrangfolge.** Vorher ueberschrieb ein
spaeterer Lauf bedingungslos — wer erst die amtliche Domain und danach den
Clay-Export einspielte, hatte am Ende die schlechtere Zahl in der Spalte und
sah es nicht, weil die Spalte gefuellt blieb. Jetzt gewinnt die besser belegte
Quelle, die abgewiesene Angabe steht in `domain_note`, und identische Angaben
werden als Bestaetigung gezaehlt statt als Konflikt gemeldet.

### Warum Stufe 3 nicht optional ist

Erste Messung an 13 **bekannten Marken** (Bechtle, CANCOM, Controlware,
Materna, iteratec): Stufe 1 traf 7, Stufe 2 weitere 4 -> 77 %. Sah gut aus.

Diese Stichprobe war **verzerrt**. Grosse Marken sind in Apollo sauber
gepflegt. Im Longtail derselben Liste kippte das Bild - von 12
Stufe-2-Aufloesungen waren 8 falsch:

| Zuschlag an | Stufe 2 lieferte | tatsaechlich |
|---|---|---|
| Dedalus HealthCare GmbH, Bonn | `dedalus.at` | Oesterreich |
| msg systems ag, Ismaning | `msg-systems.ro` | Rumaenien |
| EOMI AG, Hamburg | `eominnesota.org` | Entrepreneurs Organization Minnesota |
| Netlight Consulting GmbH, Frankfurt | `domainflotta.hu` | Ungarn |
| EduXpert GmbH, Regensburg | `eduxpert.co.uk` | UK |
| RICOH Deutschland GmbH | `ricoh-documentcenter.de` | falsche Teileinheit |
| Sopra Steria SE, Hamburg | `soprasteria.com` | franz. Konzern |
| Eviden Germany GmbH, Berlin | `eviden.com` | Konzern |

**Lehre: eine Trefferquote ohne Angabe der Stichprobe ist wertlos.**

### Die Falle in Stufe 3

Eine reine Namenspruefung im Impressum reicht NICHT. Bei internationalen
Marken steht der Name im Impressum jeder Landesgesellschaft:
`msg-systems.ro` und `soprasteria.com` bestanden die Namenspruefung.

Diskriminator ist der **Ort aus der Vergabebekanntmachung**. Er steht nur
im Impressum der Gesellschaft, an die der Zuschlag ging.
Regel: `name_ratio >= 0.6 AND (Ort im Impressum ODER .de-Domain)`.

### Gemessene Quoten Stufe 3

Von 12 geprueften Domains waren 5 per Impressum erreichbar (42 %); der Rest
blockte Bots oder nutzt abweichende Pfade. Von diesen 5 bestanden nach der
verschaerften Regel 2 (`convergetp.de`, `beneering.com`), 3 wurden korrekt
abgelehnt. Beide Bestaetigungen lieferten zusaetzlich den HRB-Eintrag.

## 2. Firmographics (Domain -> Mitarbeiterzahl, Branche)

| Stufe | Methode | Kosten | Quote |
|---|---|---|---|
| 1 | Apollo Bulk Organization Enrichment | 1 Credit je Treffer | 11/11 = 100 % |

Alle 11 kamen als `information technology & services` zurueck - der
CPV-Filter aus Aufgabe 1 hatte also sauber vorselektiert.

**Konzern vs. Rechtstraeger:** Apollo loest die Domain auf den Konzern auf,
die Vergabe ging an den Rechtstraeger. `computacenter.com` -> Hatfield/UK,
21.000 MA statt der deutschen OHG in Kerpen. `bechtle.com` -> Bechtle AG,
17.000 MA statt des regionalen Systemhauses. Konzernwerte werden im Export
als `employees_scope = konzern_oder_unklar` markiert und **nicht** fuers
Tiering verwendet.

## 3. Kontakte (Domain -> Person)

| Stufe | Methode | Kosten | Quote |
|---|---|---|---|
| 1 | Apollo People Search, Titel aus den Personas | 1 Credit je Suche | 15 Personen an 5 Accounts |
| 2 | Apollo People Bulk Match | 1 Credit je Treffer | 15/15 = 100 % gematcht |

**E-Mail-Status:** 13 verifiziert, 1 geraten (`extrapolated`), 1 nicht
verfuegbar. Kein Catch-All in dieser Stichprobe
(`email_domain_catchall_verdict: allow` bei allen).

**Domain-Abgleich als Gegenprobe:** Der Export vergleicht die E-Mail-Domain
mit der Account-Domain. Zwei Abweichungen gefunden:
`karl.freundsberger@controlware.at` (oesterreichische Schwester) und
`t.tabu@arktis.net` (abweichende Domain). Beide gehen nicht ungeprueft raus.

## 4. Telefon (noch offen)

| Stufe | Methode | Kosten | Status |
|---|---|---|---|
| 1 | Impressum-Zentrale (§ 5 DDG Pflichtangabe) | 0 | vorgesehen, hohe erwartete Quote |
| 2 | Apollo Direct Dial | Direct-Dial-Credit | bewusst zurueckgestellt, 75 verfuegbar |

Die Zentrale ist in Deutschland praktisch immer verfuegbar, weil das
Impressum sie vorschreibt - kostenlos und mit belegbarer Quelle. Direct
Dials sind das knappe Gut und werden erst fuer bestaetigte Accounts gezogen.
