#!/usr/bin/env python3
"""Erzeugt SYNTHETISCHE Fixtures im echten Schema der beiden Quellen.

WARUM SYNTHETISCH:
Die Zielsysteme (oeffentlichevergabe.de, rest.arbeitsagentur.de) sind aus
dieser Umgebung heraus nicht erreichbar. Statt echte Daten zu behaupten,
erzeugen wir Testdaten, die dem VERIFIZIERTEN Schema entsprechen:

  - BA Jobsuche: Felder aus openapi.yaml v2.1.0
    https://github.com/bundesAPI/jobsuche-api  (JobSearchResponse)
  - DOEE: OCDS-Release-Struktur (releases[].awards[].suppliers[])
    https://oeffentlichevergabe.de/documentation/swagger-ui/opendata/index.html

Die Firmennamen sind FREI ERFUNDEN. Sobald `make run` gegen die echten
APIs laeuft, werden diese Dateien durch echte Antworten ueberschrieben.

Die Fixtures decken bewusst die Kanten ab, an denen eine Pipeline bricht:
  - Bietergemeinschaft in einem Feld
  - oeffentlicher Inhouse-Dienstleister (muss ausgeschlossen werden)
  - Wettbewerber/Portalbetreiber (muss ausgeschlossen werden)
  - Einkaufsseitige Stellenanzeige (False Positive des Job-Signals)
  - Rahmenvertrag mit Ende in ~7 Monaten (Expiry-Signal)
  - Umlaute und "GmbH & Co. KG" (Normalisierung)
"""
import json
from datetime import date, timedelta
from pathlib import Path

FIX = Path(__file__).resolve().parent
today = date.today()
d = lambda n: (today - timedelta(days=n)).isoformat()      # noqa: E731
fwd = lambda n: (today + timedelta(days=n)).isoformat()    # noqa: E731


def award(ocid, buyer, title, cpv, suppliers, award_days_ago, contract_end=None):
    a = {
        "id": f"AWD-{ocid[-4:]}",
        "date": d(award_days_ago) + "T10:00:00+02:00",
        "value": {"amount": 480000, "currency": "EUR"},
        "suppliers": suppliers,
    }
    if contract_end:
        a["contractPeriod"] = {"endDate": contract_end + "T23:59:59+02:00"}
    return {
        "ocid": ocid,
        "date": d(award_days_ago) + "T10:00:00+02:00",
        "buyer": {"name": buyer, "address": {"locality": "Musterstadt"}},
        "tender": {
            "title": title,
            "classification": {"scheme": "CPV", "id": cpv},
            "items": [{"classification": {"scheme": "CPV", "id": cpv}}],
        },
        "awards": [a],
    }


def sup(name, locality, plz, sid=None):
    return {
        "id": sid, "name": name,
        "address": {"locality": locality, "postalCode": plz, "countryName": "Deutschland"},
    }


# --- Vergabedaten -------------------------------------------------------------
vergabe = [
    # 1) frischer Zuschlag, sauberer Fall
    award("ocds-pat-0001", "Stadt Beispielheim", "Rahmenvertrag Client-Hardware und Support",
          "30213000", [sup("Nordlicht IT-Systemhaus GmbH", "Lüneburg", "21335", "DE-HRB-111")], 12),

    # 2) Rahmenvertrag laeuft in ~7 Monaten aus -> Expiry-Signal
    award("ocds-pat-0002", "Landkreis Musterau", "Rahmenvereinbarung Netzwerkbetrieb",
          "72510000", [sup("Südwest Systemtechnik GmbH & Co. KG", "Karlsruhe", "76131", "DE-HRB-222")],
          400, contract_end=fwd(215)),

    # 3) Bietergemeinschaft - muss in zwei Firmen aufgeteilt werden
    award("ocds-pat-0003", "Universität Beispielstadt", "Migration Groupware",
          "72263000",
          [sup("ARGE Rheinbit GmbH + Moselwerk IT AG", "Koblenz", "56068")], 20),

    # 4) oeffentlicher Inhouse-Dienstleister -> muss ausgeschlossen werden
    award("ocds-pat-0004", "Freie Hansestadt Beispiel", "Betrieb Fachverfahren",
          "72500000", [sup("Dataport AöR", "Altenholz", "24161")], 15),

    # 5) Wettbewerber/Portalbetreiber -> muss ausgeschlossen werden
    award("ocds-pat-0005", "Land Beispielstein", "Betrieb Vergabeplattform",
          "48000000", [sup("cosinex GmbH", "Bochum", "44787")], 25),

    # 6) Nicht-IT-CPV -> muss durch den CPV-Filter fallen
    award("ocds-pat-0006", "Gemeinde Randfall", "Dachsanierung Grundschule",
          "45261000", [sup("Musterdach GmbH", "Kassel", "34117")], 10),

    # 7) offenes Verfahren, Frist in 18 Tagen -> Buyer-Side-Signal
    {
        "ocid": "ocds-pat-0007",
        "date": d(4) + "T08:00:00+02:00",
        "buyer": {"name": "Bundesamt für Beispielwesen",
                  "address": {"locality": "Bonn"}},
        "tender": {
            "title": "Beschaffung Managed Workplace Services",
            "classification": {"scheme": "CPV", "id": "72514000"},
            "items": [{"classification": {"scheme": "CPV", "id": "72514000"}}],
            "tenderPeriod": {"endDate": fwd(18) + "T12:00:00+02:00"},
            "value": {"amount": 2400000, "currency": "EUR"},
        },
    },
]

# --- Stellenanzeigen ----------------------------------------------------------
ba_jobs = [
    {  # sauberer Treffer
        "refnr": "10000-BEISPIEL-001", "titel": "Bid Manager (m/w/d) Public Sector",
        "beruf": "Vertriebsmanager/in", "arbeitgeber": "Nordlicht IT-Systemhaus GmbH",
        "aktuelleVeroeffentlichungsdatum": d(9), "eintrittsdatum": fwd(30),
        "arbeitsort": {"plz": 21335, "ort": "Lüneburg", "region": "Niedersachsen",
                       "land": "Deutschland"},
    },
    {  # zweiter Signaltyp auf derselben Firma -> Stacking-Bonus
        "refnr": "10000-BEISPIEL-002", "titel": "Angebotsmanager Ausschreibungen (m/w/d)",
        "beruf": "Kaufmann/-frau", "arbeitgeber": "Südwest Systemtechnik GmbH & Co. KG",
        "aktuelleVeroeffentlichungsdatum": d(21), "eintrittsdatum": fwd(60),
        "arbeitsort": {"plz": 76131, "ort": "Karlsruhe", "region": "Baden-Württemberg",
                       "land": "Deutschland"},
    },
    {  # FALSE POSITIVE: Einkaufsseite, muss die Blacklist ziehen
        "refnr": "10000-BEISPIEL-003",
        "titel": "Strategischer Einkäufer / Vergabemanager (m/w/d)",
        "beruf": "Einkäufer/in", "arbeitgeber": "Stadtverwaltung Beispielheim",
        "aktuelleVeroeffentlichungsdatum": d(5), "eintrittsdatum": fwd(45),
        "arbeitsort": {"plz": 30159, "ort": "Hannover", "region": "Niedersachsen",
                       "land": "Deutschland"},
    },
    {  # kein Titel-Match -> faellt durch die Whitelist
        "refnr": "10000-BEISPIEL-004", "titel": "Fachinformatiker Systemintegration (m/w/d)",
        "beruf": "Fachinformatiker/in", "arbeitgeber": "Rheinbit GmbH",
        "aktuelleVeroeffentlichungsdatum": d(3), "eintrittsdatum": fwd(14),
        "arbeitsort": {"plz": 56068, "ort": "Koblenz", "region": "Rheinland-Pfalz",
                       "land": "Deutschland"},
    },
    {  # Treffer auf einem Konsortialmitglied
        "refnr": "10000-BEISPIEL-005", "titel": "Tender Manager (m/w/d)",
        "beruf": "Kaufmann/-frau", "arbeitgeber": "Moselwerk IT AG",
        "aktuelleVeroeffentlichungsdatum": d(30), "eintrittsdatum": fwd(90),
        "arbeitsort": {"plz": 54290, "ort": "Trier", "region": "Rheinland-Pfalz",
                       "land": "Deutschland"},
    },
]

(FIX / "vergabe_dovs.json").write_text(
    json.dumps(vergabe, ensure_ascii=False, indent=2), encoding="utf-8")
(FIX / "ba_jobs.json").write_text(
    json.dumps(ba_jobs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"vergabe_dovs.json: {len(vergabe)} Releases")
print(f"ba_jobs.json:      {len(ba_jobs)} Stellenanzeigen")
