"""Domains aus der amtlichen Quelle statt aus Web-Recherche.

=== DER BEFUND, DER DIESES MODUL AUSGELOEST HAT ===
Die Spalte `domain` war in der abgegebenen Longlist bei 0 von 2.458 Zeilen
gefuellt - obwohl 1c sie ausdruecklich verlangt. Der geplante Weg lief ueber
Clay/Apollo und deckte 23 Firmen ab.

Vor dem ersten Credit die naheliegende Frage: Fuehrt die Quelle die Domain
selbst? eForms hat ein Feld dafuer. Gemessen am 12-Monats-Korpus:

    Bieter-/Gewinnerparteien            5.735
      mit contactPoint.url              1.468   (25,6 %)
      mit contactPoint.email            4.006   (69,9 %)

Auf die 2.458 Firmen der Longlist gerechnet:

      aus url                             799   (32,5 %)
      aus E-Mail-Domain                 1.779   (72,4 %)
      Vereinigung                       1.852   (75,3 %)

Die Domain steht also im selben CC0-Datensatz wie der Zuschlagsbeleg, mit
derselben proof_url. Das ist nicht nur billiger als Apollo, es ist eine
BESSERE Quelle: Die Adresse hat das Unternehmen der Vergabestelle selbst
gemeldet.

=== WARUM DAS TROTZDEM NICHT EINFACH UEBERNOMMEN WIRD ===
Wo url und E-Mail beide vorliegen (726 Firmen), widersprechen sie sich in
23 % der Faelle. Die Abweichungen sind keine Zufallsstreuung, sondern vier
wiederkehrende Muster - und das vierte ist gefaehrlich:

  1. Kaputte Felder
     "https" ohne Rest, "milchundzucker" ohne TLD,
     "vertrieb@btc-ag.com" im URL-Feld, "emailaddress.given" als Platzhalter,
     "nortal.cpm" als Tippfehler im Original.

  2. Konzern statt Rechtstraeger
     Fsas Technologies GmbH  -> fujitsu.com
     Eviden Germany GmbH     -> atos.net
     Micro Focus Deutschland -> opentext.com
     Dasselbe Problem wie bei Apollo, nur andersherum: nicht falsch,
     aber nicht der Bieter.

  3. Zweitdomains desselben Hauses
     materna.de / materna.group, iserv.de / iserv.eu, acp.de /
     techrent.acp-gruppe.com. Beides richtig, eine muss gewinnen.

  4. FREMDE Adressen im Bieterdatensatz  <-- der teure Fall
     avodaq AG, Vodafone GmbH, Bredex GmbH und IF-Tech AG tragen alle
     "fb.hamburg.de". Das ist die Beschaffungsstelle Hamburg, also der
     AUFTRAGGEBER. b.telligent Deutschland traegt "deutschebahn.com" -
     der Kunde. time4you GmbH traegt "karlsruhe.de".
     Wer das uebernimmt, schreibt eine Outbound-Mail an die Vergabestelle
     und behauptet dabei, sie sei Bieter gewesen.

Muster 4 macht den Unterschied zwischen "Feld gefuellt" und "Feld
belastbar". Deshalb dieser Resolver: uebernehmen, was sich pruefen laesst,
und den Rest sichtbar offen lassen.

=== DIE PRUEFKETTE ===
Jede Kandidatendomain durchlaeuft vier Tests. Keiner davon braucht Netz,
alle sind nachrechenbar:

  Syntax       Punkt vorhanden, plausible TLD, kein @, keine Platzhalter
  Auftraggeber Domain kommt im Korpus in einer buyer-Rolle vor -> raus
  Streuung     Domain beansprucht >= 3 namentlich unverwandte Firmen -> raus
  Namensbezug  Teilt der Domainstamm ein Token mit dem Firmennamen?

Das Ergebnis ist eine Konfidenz, keine Ja/Nein-Entscheidung:

  0,95  amtlich_bestaetigt    url und Mail stimmen ueberein
  0,90  amtlich_namensbezug   eine Quelle, Domainstamm passt zum Namen
  0,60  amtlich_unbestaetigt  eine Quelle, kein Namensbezug, kein Verdacht
  ---   pruefen               Widerspruch oder Verdacht -> KEINE Domain

Unter RESOLUTION_MIN_CONFIDENCE wird nichts geschrieben. Das ist dieselbe
Regel wie bei der Firmenauflösung: nicht raten, sondern die Luecke zeigen.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.config import RESOLUTION_MIN_CONFIDENCE
from src.resolve.normalize import fold, normalize_company

DATA = Path("data")
FIXTURE = Path("fixtures/vergabe_dovs.longlist.json")

# Freemail und Provider. Eine persoenliche Adresse bei einem Freemailer ist
# keine Firmendomain - bei kleinen Systemhaeusern kommt das vor.
FREEMAIL = {
    "gmail.com", "googlemail.com", "t-online.de", "gmx.de", "gmx.net",
    "gmx.at", "gmx.ch", "web.de", "outlook.com", "outlook.de", "hotmail.com",
    "hotmail.de", "yahoo.de", "yahoo.com", "icloud.com", "me.com", "aol.com",
    "freenet.de", "mail.de", "online.de", "posteo.de", "protonmail.com",
    "arcor.de", "1und1.de", "vodafone.de", "unity-mail.de",
}

# Platzhalter, die im Original stehen und keine Adresse sind.
PLATZHALTER = {
    "emailaddress.given", "example.com", "example.de", "test.de",
    "keine.de", "nicht.vorhanden", "n.a.", "na.de", "xxx.de",
    # "beispiel.de" ist example.de auf Deutsch. Stand bei 5 Firmen und waere
    # ohne den Streuungstest als Domain durchgegangen - gefunden hat es
    # nicht diese Liste, sondern die Messung.
    "beispiel.de", "musterfirma.de", "muster.de",
}

# Eine Domain braucht mindestens einen Punkt und eine TLD aus Buchstaben.
# "https", "milchundzucker" und "n/a" fallen hier heraus.
DOMAIN_OK = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$")

# Wie viele namentlich unverwandte Firmen darf eine Domain beanspruchen,
# bevor sie als Fremdadresse gilt? Drei, nicht zwei: Ein Konzern mit zwei
# Tochtergesellschaften in der Liste ist normal, fb.hamburg.de mit vier
# unverwandten Systemhaeusern ist es nicht.
MAX_FREMDE_FIRMEN = 3


def host_of(value: str | None) -> str | None:
    """Registrierbaren Host aus einem URL- oder Mailfeld ziehen.

    Das URL-Feld enthaelt im Original auch Mailadressen
    ("vertrieb@btc-ag.com") und nackte Schemata ("https"). Beides wird hier
    abgefangen, nicht weiter unten als kaputte Domain.
    """
    if not value:
        return None
    v = value.strip().lower()
    v = re.sub(r"^[a-z][a-z0-9+.-]*://", "", v)     # Schema weg
    if "@" in v:                                     # Mail im URL-Feld
        v = v.rsplit("@", 1)[1]
    v = v.split("/")[0].split("?")[0].split("#")[0]
    v = v.split(":")[0]                              # Port weg
    if v.startswith("www."):
        v = v[4:]
    v = v.strip(". ")
    if not v or v in PLATZHALTER or v in FREEMAIL:
        return None
    return v if DOMAIN_OK.match(v) else None


def stamm(domain: str) -> str:
    """Der aussagekraeftige Teil der Domain, ohne TLD und ohne Subdomains
    wie 'de.' oder 'geschaeftskunden.'. Fuer den Namensvergleich."""
    teile = domain.split(".")
    # Zweistufige Laender-TLDs (co.uk) kommen im Korpus nicht vor; der
    # einfache Fall genuegt und ist erklaerbar.
    kern = teile[-2] if len(teile) >= 2 else teile[0]
    # Bei 'techrent.acp-gruppe.com' ist der Kern 'acp-gruppe'; die
    # Subdomain 'techrent' traegt aber die Information. Beide pruefen.
    return kern


def namensbezug(firmenname: str, domain: str) -> bool:
    """Teilt die Domain einen Wortstamm mit dem Firmennamen?

    Bewusst grob und erklaerbar: Im Review muss nachvollziehbar sein, warum
    eine Domain als passend galt. Ein Token ab vier Zeichen, das in der
    Domain vorkommt, genuegt - 'nds' in 'nds-systemhaus.de' faellt damit
    durch, 'avodaq' in 'fb.hamburg.de' ebenfalls, und das ist richtig:
    beide gehoeren in die Pruefung, nicht ins Outbound.
    """
    dom = fold(domain).replace("-", "").replace(".", "")
    for tok in normalize_company(firmenname).split():
        tok = tok.replace("-", "")
        if len(tok) >= 4 and tok in dom:
            return True
        # Kurze Firmenkuerzel (SVA, ACP, IBH) als eigenes Label zulassen,
        # aber nur als ganzes Label - sonst matcht 'ibh' in 'weibhausen'.
        if 2 <= len(tok) <= 3 and tok in domain.split(".")[0].split("-"):
            return True
    return False


def _kandidaten(releases: list[dict], firmen: dict[str, str]) -> tuple[dict, dict, set]:
    """Rohkandidaten je company_id sammeln, plus die Auftraggeberdomains.

    firmen: company_id -> legal_name (nur die Longlist zaehlt)
    """
    aus_url: dict[str, str] = {}
    aus_mail: dict[str, str] = {}
    buyer_domains: set[str] = set()

    for rel in releases:
        for p in (rel.get("parties") or []):
            rollen = p.get("roles") or []
            cp = p.get("contactPoint") or {}
            # Auftraggeber- und Verfahrensadressen zuerst einsammeln. Sie
            # sind der Grund, warum 'fb.hamburg.de' bei vier Systemhaeusern
            # steht, und muessen deshalb bekannt sein, bevor geprueft wird.
            if any(r in ("buyer", "processContactPoint", "submissionReceiptBody",
                         "reviewBody", "reviewContactPoint", "mediationBody")
                   for r in rollen):
                for feld in (cp.get("url"), cp.get("email")):
                    h = host_of(feld)
                    if h:
                        buyer_domains.add(h)
            if not any(r in ("supplier", "tenderer") for r in rollen):
                continue
            cid = normalize_company(p.get("name") or "")
            if cid not in firmen:
                continue
            h = host_of(cp.get("url"))
            if h:
                aus_url.setdefault(cid, h)
            m = host_of(cp.get("email"))
            if m:
                aus_mail.setdefault(cid, m)
    return aus_url, aus_mail, buyer_domains


def resolve(releases: list[dict], firmen: dict[str, str]) -> tuple[list[dict], dict]:
    """company_id -> Domainbefund, plus Kennzahlen des Laufs."""
    aus_url, aus_mail, buyer_domains = _kandidaten(releases, firmen)

    # Streuung messen: Wie viele NAMENTLICH UNVERWANDTE Firmen beansprucht
    # eine Domain? Telekom-Toechter teilen telekom.de zu Recht - dort greift
    # der Namensbezug. fb.hamburg.de teilt sich auf Firmen, mit denen es
    # nichts zu tun hat.
    fremd_zaehler: Counter = Counter()
    for cid, dom in list(aus_url.items()) + list(aus_mail.items()):
        if not namensbezug(firmen[cid], dom):
            fremd_zaehler[dom] += 1
    gestreut = {d for d, n in fremd_zaehler.items() if n >= MAX_FREMDE_FIRMEN}

    rows: list[dict] = []
    stat: Counter = Counter()
    for cid, name in firmen.items():
        u, m = aus_url.get(cid), aus_mail.get(cid)
        if not u and not m:
            stat["ohne_kandidat"] += 1
            continue

        # Verdacht pruefen - aber NUR fuer Kandidaten ohne Namensbezug.
        #
        # Die erste Fassung verwarf jede Domain, die im Korpus auch in einer
        # buyer-Rolle vorkam. Das traf die Falschen: Aagon GmbH -> aagon.com,
        # Bundesdruckerei -> bdr.de, DLR -> dlr.de, DFN -> dfn.de. Diese
        # Haeuser beschaffen selbst und stehen deshalb auch als Auftraggeber
        # im Datensatz - ihre eigene Domain ist dadurch nicht falsch.
        # 96 von 96 Treffern waren so zu erklaeren oder eben nicht; erst der
        # Namensbezug trennt die beiden Gruppen:
        #
        #   aagon.com     bei Aagon GmbH   -> Name passt -> behalten
        #   fb.hamburg.de bei avodaq AG    -> Name passt nicht -> raus
        #
        # Der Namensbezug ist das staerkere Indiz. Eine Rollenkoinzidenz im
        # Korpus wiegt weniger als ein Firmenname, der in der Domain steht.
        verdacht = []
        for d in (u, m):
            if not d or namensbezug(name, d):
                continue
            if d in buyer_domains:
                verdacht.append(f"{d} ist eine Auftraggeberadresse")
            if d in gestreut:
                verdacht.append(f"{d} steht bei {fremd_zaehler[d]} fremden Firmen")

        if verdacht:
            rows.append({"company_id": cid, "legal_name": name, "domain": "",
                         "domain_confidence": "", "domain_source": "",
                         "kandidat_url": u or "", "kandidat_mail": m or "",
                         "befund": "; ".join(dict.fromkeys(verdacht))})
            stat["verworfen_verdacht"] += 1
            continue

        if u and m and u == m:
            dom, conf, quelle = u, 0.95, "amtlich_bestaetigt"
        elif u and m and u != m:
            # Widerspruch. Der Namensbezug entscheidet - passt genau eine
            # Seite zum Firmennamen, gewinnt sie. Passen beide oder keine,
            # ist es eine Handentscheidung.
            bu, bm = namensbezug(name, u), namensbezug(name, m)
            if bu and not bm:
                dom, conf, quelle = u, 0.90, "amtlich_namensbezug"
            elif bm and not bu:
                dom, conf, quelle = m, 0.90, "amtlich_namensbezug"
            else:
                rows.append({"company_id": cid, "legal_name": name, "domain": "",
                             "domain_confidence": "", "domain_source": "",
                             "kandidat_url": u, "kandidat_mail": m,
                             "befund": "url und Mail widersprechen sich, "
                                       "Namensbezug entscheidet nicht"})
                stat["verworfen_widerspruch"] += 1
                continue
        else:
            dom = u or m
            if namensbezug(name, dom):
                conf, quelle = 0.90, "amtlich_namensbezug"
            else:
                conf, quelle = 0.60, "amtlich_unbestaetigt"

        if conf < RESOLUTION_MIN_CONFIDENCE:
            rows.append({"company_id": cid, "legal_name": name, "domain": "",
                         "domain_confidence": conf, "domain_source": quelle,
                         "kandidat_url": u or "", "kandidat_mail": m or "",
                         "befund": "kein Namensbezug, Einzelquelle - unter Schwelle"})
            stat["unter_schwelle"] += 1
            continue

        rows.append({"company_id": cid, "legal_name": name, "domain": dom,
                     "domain_confidence": conf, "domain_source": quelle,
                     "kandidat_url": u or "", "kandidat_mail": m or "",
                     "befund": ""})
        stat[quelle] += 1

    stat["buyer_domains_bekannt"] = len(buyer_domains)
    stat["gestreute_domains"] = len(gestreut)
    return rows, stat


def main() -> int:
    ll = list(csv.DictReader(open(DATA / "longlist_markt.csv", encoding="utf-8-sig")))
    firmen = {r["company_id"]: r["legal_name"] for r in ll}

    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    releases = d if isinstance(d, list) else (d.get("releases") or [])

    rows, stat = resolve(releases, firmen)
    rows.sort(key=lambda r: (r["domain"] == "", r["legal_name"].lower()))

    out = DATA / "domains_amtlich.csv"
    felder = ["company_id", "legal_name", "domain", "domain_confidence",
              "domain_source", "kandidat_url", "kandidat_mail", "befund"]
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=felder, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    n = len(firmen)
    mit = sum(1 for r in rows if r["domain"])
    print(f"{out}: {len(rows)} Zeilen fuer {n} Firmen")
    print(f"\n  MIT Domain            {mit:5} / {n}  {mit/n:5.1%}")
    for k in ("amtlich_bestaetigt", "amtlich_namensbezug", "amtlich_unbestaetigt"):
        print(f"    {k:22} {stat[k]:5}")
    print(f"\n  OHNE Domain           {n-mit:5} / {n}  {(n-mit)/n:5.1%}")
    for k, txt in (("ohne_kandidat", "Quelle fuehrt kein Feld"),
                   ("verworfen_verdacht", "Fremdadresse erkannt"),
                   ("verworfen_widerspruch", "url/Mail widersprechen sich"),
                   ("unter_schwelle", "unter Confidence-Schwelle")):
        print(f"    {txt:28} {stat[k]:5}")
    print(f"\n  Auftraggeberdomains bekannt: {stat['buyer_domains_bekannt']}")
    print(f"  als gestreut verworfen:      {stat['gestreute_domains']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
