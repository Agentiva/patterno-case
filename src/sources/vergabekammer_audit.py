"""Quellenaudit fuer die vierte Signalquelle: Vergabekammer-Entscheidungen.

=== WARUM DIESES SKRIPT VOR DEM ADAPTER KOMMT ===
In diesem Projekt sind drei Signaltypen gebaut worden, die nie gefeuert haben,
weil vorher niemand geprueft hat, ob das Feld ueberhaupt existiert:
  rahmenvertrag_laeuft_aus       las awards[].contractPeriod  -> 0 Treffer
  offene_ausschreibung_im_profil las tender.tenderPeriod      -> 0 Treffer
  nachpruefung_vergabekammer     war nur spezifiziert         -> nie gebaut

Jedes Mal sah der Lauf erfolgreich aus. Deshalb gilt fuer die vierte Quelle
die umgekehrte Reihenfolge: erst messen, dann bauen.

Dieses Skript beantwortet drei Fragen, bevor eine Zeile Adapter entsteht:

  1. ERREICHBARKEIT  Antwortet die Quelle ueberhaupt, und mit was?
  2. AUFFINDBARKEIT  Sind einzelne Entscheidungen verlinkt und abrufbar?
  3. NAMENSQUOTE     Steht die Antragstellerin namentlich im Text -
                     oder nur "die Antragstellerin"?

Frage 3 entscheidet alles. Eine anonymisierte Entscheidung ist als Signal
wertlos: Ohne Firmennamen gibt es keinen Account. Liegt die Namensquote unter
MIN_NAMENSQUOTE, wird der Adapter nicht gebaut.

=== WAS AM 24.09.2026 GEMESSEN WURDE ===
  bundeskartellamt.de, statische Seiten      HTTP 200, 148 KB
  bundeskartellamt.de, Entscheidungssuche    HTTP 403  <- WAF, nicht der Proxy
  openjur.de                                 HTTP 200
  rechtsprechung-im-internet.de              HTTP 200
  landesrecht-bw.de                          HTTP 200
  vergabekammer.nrw.de                       nicht aufloesbar

Der 403 kam vom Server, nicht vom Egress-Proxy - dessen Statusendpunkt meldete
nur einen einzigen Relay-Fehler, und zwar fuer eine andere Domain. Der
Such-Endpunkt des Bundeskartellamts blockt also HTTP-Clients gezielt.

FOLGERUNG: Die wichtigste Einzelquelle (Vergabekammer des Bundes, rund 2.200
Verfahren in 12 Monaten) braucht einen echten Browser. Genau dafuer ist Apify
da - und es ist das erste belastbare Argument fuer Apify in diesem Projekt.

=== WELCHE KAMMERN UEBERHAUPT ZAEHLEN ===
Der OCDS-Feed nennt je Verfahren die zustaendige Stelle
(parties[].roles = "reviewBody"): 12.326 Nennungen, 652 verschiedene Stellen.
Die Verteilung ist stark konzentriert, deshalb reichen rund 15 Quellen:

  ~2.200  Vergabekammer des Bundes (drei Namensvarianten!)
     593  Vergabekammer Westfalen
     573  Vergabekammer des Landes Berlin
     424  Vergabekammer Hessen
     409  Vergabekammer Baden-Wuerttemberg
     355  Vergabekammer Niedersachsen
     329  Vergabekammer Rheinland
     324  Vergabekammer Suedbayern
     313  1. Vergabekammer des Freistaates Sachsen

Die Namensvarianten sind kein Schoenheitsfehler: Ohne Normalisierung zaehlt
man die Kammer des Bundes dreimal und priorisiert falsch.

Aufruf:
    python3 -m src.sources.vergabekammer_audit
    python3 -m src.sources.vergabekammer_audit --stichprobe 20
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import requests

DATA = Path("data")
TIMEOUT = 25
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PatternoCaseBot/1.0; +Quellenaudit)",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
}

# Unter dieser Quote wird der Adapter nicht gebaut. Der Wert ist eine
# Entscheidungsschwelle, keine Messung: Bei weniger als jeder dritten
# namentlich genannten Antragstellerin kostet die Quelle mehr Pflege, als
# sie an Accounts einbringt.
MIN_NAMENSQUOTE = 0.30

# Nach Volumen aus dem OCDS-Feed (reviewBody), siehe Modulkopf.
QUELLEN = [
    {
        "kammer": "Vergabekammer des Bundes",
        "verfahren_12m": 2206,
        "url": "https://www.bundeskartellamt.de/DE/Vergaberecht/vergaberecht_node.html",
        "such_url": ("https://www.bundeskartellamt.de/SiteGlobals/Forms/Suche/"
                     "Entscheidungsdatenbanksuche_Formular.html"
                     "?nn=299718&cl2Categories_Arbeitsbereich=vergaberecht"
                     "&sortOrder=dateOfIssue_dt+desc&pageLocale=de"),
    },
    {
        "kammer": "Rechtsprechung im Internet (Bund)",
        "verfahren_12m": 0,
        "url": "https://www.rechtsprechung-im-internet.de",
        "such_url": "",
    },
    {
        "kammer": "openJur",
        "verfahren_12m": 0,
        "url": "https://openjur.de",
        "such_url": "",
    },
    {
        "kammer": "Landesrecht Baden-Wuerttemberg",
        "verfahren_12m": 409,
        "url": "https://www.landesrecht-bw.de",
        "such_url": "",
    },
    {
        "kammer": "Vergabekammer NRW",
        "verfahren_12m": 593,
        "url": "https://www.vergabekammer.nrw.de",
        "such_url": "",
    },
]

# --- Namensquote ---------------------------------------------------------------
# Eine Entscheidung ist nur dann als Signal brauchbar, wenn neben der
# Rollenbezeichnung eine Firmierung steht.
# Ein einziges Muster statt einer Schleife ueber Einzelbegriffe: "antragsteller"
# matcht sonst innerhalb von "antragstellerin", und jede Nennung wird doppelt
# gezaehlt. Die laengere Variante steht vorn, \b verhindert Teiltreffer.
ROLLEN_RE = re.compile(
    r"\b(antragstellerin|antragsteller|antragsgegnerin|antragsgegner"
    r"|beigeladenen|beigeladener|beigeladene)\b", re.IGNORECASE)
# Kleinschreibung ist Absicht: "msg systems ag" und "adesso SE" stehen so im
# Handelsregister und in meiner Longlist. Eine Regex, die Grossschreibung
# verlangt, haette beide fuer anonymisiert gehalten.
# Rechtsformen bewusst NICHT global case-insensitive, sondern mit
# ausgeschriebenen Kleinvarianten - sonst matcht \bag\b in Fliesstext.
FIRMA = re.compile(
    r"\b[\wÄÖÜäöüß&.\-]{2,}(?:[ \t]+[\wÄÖÜäöüß0-9&.\-]+){0,5}[ \t]+"
    r"(GmbH[ \t]*&[ \t]*Co\.?[ \t]*KGaA|GmbH[ \t]*&[ \t]*Co\.?[ \t]*KG|GmbH|gmbh"
    r"|mbH|KGaA|KG|OHG|AG|ag|SE|se|e\.[ \t]?V\.)\b"
)
AKTENZEICHEN = re.compile(
    r"\b(?:VK\s*\d{0,2}\s*[-–/]?\s*\d{1,3}\s*/\s*\d{2}"
    r"|\d{1,2}\s*Verg\s*\d{1,3}\s*/\s*\d{2})\b", re.IGNORECASE)


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html))


def namensquote(text: str) -> dict:
    """Steht bei den Verfahrensrollen eine Firmierung - oder nur die Rolle?"""
    treffer: dict[str, dict] = {}
    for m in ROLLEN_RE.finditer(text):
        rolle = m.group(1).lower()
        eintrag = treffer.setdefault(rolle, {"nennungen": 0, "mit_firma": 0})
        eintrag["nennungen"] += 1
        # Fenster um die Rollennennung: Firmierungen stehen im Rubrum direkt
        # daneben, nicht drei Seiten spaeter.
        fenster = text[max(0, m.start() - 260): m.start() + 260]
        if FIRMA.search(fenster):
            eintrag["mit_firma"] += 1
    ges = sum(v["nennungen"] for v in treffer.values())
    ben = sum(v["mit_firma"] for v in treffer.values())
    return {
        "rollen": treffer,
        "rollennennungen": ges,
        "davon_mit_firmierung": ben,
        "quote": round(ben / ges, 3) if ges else 0.0,
        "aktenzeichen": len(set(AKTENZEICHEN.findall(text))),
    }


# --- Erreichbarkeit ------------------------------------------------------------
def probe(url: str) -> dict:
    if not url:
        return {"status": "", "typ": "", "bytes": 0, "befund": "keine URL hinterlegt"}
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return {"status": 0, "typ": "", "bytes": 0,
                "befund": f"nicht erreichbar: {type(exc).__name__}"}

    typ = (r.headers.get("content-type") or "").split(";")[0].strip()
    n = len(r.content)
    if r.status_code == 403:
        befund = ("HTTP 403 - Server blockt HTTP-Clients. Browser noetig "
                  "(Playwright/Apify), kein Proxy-Problem.")
    elif r.status_code == 404:
        befund = "HTTP 404 - Pfad veraltet, Einstieg neu bestimmen"
    elif r.status_code != 200:
        befund = f"HTTP {r.status_code}"
    elif n < 2000:
        befund = "erreichbar, aber verdaechtig wenig Inhalt"
    else:
        befund = "erreichbar"
    return {"status": r.status_code, "typ": typ, "bytes": n, "befund": befund,
            "text": strip_html(r.text) if "html" in typ else ""}


def entscheidungslinks(html: str, basis: str) -> list[str]:
    """Links, die nach einzelnen Entscheidungen aussehen."""
    out = []
    for href in re.findall(r'href="([^"]+)"', html):
        u = href.replace("&amp;", "&")
        if AKTENZEICHEN.search(u) or u.lower().endswith(".pdf"):
            if u.startswith("/"):
                u = basis.rstrip("/") + u
            if u.startswith("http"):
                out.append(u)
    return list(dict.fromkeys(out))


def main() -> int:
    ap = argparse.ArgumentParser(prog="vk-quellenaudit")
    ap.add_argument("--stichprobe", type=int, default=10,
                    help="Entscheidungen je Quelle fuer die Namensquote")
    a = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    zeilen = []
    print(f"{'Kammer':<36}{'Verf.':>7}  {'HTTP':>5}  {'Bytes':>9}  Befund")
    print("-" * 104)

    for q in QUELLEN:
        haupt = probe(q["url"])
        such = probe(q["such_url"]) if q["such_url"] else {}

        # Der Such-Endpunkt ist der, auf den es ankommt - wenn er blockt,
        # ist die Quelle ohne Browser nicht nutzbar, auch wenn die
        # Startseite antwortet.
        entscheidend = such if q["such_url"] else haupt
        links = entscheidungslinks(haupt.get("text", ""), q["url"]) if haupt.get("text") else []

        # Namensquote nur messen, wo wir wirklich an Text kommen.
        quote = {"quote": "", "rollennennungen": 0, "davon_mit_firmierung": 0,
                 "aktenzeichen": 0}
        geprueft = 0
        for u in links[: a.stichprobe]:
            d = probe(u)
            if not d.get("text"):
                continue
            geprueft += 1
            m = namensquote(d["text"])
            quote["rollennennungen"] += m["rollennennungen"]
            quote["davon_mit_firmierung"] += m["davon_mit_firmierung"]
            quote["aktenzeichen"] += m["aktenzeichen"]
        if quote["rollennennungen"]:
            quote["quote"] = round(
                quote["davon_mit_firmierung"] / quote["rollennennungen"], 3)

        urteil = _urteil(entscheidend, links, quote, geprueft)
        print(f"{q['kammer'][:35]:<36}{q['verfahren_12m']:>7}  "
              f"{str(entscheidend.get('status','-')):>5}  "
              f"{entscheidend.get('bytes',0):>9}  {entscheidend.get('befund','')[:52]}")

        zeilen.append({
            "kammer": q["kammer"],
            "verfahren_12m": q["verfahren_12m"],
            "url": q["url"],
            "such_url": q["such_url"],
            "http_start": haupt.get("status", ""),
            "http_suche": such.get("status", ""),
            "bytes": entscheidend.get("bytes", 0),
            "content_type": entscheidend.get("typ", ""),
            "entscheidungslinks_gefunden": len(links),
            "entscheidungen_geprueft": geprueft,
            "rollennennungen": quote["rollennennungen"],
            "davon_mit_firmierung": quote["davon_mit_firmierung"],
            "namensquote": quote["quote"],
            "aktenzeichen_erkannt": quote["aktenzeichen"],
            "befund": entscheidend.get("befund", ""),
            "urteil": urteil,
        })

    pfad = DATA / "vk_quellenaudit.csv"
    with pfad.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0]), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(zeilen)

    print("-" * 104)
    print(f"\n{pfad}: {len(zeilen)} Quellen geprueft\n")

    browser = [z for z in zeilen if z["urteil"] == "browser_noetig"]
    offen = [z for z in zeilen if z["urteil"] == "einstieg_unklar"]
    messbar = [z for z in zeilen if isinstance(z["namensquote"], float)]

    if browser:
        vol = sum(z["verfahren_12m"] for z in browser)
        print(f"  {len(browser)} Quelle(n) brauchen einen Browser "
              f"({vol} Verfahren/Jahr dahinter):")
        for z in browser:
            print(f"    - {z['kammer']}")
        print("    -> Playwright im Runner oder Apify. Das ist das erste")
        print("       belastbare Argument fuer Apify in diesem Projekt.")
    if offen:
        print(f"\n  {len(offen)} Quelle(n) ohne erkennbaren Einstieg - Pfad "
              f"von Hand bestimmen, dann erneut messen.")
    if not messbar:
        print("\n  NAMENSQUOTE NICHT MESSBAR. Ohne sie wird der Adapter NICHT")
        print("  gebaut - ob die Antragstellerin namentlich im Text steht,")
        print("  entscheidet ueber die gesamte Quelle. Naechster Schritt:")
        print("  20 Entscheidungen von Hand ziehen und durch namensquote()")
        print("  schicken.")
        return 1

    schnitt = sum(z["namensquote"] for z in messbar) / len(messbar)
    print(f"\n  Namensquote im Schnitt: {schnitt:.0%} "
          f"(Schwelle {MIN_NAMENSQUOTE:.0%})")
    return 0 if schnitt >= MIN_NAMENSQUOTE else 1


def _urteil(p: dict, links: list, quote: dict, geprueft: int) -> str:
    if p.get("status") == 403:
        return "browser_noetig"
    if p.get("status") in (0, 404) or not p.get("status"):
        return "einstieg_unklar"
    if not links:
        return "einstieg_unklar"
    if not geprueft:
        return "text_nicht_lesbar"
    if isinstance(quote["quote"], float) and quote["quote"] < MIN_NAMENSQUOTE:
        return "zu_stark_anonymisiert"
    return "brauchbar"


if __name__ == "__main__":
    sys.exit(main())
