.PHONY: demo run longlist domains vollstaendigkeit export runlog reset retier package vk-audit

demo:            ## Offline gegen Fixtures - fuer die Live-Demo
	python3 -m src.cli run
	python3 -m src.cli export

longlist:        ## Aufgabe 1: Markt-Longlist aus 12 Monaten Vergabedaten
	python3 -m src.cli longlist --live --months 12

vollstaendigkeit: ## Fang-Wiederfang: wie viele Firmen fehlen der Liste?
	python3 -m src.longlist.completeness

domains:         ## Domains aus der amtlichen Quelle ziehen und einspielen
	python3 -m src.resolve.domains
	python3 -m src.cli retier --from data/domains_amtlich.csv
	python3 -m src.cli export

run:             ## Gegen die echten APIs
	python3 -m src.cli run --live
	python3 -m src.cli export

export:
	python3 -m src.cli export

retier:          ## Angereicherte Daten einspielen und neu einstufen
	@test -n "$(FROM)" || (echo "Aufruf: make retier FROM=<clay-export.csv>"; exit 1)
	python3 -m src.cli retier --from $(FROM)
	python3 -m src.cli export

package:         ## Abgabedateien + Stichproben-Audit bauen
	python3 -m src.export.package

vk-audit:        ## Quellenaudit fuer die vierte Signalquelle (Vergabekammer)
	python3 -m src.sources.vergabekammer_audit

runlog:
	python3 -m src.cli runlog

reset:           ## Delta-Store leeren (Demo von vorn)
	rm -f data/state.sqlite

enrich-dry:      ## Credit-Kalkulation ohne Abruf
	python3 -m src.enrich.apollo --dry-run

enrich-domains:  ## Stufe 1-3, kostenlos
	python3 -m src.enrich.apollo --stage domains

enrich-all:      ## Domains + Firmographics + Kontakte (kostet Credits)
	python3 -m src.enrich.apollo --stage all
