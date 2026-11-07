# Lernseite: Befund und Behebung, 07.11.2026

**Seine Meldung:** „die lernen Seite arbeitet nicht, man kann keine Bilder weiterschalten etc."
**Seine Vorgaben dazu:** „Bitte alles mit Knopftest prüfen vor Auslieferung!" und „prüfe bitte auf
Instabilitäten und versuche diese dann zu beseitigen."

**Ergebnis:** Der Fehler ist nachgestellt, erklärt und behoben. Fassung 1.6 läuft seit 11:38 auf dem Jetson
und besteht 16 von 16 Knopfproben und 4 von 4 Instabilitätsproben — geprüft an der Seite, die der Jetson
**wirklich ausliefert** (zurückgeholt und im Browser durchgespielt), nicht an meiner Arbeitskopie.

## Die Ursache

Die Auswahl „Zeige" stand fest auf **„nur offene"**. Offene Bilder gibt es seit der ersten Bewertungsrunde
keine mehr: von 301 Lernbildern sind 52 geprüft, 243 zurückgestellt, 6 verworfen, **0 offen**. Damit

- blieb die Liste rechts leer,
- zeigte die Leinwand trotzdem ein Bild (das erste der Gesamtliste, ein bereits geprüftes),
- und jeder Weiterknopf meldete „Keine weiteren Bilder in dieser Auswahl."

Die Seite sah tot aus, obwohl Dienst, Liste, Bilder und Speichern einwandfrei arbeiteten. Dass die Auswahl
umzustellen war, stand nirgends, und die Auswahlpunkte trugen keine Zahlen.

## Knopfprobe an der alten Fassung 1.5 (pruefe_lernseite_knopf_1.1.js)

| | |
|---|---|
| bestanden | 11 von 16 |
| K0 Start: Liste gefüllt | **nein** — Filter „offen", 0 Einträge |
| K1 „nur blättern" schaltet weiter | **nein** — meldet „Keine weiteren Bilder" |
| K5 „zurück" bleibt in der Auswahl | **nein** — springt aus der Auswahl heraus, kein Eintrag aktiv |
| K12 Auswahl zeigt ihre Zahlen | **nein** |
| K14 Platzanzeige | **nein** — gibt es nicht |

## Instabilitätsprobe an 1.5 (pruefe_lernseite_stabil_1.0.js)

| Fall | 1.5 |
|---|---|
| Bild kommt nicht an | **nein** — das vorige Bild bleibt stehen, Speichern bleibt möglich. Wer dann bewertet, zeichnet Rahmen auf das falsche Bild und speichert sie unter dem neuen Namen. |
| Dreifachklick auf Speichern | **nein** — drei Speichervorgänge |
| Liste kommt nicht an | **nein** — die Seite schweigt, kein Hinweis, kein Wiederholknopf |
| Umschalten während des Ladens | ja (die Probe ist hier allerdings schwach, siehe unten) |

## Was 1.6 ändert

1. **Anfangszustand.** Beim Laden wird die Auswahl selbst auf die erste gestellt, in der Bilder stehen
   (offen → zurückgestellt → geprüft → verworfen). Jeder Auswahlpunkt trägt seine Anzahl
   („nur offene (0) · zurückgestellte (240) · alle (301) · geprüfte (54) · verworfene (7)"), leere Punkte
   sind gesperrt. Eine neue Anzeige nennt den Platz: „Bild 3 von 240 in dieser Auswahl".
2. **Blättern bleibt in der Auswahl.** „zurück" geht auf das vorige Bild **derselben** Auswahl. Am Ende der
   Auswahl wird wieder von vorn begonnen und das auch angesagt, statt stumm stehen zu bleiben.
3. **Gesperrte Knöpfe sagen warum** (Mausüberfahrt), statt wirkungslos zu sein.
4. **Tastatur bleibt wirksam.** Bisher behielt ein angeklickter Knopf den Eingabefokus, und die
   Tastaturbedienung (Eingabe, Pfeile, V, R, 1/2/3) war ab dem ersten Klick tot. Jetzt gibt jeder Knopf den
   Fokus nach dem Klick frei.
5. **Bildabriss sperrt das Bewerten.** Kommt ein Lernbild nicht an, wird die Leinwand geleert, der Grund
   steht darauf, und Speichern ist gesperrt, bis ein Bild wirklich da ist.
6. **Doppelklicksperre.** Während eines Speichervorgangs sind die Knöpfe gesperrt; drei schnelle Klicks
   lösen genau einen Speichervorgang aus.
7. **Abrisse werden gemeldet.** Fällt die Liste oder ein Rahmensatz aus, erscheint der Grund und ein
   Wiederholknopf, statt dass die Seite schweigt.
8. **Wettlauf abgefangen.** Wird während des Ladens etwas anderes geöffnet oder die Auswahl umgestellt,
   gilt nur das Letzte; eine verspätete Antwort überschreibt die Anzeige nicht mehr.
9. **„Fertig" bietet das gezeigte Bild an**, wenn es noch nicht beurteilt ist **oder** Rahmen verändert
   wurden. 1.5 fragte nur bei Status „offen" — und den gibt es nicht mehr, also ging die Arbeit am gerade
   gezeigten Bild beim Fertigdrücken verloren.

## Prüfung der neuen Fassung

| Probe | 1.5 | 1.6 | 1.6 wie vom Jetson ausgeliefert |
|---|---|---|---|
| Knopfprobe (16 Punkte) | 11 | 16 | **16** |
| Instabilitätsprobe (4 Fälle) | 1 | 4 | — |

Beide Proben laufen im echten Browser (Chromium über Playwright) gegen die echten Daten: die Liste mit
301 Einträgen vom Jetson, zwei echte Lernbilder und ihre Rahmen. Der Jetson selbst wird dabei nicht
angefasst; Speichern und „Fertig" gehen an einen Stellvertreter, der den Serverzustand mitführt.

## Rückfall
Die alte Seite liegt auf dem Jetson als `lernen_vorher.html`. Zurück in einem Befehl:
```
cp ~/mikroskop/lernen_vorher.html ~/mikroskop/lernen.html
```
Der Dienst liest die Datei bei jedem Aufruf — kein Neustart, keine Unterbrechung laufender Bewertungen.

## Was bewusst nicht geändert wurde

- **Kein „Zurückstellen"-Knopf.** Wer unsicher ist, kann heute nur „Rahmen stimmen" oder „unbrauchbar"
  wählen; der Stand „zurückgestellt" lässt sich über die Seite nicht setzen, weil der Dienst beim Speichern
  nur offen/geprüft/verworfen annimmt. Die 243 zurückgestellten Bilder stammen aus einem Skript. Das ist
  eine Lücke, aber keine Instabilität — die Behebung braucht eine Änderung am Dienst und sein Wort.
- **Die Probe „Umschalten während des Ladens" ist schwach.** Der Stellvertreter liefert für jeden Namen
  dieselben Rahmen, darum fällt ein vertauschter Satz nicht auf. Die Behebung (Punkt 8) ist trotzdem
  eingebaut; die Probe belegt sie nicht.

## Dateien
`lernen_1.6.html` (Seite), `auftrag_lernseite_16_1.0.py` (Einsatz mit Rückfallkopie),
`pruefmittel/pruefe_lernseite_knopf_1.1.js`, `pruefmittel/pruefe_lernseite_stabil_1.0.js`,
`medien/lernen_liste_2026-11-07.json` und zwei echte Lernbilder als Prüfdaten.
