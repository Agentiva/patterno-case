# Enrichment-Waterfalls mit gemessenen Trefferquoten

Alle Zahlen sind an echten Daten gemessen, Stand 23.09.2026. Keine Schaetzungen.

## 1. Domain-Resolution (Firmenname aus Vergabedaten -> Domain)

| Stufe | Methode | Kosten | Ergebnis |
|---|---|---|---|
| 1 | Apollo Organizations Lookup, voller Name + Ortsfilter Deutschland | 0 | praezise, aber loechrig |
| 2 | Apollo Lookup, verkuerzter Name, OHNE Ortsfilter | 0 | mehr Treffer, hohe Fehlerquote |
| 3 | Impressum abrufen (§ 5 DDG) und gegen Firmenname + Ort der Vergabe pruefen | 0 | harter Beleg |
| 4 | Manuelle Review-Queue | Zeit | Rest |

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
