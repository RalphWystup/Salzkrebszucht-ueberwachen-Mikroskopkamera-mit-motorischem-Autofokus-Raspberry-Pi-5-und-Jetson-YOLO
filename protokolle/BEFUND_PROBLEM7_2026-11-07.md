# Befund Problem 7 — zwei Tiere dicht beieinander, 07.11.2026

**Auftrag:** Punkt 7 des Plans lautete „Zwei Tiere näher als 50 px (0,7 % der Bilder) verschmelzen, Nummern
können tauschen — nicht gemessen."

**Ergebnis in einem Satz:** Beides tritt praktisch nicht auf. Die angenommenen 0,7 % sind in Wirklichkeit
0,006 %, und was wie eine Verschmelzung zweier Tiere aussieht, ist beim Hinsehen meist ein einziges Tier,
das die Farbregel in Rumpf und Schwanz zerlegt.

## A. Zwei getrennt verfolgte Tiere (jetson_nummernwechsel_1.1.py, 1077 Sätze, 191 214 Bilder)

| Abstand | Bilder | Anteil |
|---|---|---|
| näher als 30 px | 0 | 0,000 % |
| näher als 50 px | 12 | 0,006 % |
| näher als 80 px | 91 | 0,048 % |

Begegnungen unter 50 px: 7 Stück. Alle dauerten nur 1 bis 4 Bilder — zu kurz, um aus Körperlänge vor und
nach der Begegnung auf einen Nummerntausch zu schließen. Ein Verlust einer Nummer trat in keiner auf.

**Damit ist die Sorge „Nummern tauschen" für diese Tierdichte gegenstandslos.** Die Tiere sind zu selten
und zu weit auseinander. Das deckt sich mit der laufenden Verfolgungsprüfung (0,3 % Nummernwechsel).

## B. Verschmelzung — das war die eigentliche Frage

Teil A kann naturgemäß nichts über Tiere sagen, die zu **einem** Rahmen verschmelzen: dann sieht der
Verfolger nur ein Objekt, und ein Abstand zwischen zwei Nummern entsteht gar nicht erst. Gemessen wurde das
darum über den unabhängigen Weg, die Farbwahrheit:

| Rahmen des Beobachters (bewegte Tiere) | 89 189 |
|---|---|
| mit genau einem Farbgebiet | 80 043 = 89,75 % |
| mit zwei oder mehr Farbgebieten | 968 = 1,09 % |
| mit keinem Farbgebiet | 8 178 = 9,17 % |

Abstand der beiden Gebiete: Median 76 px, Viertel 59 bis 102, Spanne 30 bis 173. Alle über 30 px — nach der
Rechnung also „zwei getrennte Objekte".

## C. Die 1,09 % angesehen (MONTAGE_VERSCHMELZUNG_2026-11-07.jpg, 12 Fälle, 3-fach vergrößert)

Die Rechnung allein hätte hier in die Irre geführt. Im Bild zeigt sich:

- **9 von 12 Kacheln: ein einziges Tier.** Der dunkelbraune Rumpf bildet ein Gebiet, ein Stück des blassen
  Schwanzes ein zweites; dazwischen ist der Schwanz zu hell für die Farbregel, und 15 px Gruppierungsabstand
  reichen nicht, um beide zusammenzulegen. Dazu passt das Flächenverhältnis: durchweg ein großes Gebiet
  (485–1413 px) und ein kleines (162–410 px).
- **3 von 12 Kacheln: tatsächlich ein zweites Objekt** im Rahmen — ein dunkles Korn, bzw. zwei helle runde
  Körper (Blasen oder Zysten).

Hochgerechnet liegt die echte Verschmelzung zweier Tiere damit bei grob einem Viertel von 1,09 %, also bei
etwa 0,3 % der Rahmen. Das ist eine Stichprobe von 12 aus 1085 und kein genauer Wert; für eine Zahl mit
Nachkommastelle müssten mehr Kacheln angesehen werden.

## D. Was dabei nebenbei herauskam

1. **Die Farbregel zerlegt Tiere.** Das betrifft nicht nur diese Zählung, sondern auch die Länge: wer die
   Körperlänge aus einem Farbgebiet nimmt, misst bei einem zerlegten Tier nur den Rumpf. Sein Längenmaß
   („Rumpf + Schwanz", Wort vom 06.11.) kommt aus dem Rahmen des Beobachters und ist davon nicht betroffen.
2. **9,17 % der Rahmen enthalten gar kein Farbgebiet.** Das ist die Gegenrichtung von Problem 9 und passt zu
   dessen Befund (siehe `BEFUND_PROBLEM9_2026-11-07.md`): blasse Tiere fallen unter die Sättigungsschwelle.

## Gemessen mit
`jetson_nummernwechsel_1.0.py` (Teil A), `jetson_nummernwechsel_1.1.py` (A und B),
`jetson_verschmelzung_montage_1.0.py` (Montage). Zahlen in `befund_problem7_2026-11-07.json`.
