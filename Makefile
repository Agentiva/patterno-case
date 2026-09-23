.PHONY: demo run export runlog reset

demo:            ## Offline gegen Fixtures - fuer die Live-Demo
	python3 -m src.cli run
	python3 -m src.cli export

run:             ## Gegen die echten APIs
	python3 -m src.cli run --live
	python3 -m src.cli export

export:
	python3 -m src.cli export

runlog:
	python3 -m src.cli runlog

reset:           ## Delta-Store leeren (Demo von vorn)
	rm -f data/state.sqlite
