# Sechs Fehler, die jeder erfolgreich aussah

Diese Liste steht nicht aus Koketterie hier. Jeder dieser Fehler hat den
Selbsttest bestanden, den man normalerweise dagegen laufen lässt — ein
HTTP-200, ein erfolgreicher Lauf, eine plausible Zahl. Entdeckt wurden sie
alle erst, als ich das Ergebnis gegen etwas Unabhängiges gehalten habe.

1. **Beleg-URL erfunden.** `/ui/de/notice/<ocid>` ist eine SPA: HTTP 200 auf
   *jede* URL, 404 erst im Browser. Ein Statuscheck hätte ihn *bestätigt*.
2. **Das wertvollste Signal feuerte nie.** `rahmenvertrag_laeuft_aus` las
   `awards[].contractPeriod` — 0 Treffer. Es hängt am Los: 15.716.
3. **TED schnitt stumm ab.** 2.000 von 2.435 Notices, Lauf meldete Erfolg.
   Jetzt Abgleich gegen `totalNoticeCount`.
4. **Trefferquote ohne Stichprobenangabe ist wertlos.** Domain-Resolution maß
   77 % — an bekannten Marken. Im Longtail 8 von 12 falsch.
5. **Das Delta log dauerhaft.** 25 Zeilen galten in *jedem* Lauf als
   „geändert". Hier stand dazu „echte Korrekturen im Überlappungsfenster" — die
   Erklärung, die zur Zahl passte. Widerlegt von vier identischen Läufen.
6. **Den Waterfall von oben gebaut.** Apollo und Clay für die Domains geplant,
   ohne zu prüfen, ob die Quelle sie selbst führt. Sie führt sie — bei drei
   Vierteln der Firmen, kostenlos, neben dem Beleg.

## Was die sechs gemeinsam haben

In fünf von sechs Fällen war die Prüfung, die ich *hatte*, nicht die Prüfung,
die den Fehler gefunden hätte:

| Fehler | Meine Prüfung sagte | Gefunden hat es |
|---|---|---|
| Beleg-URL | HTTP 200 | Content-Type und Antwortlänge |
| Rahmenvertrag | Lauf ohne Fehler | Die Frage, warum ein Typ nie feuert |
| TED-Abbruch | 2.000 Zeilen geladen | Abgleich gegen `totalNoticeCount` |
| Domain-Quote | 77 % an 13 Firmen | Dieselbe Messung im Longtail |
| Delta-Flattern | 6 Änderungen, plausibel | Vier statt zwei Läufe hintereinander |
| Waterfall | Stufe 1 lieferte Treffer | Die Frage, was Stufe 0 wäre |

Daraus folgt die Regel, nach der das Repo gebaut ist: **Jeder Lauf meldet, was
NICHT passiert ist** — welcher Signaltyp nicht gefeuert hat, wie viele Zeilen
unter der Schwelle blieben, wie viele Belege nicht prüfbar waren. Eine Null,
die man sieht, ist ein Befund. Eine Null, die man nicht sieht, sieht aus wie
„diese Woche kein Anlass".
