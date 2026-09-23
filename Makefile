.PHONY: demo run export runlog reset retier

demo:            ## Offline gegen Fixtures - fuer die Live-Demo
	python3 -m src.cli run
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
