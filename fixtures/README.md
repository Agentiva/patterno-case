# Fixtures

Die JSON-Dateien hier sind **synthetisch** und mit `make_fixtures.py` erzeugt.
Firmennamen sind frei erfunden.

Zweck: `make demo` laeuft ohne Netzzugang und ohne API-Keys. Das ist fuer eine
Live-Demo wichtig, in der man sich nicht auf fremde APIs verlassen will.

Die Struktur entspricht dem **verifizierten** Schema der echten Quellen:
- `ba_jobs.json` -> `JobSearchResponse` aus https://github.com/bundesAPI/jobsuche-api (openapi.yaml v2.1.0)
- `vergabe_dovs.json` -> OCDS-Releases, `releases[].awards[].suppliers[]`

Die Testdaten decken bewusst die Kanten ab, an denen eine Pipeline bricht:
Bietergemeinschaft, oeffentlicher Inhouse-Dienstleister, Wettbewerber,
einkaufsseitige Stellenanzeige, Rahmenvertrag kurz vor Ablauf, Umlaute.

`make run` (live) ueberschreibt die Dateien mit echten API-Antworten.

---
## Stand 23.09.2026: echte Daten

`make run` lief erstmals gegen die Live-APIs. Die Fixtures wurden dabei mit
echten Antworten ueberschrieben und sind nicht mehr synthetisch.
