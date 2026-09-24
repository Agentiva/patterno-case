# Clay Sculptor: Systemhaus-Klassifikator

Schließt die größte offene Lücke der Longlist. **CPV belegt Teilnahme an
IT-Vergaben, nicht das Geschäftsmodell.** Unter den Top 25 der Signalliste
stehen ein Gebäudeautomatisierer, ein Quantencomputer-Hersteller, zwei
Sensorhersteller und ein Personaldienstleister.

Der Klassifikator läuft in Clay über die Domain und entscheidet je Zeile, ob
IT-Dienstleistung für Dritte das **Kerngeschäft** ist.

**Wie groß das Problem ist:** Von den 20 Firmen im Testsatz unten stehen 18 in
**Tier A** — und 6 davon gehören nicht ins ICP. Das ist ein Drittel der
höchstbewerteten Accounts. Ohne diesen Check geht genau diese Spitze zuerst
ins Outbound.

---

## Der Prompt

Spaltentyp **Claygent / Sculptor**, Eingabe: `{{Company Domain}}` und
`{{Company Name}}`.

```
Du prüfst, ob ein Unternehmen als IT-Systemhaus oder IT-Dienstleister
arbeitet. Auftraggeber ist ein Anbieter von Ausschreibungssoftware für
Bieter; die Zielkunden sind Unternehmen, die IT-Leistungen für Dritte
erbringen und sich an öffentlichen Ausschreibungen beteiligen.

UNTERNEHMEN: {{Company Name}}
DOMAIN: {{Company Domain}}

VORGEHEN
Rufe die Website auf und lies in dieser Reihenfolge:
1. Startseite
2. Leistungen / Services / Lösungen / Portfolio
3. Über uns / Unternehmen
4. Referenzen / Branchen / Kunden
5. Karriere (die ausgeschriebenen Rollen verraten das Geschäftsmodell
   zuverlässiger als die Marketingsprache)

ENTSCHEIDUNGSREGEL
Die Leitfrage lautet nicht "hat das Unternehmen mit IT zu tun", sondern:
Erbringt es IT-Leistungen ALS DIENSTLEISTUNG FÜR FREMDE KUNDEN, und ist
das sein Kerngeschäft?

Vergib genau eine Klassifikation:

"systemhaus"
  Plant, liefert, integriert und betreibt IT-Infrastruktur für Kunden.
  Typische Belege: Managed Services, Arbeitsplatz/Client Management,
  Netzwerk, Server, Storage, Rechenzentrum, Cloud-Migration, IT-Security,
  Hersteller-Partnerschaften (Microsoft, Cisco, Dell, HPE, VMware, Citrix),
  eigener Service Desk, SLA, Wartungsverträge.

"it_dienstleister"
  IT-Beratung, Softwareentwicklung, Systemintegration oder IT-Projekte
  für fremde Kunden, aber ohne klassisches Infrastrukturgeschäft.
  Beispiele: Individualentwicklung, Fachverfahren, E-Government-Projekte,
  Test- und Qualitätssicherung, IT-Architekturberatung mit Umsetzung.

"softwarehaus"
  Entwickelt und verkauft ein EIGENES Softwareprodukt. Lizenz- oder
  SaaS-Geschäft steht im Mittelpunkt, Dienstleistung ist Beiwerk
  (Einführung, Schulung, Support des eigenen Produkts).

"it_handel"
  Verkauft überwiegend Hardware, Software-Lizenzen oder Zubehör weiter.
  Shop, Katalog, Preislisten, Distribution. Dienstleistung ist gering
  oder fehlt.

"kein_it_dienstleister"
  Alles andere. Dazu gehören ausdrücklich:
  - Hersteller von Geräten, Anlagen, Sensorik, Medizintechnik
  - Gebäude-, Anlagen- und Prozessautomation
  - Telekommunikations- und Netzbetreiber (Carrier)
  - Personaldienstleister, Zeitarbeit, IT-Freelancer-Vermittlung
  - Ingenieur-, Planungs- und Architekturbüros
  - reine Managementberatung ohne IT-Umsetzung
  - Behörden, Eigenbetriebe, kommunale Rechenzentren, Zweckverbände
  - Forschungseinrichtungen, Hochschulen, Vereine

"nicht_pruefbar"
  Die Website ist nicht erreichbar, leer, im Aufbau, oder der Inhalt
  reicht für eine Entscheidung nicht aus.

ABGRENZUNGEN, DIE HÄUFIG FALSCH LAUFEN
- Ein Unternehmen, das IT EINKAUFT oder intern betreibt, ist KEIN
  IT-Dienstleister. Entscheidend ist der Verkauf an Dritte.
- Ein Hersteller, der seine eigenen Geräte auch installiert und wartet,
  bleibt Hersteller.
- Gebäudeautomation, Verkehrstechnik, Sicherheitstechnik und Sensorik
  sind kein IT-Systemhausgeschäft, auch wenn Software enthalten ist.
- Personalvermittlung im IT-Umfeld ist kein IT-Dienstleister, auch wenn
  die Website voller IT-Begriffe steht.
- Ein Konzern mit vielen Geschäftsbereichen wird nach dem Bereich
  beurteilt, der zum genannten Unternehmensnamen gehört. Wenn die Domain
  auf den Gesamtkonzern zeigt, vermerke das.

BELEGPFLICHT
Jede Klassifikation braucht ein wörtliches Zitat von der Website, das sie
trägt, plus die URL der Seite, auf der es steht.

Wenn du die Website nicht erreichst oder der Inhalt nicht ausreicht:
setze "nicht_pruefbar". Schreibe dann NICHT, was du vermutest, und leite
nichts aus dem Firmennamen ab. Eine ehrliche Lücke ist brauchbar, eine
geratene Einordnung nicht.

AUSGABE
Antworte ausschließlich mit diesem JSON, ohne Text davor oder danach:

{
  "klassifikation": "systemhaus | it_dienstleister | softwarehaus | it_handel | kein_it_dienstleister | nicht_pruefbar",
  "im_icp": "ja | nein",
  "begruendung": "ein bis zwei Sätze, warum diese Klasse",
  "beleg_zitat": "wörtliches Zitat von der Website",
  "beleg_url": "URL der Seite mit dem Zitat",
  "leistungen": ["bis zu 5 Leistungen in den Worten der Website"],
  "hersteller_partner": ["genannte Partnerschaften, sonst leer"],
  "oeffentlicher_sektor": "ja | nein | unklar",
  "domain_zeigt_auf": "rechtstraeger | konzern | unklar",
  "konfidenz": 0.0 bis 1.0
}

"im_icp" ist "ja" bei "systemhaus" und "it_dienstleister", sonst "nein".
```

---

## Einrichtung in Clay

| Schritt | Spalte | Einstellung |
|---|---|---|
| 1 | **Systemhaus-Check** | Claygent/Sculptor, Prompt oben, Eingabe `Company Domain` + `Company Name` |
| 2 | **klassifikation** | Formel: `{{Systemhaus-Check.klassifikation}}` |
| 3 | **im_icp** | Formel: `{{Systemhaus-Check.im_icp}}` |
| 4 | **beleg_zitat** | Formel: `{{Systemhaus-Check.beleg_zitat}}` |
| 5 | **konfidenz** | Formel: `{{Systemhaus-Check.konfidenz}}` |

**Conditional Run auf allen nachgelagerten Spalten** (Find People, Work
Email, Sequenz):

```
{{im_icp}} = "ja" AND {{konfidenz}} >= 0.7
```

Damit zahlst du Anreicherungs-Credits nur für Accounts, die den Check
bestanden haben. Bei 2.458 Zeilen ist das der Unterschied zwischen einem
vierstelligen und einem dreistelligen Credit-Verbrauch.

**Reihenfolge nicht vertauschen.** Der Klassifikator läuft *vor* der
Personensuche, nicht danach. Sonst hast du Kontakte bei Siemens
Gebäudeautomation gekauft, bevor du weißt, dass sie nicht ins ICP gehören.

---

## Der Testsatz — vor dem Volllauf

Lass den Prompt zuerst über diese 20 Zeilen laufen. Alle stammen aus der
echten Signalliste, die erwartete Klasse steht daneben. **Stimmen weniger
als 17 von 20, geh nicht in den Volllauf** — dann korrigiere den Prompt an
den Fällen, die danebenliegen.

### Muss „ja" ergeben

| Unternehmen | Tier · Verf. | Domain | erwartet |
|---|---|---|---|
| SCALTEL GmbH & Co. KG | A · 4 | | `systemhaus` |
| Bechtle GmbH & Co. KG | A · 104 | `bechtle.com` | `systemhaus` |
| CANCOM GmbH | A · 51 | | `systemhaus` |
| Computacenter AG & Co. oHG | A · 68 | | `systemhaus` |
| netgo Ost GmbH | A · 11 | `netgo.de` | `systemhaus` |
| sysGen GmbH | A · 20 | | `systemhaus` |
| itec systems AG | A · 5 | | `systemhaus` |
| thinkRED GmbH | A · 8 | `thinkred.de` | `systemhaus` |
| Controlware GmbH | A · 17 | `controlware.de` | `systemhaus` |
| Cassini Consulting AG | A · 5 | | `it_dienstleister` |
| Sopra Steria SE | A · 26 | | `it_dienstleister` |
| Semper Prospera GmbH | A · 3 | | `it_dienstleister` |
| SimplyTest GmbH | B · 2 | | `it_dienstleister` |
| d.velop AG | A · 20 | | `softwarehaus` — **Grenzfall, bewusst dabei** |

### Muss „nein" ergeben

Alle sechs stehen in **Tier A**. Das ist der Punkt.

| Unternehmen | Tier · Verf. | Domain | warum nicht ICP |
|---|---|---|---|
| **Siemens AG** | A · 6 | `siemens.com` | Gebäude- und Anlagenautomation |
| **ARQUE Systems GmbH** | B · 2 | | Quantencomputer-Hersteller |
| **iris-GmbH infrared & intelligent sensors** | A · 3 | | Sensorhersteller |
| **Derovis GmbH** | A · 3 | | Fahrzeugzählanlagen |
| **TraffGo Road GmbH** | A · 4 | | Verkehrsflussmessung |
| **SThree GmbH** | A · 8 | `sthree.com` | Personaldienstleister (Computer Futures) |

**SThree ist der lehrreichste Fall — und der Beweis, dass eine Blacklist
nicht reicht.** Die Website ist voller IT-Begriffe, das Unternehmen gewinnt
IT-Ausschreibungen, und es vermittelt Personal. Die Ausschlussliste kannte
Hays, FERCHAU, GULP, Brunel und Amadeus FiRe — aber nicht SThree.

Ich habe SThree und neun weitere Personaldienstleister nachgetragen. Ergebnis:
**2.468 → 2.458 Firmen**, SThree ist aus den Top 20 verschwunden.

Siemens, ARQUE Systems, iris-GmbH, Derovis und TraffGo stehen **weiterhin
drin** — und lassen sich auch nicht sinnvoll eintragen. Man kann nicht
aufzählen, was alles *kein* Systemhaus ist. Eine Blacklist fängt jeden Fall
erst nach dem Schaden; der Klassifikator entscheidet vorher und für jede
Zeile.

**d.velop ist der zweitlehrreichste.** Eigenes Produkt (Dokumentenmanagement),
aber 20 Verfahren bei 19 Auftraggebern in zwölf Monaten. Wenn der
Klassifikator hier `softwarehaus` sagt und du `im_icp = nein` setzt,
verlierst du einen Account mit nachweislich hoher Bieterfrequenz. Entscheide
das bewusst — und wenn du Softwarehäuser mitnehmen willst, ändere die
`im_icp`-Regel im Prompt statt die Klasse.

---

## Kosten und Laufzeit

| | |
|---|---|
| Sculptor-Lauf je Zeile | 3 Credits, mehrere Seitenaufrufe |
| Testsatz (20 Zeilen) | 60 Credits, ein paar Minuten |
| Volllauf über die 233 Tier-A-Accounts | ~700 Credits |

**Nicht über alle 2.458 Zeilen laufen lassen.** Erst über die 233 Tier-A-
Accounts, dann über Tier B. Tier C braucht den Check gar nicht, solange du
dort kein Outbound fährst.

Das Ergebnis ist dauerhaft: Ein Geschäftsmodell ändert sich nicht wöchentlich.
Schreib `klassifikation` zurück in die Longlist, dann läuft der Check je
Unternehmen genau einmal — nicht bei jedem wöchentlichen Signal erneut.

---

## Was der Klassifikator nicht kann

- **Websites, die nichts verraten.** Kleine Systemhäuser haben oft eine
  Seite mit drei Sätzen. Dort kommt `nicht_pruefbar` — das ist richtig so
  und geht in die Handprüfung, nicht ins Outbound.
- **Konzerne mit gemischtem Portfolio.** Die Domain zeigt auf den Konzern,
  der Zuschlag ging an eine Tochter. Deshalb das Feld `domain_zeigt_auf` —
  bei `konzern` gehört die Zeile in die Prüfung.
- **Die Größenfrage.** Ob ein Systemhaus 30 oder 3.000 Mitarbeitende hat,
  beantwortet die Website selten verlässlich. Das bleibt bei `employees`
  und geht ohnehin nicht ins Tier ein (siehe [tiering.md](tiering.md)).

Der Klassifikator ersetzt die Sichtprüfung nicht vollständig. Er reduziert
sie von 2.458 Zeilen auf die, bei denen er `nicht_pruefbar`, `konzern` oder
eine Konfidenz unter 0,7 meldet.
