"""Zentrale Konfiguration: ICP-Filter, CPV-Profile, Ausschlusslisten, Signal-Gewichte.

Alle fachlichen Annahmen stehen HIER und nirgends sonst im Code verstreut.
Das ist Absicht: Im Review muss eine Person die ICP-Definition an einer Stelle
lesen und aendern koennen.
"""

# --- CPV-Profil IT-Systemhaus -------------------------------------------------
# Zwei Darstellungen, weil die beiden Quellen unterschiedlich filtern:
#
# OCDS (oeffentlichevergabe.de) liefert die CPV-Codes als Strings im Datensatz;
# wir filtern clientseitig ueber Praefixe.
CPV_IT_PREFIXES = [
    "48",        # Softwarepakete und Informationssysteme
    "72",        # IT-Dienstleistungen: Beratung, Entwicklung, Internet, Support
    "302",       # Buero- und Datenverarbeitungsmaschinen, Geraete
    "5031",      # Wartung/Reparatur Buero- und DV-Technik
    "5032",      # Wartung/Reparatur PC
    "5161",      # Installation von Computern und Bueroausstattung
    "642",       # Telekommunikationsdienste
]

# TED filtert serverseitig und akzeptiert KEINE Praefixe:
#   classification-cpv=72  -> HTTP 400 QUERY_UNSUPPORTED_FIELD_VALUE
# Stattdessen der vollstaendige 8-stellige Wurzelcode. Verifiziert am
# 23.09.2026: "=72000000" liefert dasselbe Ergebnis wie "=72*" (398.987
# Notices), die Hierarchie wird also serverseitig mit aufgeloest.
CPV_IT_ROOTS_TED = [
    "48000000",  # Softwarepakete und Informationssysteme
    "72000000",  # IT-Dienstleistungen
    "30200000",  # Datenverarbeitungsgeraete
    "50300000",  # Wartung/Reparatur DV-Technik
    "51600000",  # Installation von Computern
    "64200000",  # Telekommunikationsdienste
]

# --- Ausschlusslisten ---------------------------------------------------------
# Oeffentliche IT-Dienstleister / Inhouse-Gesellschaften.
# Das sind AUFTRAGGEBER bzw. Inhouse-Vergabe-Empfaenger -> die Gegenseite
# unseres Zielkunden. Sie verschmutzen jede Liste, die ueber "Vergabe" sucht.
PUBLIC_INHOUSE_PROVIDERS = [
    "dataport", "itzbund", "informationstechnikzentrum bund", "akdb",
    "komm.one", "kommone", "regio it", "regioit", "ekom21", "krzn", "citeq",
    "lvr-infokom", "lwl.it", "zit-bb", "dvz", "datenzentrale", "it.niedersachsen",
    "it.nrw", "landesamt fuer digitalisierung", "kdo", "kdrs", "kivbf",
    "zweckverband", "kommunales rechenzentrum", "kommunale datenverarbeitung",
]

# Wettbewerber, Vergabeportale, Vergabeberatung -> niemals Zielkunde.
COMPETITORS_AND_PORTALS = [
    "cosinex", "administration intelligence", "healy hudson", "dtad",
    "deutsches ausschreibungsblatt", "subreport", "vergabe24", "evergabe",
    "staatsanzeiger", "bi-medien", "tender24", "ausschreibungen-deutschland",
    # Vergaberechtskanzleien und Verfahrensbegleiter. Tauchen in TED als
    # "organisation-*-serv-prov" auf und wurden dort frueher faelschlich als
    # Gewinner gelesen - zweite Verteidigungslinie zur Feldkorrektur.
    "vergaberecht", "rechtsanwalt", "rechtsanwaelte", "kanzlei",
    "ausschreibungsberatung", "vergabeberatung",
]

# Reine Produkt-/Handels-/Personalunternehmen -> kein Systemhaus-Motion.
NON_SYSTEMHAUS = [
    "cyberport", "notebooksbilliger", "alternate", "conrad electronic",
    # Personaldienstleister im IT-Umfeld. Ihre Websites sind voller
    # IT-Begriffe und sie gewinnen IT-Ausschreibungen - sie vermitteln aber
    # Menschen, keine IT-Leistung. SThree (Marken u. a. Computer Futures)
    # stand bis 24.09.2026 nicht hier und landete dadurch auf Platz 18 der
    # Signalliste, in Tier A, mit 8 Verfahren.
    # Eine Blacklist faengt solche Faelle immer erst NACH dem Schaden.
    # Systematisch loest das der Sculptor-Klassifikator - siehe
    # docs/clay_sculptor_systemhaus.md.
    "hays", "ferchau", "amadeus fire", "brunel", "gulp",
    "sthree", "computer futures", "hueter", "randstad", "adecco",
    "michael page", "robert half", "solcom", "etengo", "questax",
    "sap se", "software ag", "microsoft deutschland", "oracle deutschland",
]

EXCLUSION_LISTS = {
    "public_inhouse": PUBLIC_INHOUSE_PROVIDERS,
    "competitor_portal": COMPETITORS_AND_PORTALS,
    "non_systemhaus": NON_SYSTEMHAUS,
}

# --- Signal 1: Bid-/Vergabe-Rollen (BA Jobsuche) ------------------------------
# Whitelist: Titel, die auf Bieterseite-Angebotsbearbeitung hindeuten.
JOB_TITLE_INCLUDE = [
    "bid manager", "bid-manager", "bidmanager",
    "angebotsmanager", "angebotsmanagement",
    "ausschreibungsmanager", "ausschreibungsmanagement",
    "tender manager", "tendermanagement",
    "vergabemanager", "vergabemanagement",
    "submission", "bietermanagement",
    "referent ausschreibungen", "referent vergabe",
    "public sector sales", "vertrieb oeffentliche auftraggeber",
    "key account manager public", "account manager oeffentlicher",
]

# Blacklist: gleiche Woerter, aber EINKAUFSseite. Haeufigster False Positive.
JOB_TITLE_EXCLUDE = [
    "strategischer einkaeufer", "einkaeufer", "einkauf",
    "procurement", "beschaffung", "vergabestelle", "vergabesachbearbeiter",
    "vergabejurist", "vergaberecht", "rechtsanwalt",
]

# --- Scoring ------------------------------------------------------------------
SIGNAL_WEIGHTS = {
    "nachpruefung_vergabekammer": 10,   # hat verloren und klagt -> maximaler Schmerz
    "rahmenvertrag_laeuft_aus": 9,      # 6-9 Mon. vor Ablauf -> Neuausschreibung kommt
    "angebot_ohne_zuschlag": 8,         # geboten, ein anderer bekam den Zuschlag
    "offene_ausschreibung_im_profil": 8,
    "bid_rolle_ausgeschrieben": 7,
    "zuschlag_gewonnen": 6,
    "leitungswechsel_public": 5,
    "teilnahme_belegt": 5,              # geboten, Ausgang aus den Daten nicht ableitbar
    "neue_public_referenz": 4,
}

TIER_FIT = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.3}

RECENCY_BUCKETS = [(14, 1.0), (28, 0.8), (42, 0.6), (56, 0.4)]
RECENCY_FLOOR = 0.2

STACKING_BONUS = 2.0          # >= 2 verschiedene Signaltypen im Fenster
SCORE_MAX_RAW = 12.0          # max. Gewicht (10) + Stacking (2) -> Normierung auf 0-100

# Daempfung fuer icp_fit und match_confidence.
# Beide wirken auf [DAMPEN_FLOOR .. 1.0] statt auf [0 .. 1.0]. Sonst loescht
# eine Confidence von 0.65 ein Signal der Staerke 10 faktisch aus, und die
# Rangfolge wird von der Datenqualitaet bestimmt statt vom Anlass.
DAMPEN_FLOOR = 0.40

# Unter dieser Resolver-Confidence wird NICHT geraten, sondern in die
# Review-Queue geschrieben. Praezision vor Volumen.
RESOLUTION_MIN_CONFIDENCE = 0.70

# Enrichment kostet Geld, Signale nicht -> erst scoren, dann anreichern.
#
# KALIBRIERT, nicht geraten. Gemessen am Lauf vom 24.09.2026 ueber 651
# Accounts mit Signal aus 8 Wochen:
#     Schwelle 30 -> 372 Accounts (57 %)
#     Schwelle 35 -> 261 Accounts (40 %)
#     Schwelle 40 -> 200 Accounts (31 %)   <- gewaehlt
#     Schwelle 45 ->  77 Accounts (12 %)
#     Schwelle 50 ->  53 Accounts ( 8 %)
# Ziel war ein Korridor von 20-30 %: genug Volumen fuer eine Woche Outbound,
# ohne den Longtail mitzubezahlen. Zwischen 40 und 45 liegt eine Klippe -
# dort endet die Gruppe mit mehreren oder hoeher gewichteten Signalen.
#
# 31 % liegt knapp ueber dem Korridor. Nicht nachjustiert: Massgeblich ist die
# Klippe (200 -> 77), nicht die runde Zahl. Wer hier auf 42 ginge, um exakt
# 30 % zu treffen, wuerde die Verteilung an den Korridor anpassen statt
# umgekehrt.
#
# Die Zahlen davor (354/237/186/38/29) stammten aus einem Lauf, in dem sich
# Bekanntmachungen desselben Verfahrens gegenseitig ueberschrieben. Nach dem
# Dubletten-Fix in sources/dovs.py ist die Verteilung eine andere - deshalb
# neu gemessen statt fortgeschrieben.
#
# Der Wert gehoert nach jedem groesseren Quellen- oder Gewichtungswechsel
# erneut gegen die Verteilung geprueft.
ENRICH_SCORE_THRESHOLD = 40
