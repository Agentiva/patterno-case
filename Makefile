.PHONY: help demo run longlist domains clay-todo vollstaendigkeit export \
        runlog reset retier package vk-audit enrich-dry enrich-domains enrich-all

help:            ## Diese Uebersicht
	@echo "AUFGABE 1 - Der Markt"
	@echo "  make longlist          12 Monate Vergabedaten  -> data/longlist_markt.csv"
	@echo "  make domains           Domains aus der amtlichen Quelle (Waterfall Stufe 0)"
	@echo "  make clay-todo         offene Domains fuer Clay (Waterfall Stufe 2)"
	@echo "  make vollstaendigkeit  Fang-Wiederfang: wie viel deckt die Liste ab?"
	@echo
	@echo "AUFGABE 2 - Das Timing"
	@echo "  make run               Signale gegen die echten APIs"
	@echo "  make demo              dasselbe offline; 2x hintereinander = 0 neue Zeilen"
	@echo "  make vk-audit          Quellenaudit der vierten Signalquelle"
	@echo
	@echo "ABGABE"
	@echo "  make package           Enrichment-Tabellen + Stichproben-Audit"
	@echo
	@echo "BETRIEB"
	@echo "  make retier FROM=x.csv Clay-Export einspielen, Tiers nachziehen"
	@echo "  make export            CSVs neu schreiben, ohne Abruf"
	@echo "  make runlog            Laufprotokoll je Quelle"
	@echo "  make reset             Delta-Store leeren (vor der Loom-Aufnahme)"
	@echo
	@echo "ENRICHMENT ueber Apollo (braucht APOLLO_API_KEY, siehe .env.example)"
	@echo "  make enrich-dry        Credit-Kalkulation ohne Abruf"
	@echo "  make enrich-domains    Waterfall Stufe 1-3, kostenlos"
	@echo "  make enrich-all        plus Firmographics und Kontakte (kostet Credits)"

# ---------------------------------------------------------------------------
# AUFGABE 1 - Der Markt
# ---------------------------------------------------------------------------

longlist:        ## 12 Monate Vergabedaten -> longlist_markt.csv
	python3 -m src.cli longlist --live --months 12

domains:         ## Waterfall Stufe 0: Domains aus der Bekanntmachung selbst
	python3 -m src.resolve.domains
	python3 -m src.cli retier --from data/domains_amtlich.csv
	python3 -m src.cli export

clay-todo:       ## Waterfall Stufe 2: offene Zeilen fuer die KI-Recherche in Clay
	python3 -m src.export.clay_domain_todo

vollstaendigkeit: ## Fang-Wiederfang: wie viele Firmen fehlen der Liste?
	python3 -m src.longlist.completeness

# ---------------------------------------------------------------------------
# AUFGABE 2 - Das Timing
# ---------------------------------------------------------------------------

run:             ## Signale gegen die echten APIs
	python3 -m src.cli run --live
	python3 -m src.cli export

demo:            ## Offline gegen Fixtures - 2x hintereinander = 0 neue Zeilen
	python3 -m src.cli run
	python3 -m src.cli export

vk-audit:        ## Quellenaudit der vierten Signalquelle (Vergabekammer)
	python3 -m src.sources.vergabekammer_audit

# ---------------------------------------------------------------------------
# ABGABE
# ---------------------------------------------------------------------------

package:         ## Enrichment-Tabellen + Stichproben-Audit bauen
	python3 -m src.export.package

# ---------------------------------------------------------------------------
# BETRIEB
# ---------------------------------------------------------------------------

retier:          ## Angereicherte Daten einspielen und Tiers nachziehen
	@test -n "$(FROM)" || (echo "Aufruf: make retier FROM=<clay-export.csv>"; exit 1)
	python3 -m src.cli retier --from $(FROM)
	python3 -m src.cli export

export:          ## CSVs neu schreiben, ohne Abruf
	python3 -m src.cli export

runlog:          ## Laufprotokoll je Quelle
	python3 -m src.cli runlog

reset:           ## Delta-Store leeren - vor der Loom-Aufnahme noetig
	rm -f data/state.sqlite

# ---------------------------------------------------------------------------
# ENRICHMENT ueber Apollo - braucht APOLLO_API_KEY (siehe .env.example)
#
# Das ist die Implementierung der Waterfall-Stufen 1 bis 3 aus
# docs/waterfalls.md. Die abgegebenen Kontakte kamen ueber Clay; dieser
# Pfad bleibt, weil die dort genannten Trefferquoten von ihm gemessen sind.
# ---------------------------------------------------------------------------

enrich-dry:      ## Credit-Kalkulation ohne Abruf
	python3 -m src.enrich.apollo --dry-run

enrich-domains:  ## Waterfall Stufe 1-3, kostenlos
	python3 -m src.enrich.apollo --stage domains

enrich-all:      ## plus Firmographics und Kontakte (kostet Credits)
	python3 -m src.enrich.apollo --stage all
