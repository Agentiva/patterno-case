# Apollo.io Filter-Empfehlung — IT-Systemhäuser (Patterno)

Für **Clay → Find People / Apollo People Search**. Die Domain steht in Clay
bereits je Zeile, also läuft die Suche pro Account über
`q_organization_domains_list` — Firmenfilter sind dann nur noch Gegenprobe.

> **Grundlage:** Alle Titel unten stammen aus einem echten Apollo-Lauf gegen
> fünf Tier-A-Accounts (Controlware, MR Datentechnik, ARKTIS IT solutions,
> WBS IT-Service, iteratec) am 23.09.2026. Es sind keine ausgedachten
> Titelvarianten, sondern die Schreibweisen, die tatsächlich im Index stehen.

---

## Filter: Champion — Bid & Tender (Priorität 1)

| Kriterium | Werte |
|---|---|
| **Jobtitel** | Bid Manager, Senior Bid Manager, Bid Managerin, Bid & Proposal Manager, Proposal Manager, Tender Manager, Tender Managerin, Tender-/Bid Manager, Team Lead Tender Management, Tendermanagement, Tender Management Public Sector, Ausschreibungsmanager, Ausschreibungsmanagerin, Ausschreibungsmanagement, Angebotsmanager, Angebotsmanagerin, Leiter Angebotswesen, Leiter Angebotsmanagement, Bietermanagement, Submission, Submissionsbearbeitung, Vergabemanagement, Referent Ausschreibungen, Mitarbeiter Ausschreibungen, Kalkulation öffentliche Auftraggeber |
| **Seniority** | manager, senior, head, director, lead |
| **Standort (Person)** | Deutschland |
| **Ausschluss-Jobtitel** | Strategischer Einkäufer, Einkäufer, Leiter Einkauf, Einkaufsleiter, Head of Procurement, Procurement Manager, Beschaffungsmanager, Vergabesachbearbeiter, Vergabestelle, Vergabejurist, Vergaberecht, Rechtsanwalt, Justiziar, Recruiter, Talent Acquisition, Personalreferent |

**Warum die weiblichen Formen einzeln gelistet sind:** Apollo matcht Titel als
Zeichenkette. „Bid Managerin" und „Tender Managerin" sind im deutschen Index
real vorhanden (zwei der sechs gefundenen Champions bei Controlware hießen so)
und werden von „Bid Manager" **nicht** mitgefunden, wenn
`include_similar_titles = false` gesetzt ist.

**Einstellung:** `include_similar_titles = true` beim ersten Lauf. Die
Schreibweisen im deutschen Mittelstand sind zu uneinheitlich
(„Tender-/Bid Manager", „Tendermanagement" ohne Rolle im Titel). Erst wenn
die Trefferliste verrauscht, auf `false` wechseln und die Titelliste erweitern.

---

## Filter: Economic Buyer (Priorität 2)

Greift, wenn Priorität 1 keinen Treffer liefert — bei iteratec war das im Test
der Fall: Software-Beratung ohne dedizierte Angebotsabteilung.

| Kriterium | Werte |
|---|---|
| **Jobtitel** | Geschäftsführer, Geschäftsführerin, Geschäftsführender Gesellschafter, Managing Director, Inhaber, Vorstand, Kaufmännischer Leiter, Kaufmännischer Geschäftsführer, Prokurist, Vertriebsleiter, Leiter Vertrieb, Head of Sales, Director Sales, Sales Director, Head of Public Sector, Leiter Öffentliche Auftraggeber, Leiter Public Sector, Business Unit Leiter Public, Niederlassungsleiter, Standortleiter, Regionalleiter |
| **Seniority** | owner, founder, c_suite, director, head, vp |
| **Standort (Person)** | Deutschland |

---

## Filter: Nutzer & interne Fürsprecher (Priorität 3)

Nur ziehen, wenn nach Priorität 1 und 2 noch Kontaktplätze frei sind
(max. 3 je Account).

| Kriterium | Werte |
|---|---|
| **Jobtitel** | Key Account Manager Public Sector, Key Account Manager Öffentliche Auftraggeber, Account Manager Public, Vertriebsbeauftragter Öffentliche Auftraggeber, Pre-Sales Consultant, Presales Manager, Solution Sales Manager, Technical Sales Manager, Inside Sales Manager, Vertriebsinnendienst, Sales Consulting Manager, Projektleiter Öffentliche Auftraggeber |
| **Seniority** | manager, senior |
| **Standort (Person)** | Deutschland |

---

## Firmenfilter (Gegenprobe, wenn ohne Domainliste gesucht wird)

| Kriterium | Werte |
|---|---|
| **Industrie** | Information Technology & Services, Computer & Network Security, Computer Software, Computer Hardware, Telecommunications, Management Consulting (nur mit IT-Umsetzung) |
| **NAICS** | 5415 (Computer Systems Design and Related Services), 541512, 541513, 541519, 5112 |
| **SIC** | 7373 (Computer Integrated Systems Design), 7379, 7371, 5045 |
| **Mitarbeiter** | 50–2.000 · Sweet Spot 50–500 |
| **Standort (Firma)** | Deutschland, deutschlandweit |
| **Keywords (bedarfsorientiert)** | Systemhaus, IT-Systemhaus, IT-Dienstleister, Managed Services, Managed Service Provider, IT-Infrastruktur, Systemintegration, IT-Integration, Netzwerktechnik, Rechenzentrum, Client Management, Arbeitsplatz, Digital Workplace, Server, Storage, Virtualisierung, Cloud-Migration, IT-Security, Cybersecurity, SOC, IT-Beratung, Fachverfahren, E-Akte, E-Government, Digitalisierung Verwaltung, Behörde, Kommune, öffentliche Auftraggeber, öffentliche Hand, Landesverwaltung, Schul-IT, Hochschul-IT, Klinik-IT, EVB-IT, UfAB, VgV, Rahmenvertrag, Ausschreibung, Vergabe, BSI-Grundschutz, ISO 27001, BSI C5, Präqualifikation |
| **Ausschluss-Keywords** | Ausschreibungssoftware, Vergabesoftware, Bietersoftware, Vergabeplattform, Vergabeportal, eVergabe, DTVP, Vergabe24, Staatsanzeiger, subreport, cosinex, Administration Intelligence, Vergabestelle, Beschaffungsamt, Vergabekammer, Vergaberecht, Ausschreibungsberatung, Fördermittelberatung, Dataport, ITZBund, AKDB, Komm.ONE, regio iT, ekom21, KRZN, kommunales Rechenzentrum, Zweckverband, Behörde (als Arbeitgeber), Zeitarbeit, Arbeitnehmerüberlassung, Personaldienstleister, Recruiting, Distribution, Großhandel, Onlineshop, Baumarkt |

---

## Die drei Fallen, die im Testlauf zugeschnappt sind

**1. Die Einkaufsseite ist der häufigste Fehltreffer.**
„Vergabemanager" sitzt genauso in der Kommune wie beim Bieter. Ohne die
Ausschluss-Jobtitel zieht die Suche Vergabestellen — also exakt das Gegenüber
des Zielkunden. Die Blacklist läuft deshalb **vor** der Whitelist.

**2. Eine Stellenanzeige macht kein Systemhaus.**
Als wir Bid-Rollen ohne Branchenfilter suchten, kamen Max Bögl (Bau),
HAMBURG WASSER (Versorger, Auftraggeberseite!), TRON gGmbH (Biotech) und
Skan-Tours (Tourismus). Von 31 reinen Job-Treffern waren rund 4 IT-Systemhäuser
— **13 % Präzision**. In Clay heißt das: Personensuche immer gegen die
domainverifizierte Longlist, nie freihändig über Titel allein.

**3. E-Mail-Domain gegen Account-Domain prüfen.**
Zwei von 15 angereicherten Kontakten hatten eine abweichende Domain:
`karl.freundsberger@controlware.at` (österreichische Schwester) und
`t.tabu@arktis.net`. In Clay als Formelspalte abbilden:
`if(email_domain != account_domain, "PRÜFEN", "ok")`.

---

## Reihenfolge in Clay

```
1. Longlist (domainverifiziert)
2. Find People  → Priorität 1 (Champion)        max. 2 Kontakte
3. Falls 0 Treffer → Priorität 2 (Buyer)        max. 2 Kontakte
4. Auffüllen auf 3 → Priorität 3 (Nutzer)
5. Work Email finden  → Status mappen: verified / catch_all / extrapolated
6. Formelspalte Domain-Abgleich
7. Nur Zeilen mit Status ≠ extrapolated in die Sequenz
```

Erst scoren, dann anreichern: Die Signale aus Aufgabe 2 kosten nichts, das
Kontakt-Enrichment schon. Personensuche deshalb nur für Accounts über der
Score-Schwelle.
