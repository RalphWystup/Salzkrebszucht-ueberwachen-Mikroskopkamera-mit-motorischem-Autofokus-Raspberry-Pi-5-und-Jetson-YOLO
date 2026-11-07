# Befund Problem 9 — blinde Flecken der Farbprüfung, 07.11.2026

**Auftrag:** Punkt 9 des Plans lautete „Farbprüfung hat blinde Flecken (ortsfeste braune Körner, dunkler
Druck, Rand) — Prüfwerkzeug, kein Beweis; sein Auge an den Ausschnitten."
Dazu sein Auftrag vom selben Tag, abstract64.pdf (Wang & De Baets 2019, Gent) auf Tauglichkeit zu prüfen.
Gent misst gegen von Hand gezählte Bilder und erreicht 99,6 % — dasselbe ist hier gemessen worden.

**Ergebnis in einem Satz:** Der blinde Fleck ist vermessen und sein Ursprung benannt. Es ist **nicht** die
Sättigungsschwelle (die kostet 1,2 %), sondern zu gleichen Teilen die Ortsfest-Maske über dem schwarzen
Aufdruck (7,5 %) und das Flächenfenster (8,1 %).

## 1. Grundlage: seine Hand als Wahrheit

Die 52 von ihm geprüften Lernbilder tragen 236 Rahmen: 209 Tier, 14 Korn, 13 Maßstab.

| Herkunft der Rahmen | Anzahl |
|---|---|
| Vorschlag der Farbregel | 104 |
| Vorschlag der Auswertung | 87 |
| **von Hand nachgetragen** | **45** |

Die 45 von Hand nachgetragenen Rahmen sind die eigentliche Antwort auf Punkt 9: Objekte, die **beide**
Maschinen übersehen haben. Von 209 Tier-Rahmen sind 43 von Hand — **jedes fünfte Tier sieht keine der
beiden Maschinen.**

## 2. YOLO gegen seine Rahmen (jetson_zaehlgenauigkeit_1.1.py)

| Sicherheitsschwelle | Prüfteil Treffer | Prüfteil Genauigkeit | Lernteil Treffer |
|---|---|---|---|
| 0,10 | 62,5 % | 53,2 % | 77,5 % |
| 0,25 | 37,5 % | 71,4 % | 32,5 % |
| **0,40 (der Livedienst)** | **10,0 %** | 80,0 % | 13,0 % |

**Das ist ein Befund mit sofortiger Folge:** Der Livedienst `jetson_yolo_live_1.3.py` arbeitet mit
Schwelle 0,40 und findet damit etwa jedes zehnte Tier. Auf 0,25 gesenkt fände er rund dreimal so viele bei
71 % Genauigkeit. Das erklärt auch die niedrigen Livezahlen (0,04 bis 0,10 Tiere je Bild über 18 Stunden).

Dass die Trefferquote auch auf dem **Lernteil** nur 77,5 % erreicht und bei 0,40 auf 13 % fällt, heißt:
das Modell hat gelernt, ist aber sehr unsicher. Gent nutzte 250 Lernbilder, hier sind es 52. Die Klassen
Korn (14 Beispiele) und Maßstab (12) hat das Modell gar nicht gelernt — null Funde bei jeder Schwelle.

Eine erste Messung mit nur Schwelle 0,40 hätte zum falschen Schluss „das Modell findet nichts" geführt.
Erst die Reihe über drei Schwellen trennt „findet nichts" von „ist unsicher".

## 3. Farbregel gegen seine Rahmen

| | |
|---|---|
| Wahrheit (Tier) | 209 |
| Funde | 104 |
| Treffer | 93 |
| Trefferquote | 44,5 % |
| Genauigkeit | 89,4 % |
| **auf den 43 von Hand nachgetragenen Rahmen** | **1 von 43 = 2,3 %** |

Die 44,5 % sind geschönt: die Farbregel hat 104 der Vorschläge selbst geliefert. Aussagekräftig ist die
letzte Zeile — auf den Tieren, die sie zuvor übersehen hatte, findet sie auch jetzt praktisch keines.

*Hinweis zur Messung:* Eine frühere Fassung rechnete die Farbregel auf dem Lernbild neu. Zu keinem der
52 Bilder gibt es noch ein Video, also fehlte die Ortsfest-Maske, und gemessen wurde eine Regel, die so nie
gelaufen ist (230 Funde, 26 Treffer). Die Zahlen oben stammen aus der **aufgezeichneten** Farbwahrheit
`<satz>_farbe.jsonl` — das, was die Regel damals mit Maske wirklich gefunden hat.

## 4. Die Streitfälle angesehen (MONTAGE_STREITFAELLE_2026-11-07.jpg)

Vier Zeilen, 3-fach vergrößert:

- **YOLO verpasst (183):** durchweg echte Tiere, blass und kontrastarm, fast alle auf oder neben dem
  schwarzen Aufdruck.
- **YOLO zuviel (2):** beide sehen ebenfalls nach Tieren aus — die wenigen Fehlalarme bei 0,40 sind
  vermutlich gar keine.
- **Farbregel verpasst (116):** dasselbe Bild — blasse Tiere über dem Aufdruck.
- **Farbregel zuviel (11):** dunkle Körner, runde helle Körper (Blasen oder Zysten), Kanten des Aufdrucks.
  Genau die drei Dinge, die Punkt 9 vermutet hatte.

## 5. Die Vermutung „zu hohe Schwelle" — geprüft und verworfen

Punkt 6 hatte ergeben, dass S > 40 in keinem von 160 Sätzen die beste Schwelle ist (beste 20 bis 30). Die
Montage zeigte blasse Tiere. Die naheliegende Erklärung war also: zu hohe Schwelle. Gemessen
(jetson_farbschwelle_1.0.py, Rohmaß ohne Form, an seinen Rahmen):

| Schwelle | Tiere mit genug gesättigten Punkten | davon die von Hand nachgetragenen |
|---|---|---|
| 15 | 95,7 % | 95,3 % |
| 25 | 92,3 % | 93,0 % |
| **40 (heute)** | **84,7 %** | **69,8 %** |
| 55 | 71,8 % | 60,5 % |

Bei der heutigen Schwelle haben bereits **69,8 %** der von Hand nachgetragenen Tiere genug gesättigte
Punkte — die Regel findet aber nur 2,3 % von ihnen. **Die Schwelle ist also nicht die Hauptursache.** Der
Verlust passiert später. (Die Trefferquoten der ganzen Regel in derselben Messung sind unbrauchbar, weil
ohne Videos die Ortsfest-Maske fehlte; nur das Rohmaß zählt.)

## 6. Wo der Verlust wirklich passiert (jetson_farbfilter_1.0.py, 25 Sätze, 161 Tierrahmen)

Wahrheit hier: die Rahmen des Beobachters für bewegte Tiere (unabhängig von der Farbregel).

| Stufe | bleiben übrig | verloren an dieser Stufe |
|---|---|---|
| 0 Tierrahmen | 161 (100,0 %) | — |
| 1 Sättigung S > 40 / dunkler Kopf | 159 (98,8 %) | 2 (1,2 %) |
| 2 Ortsfest-Masken abgezogen | 147 (91,3 %) | 12 (**7,5 %**) |
| 3 Öffnen / Schließen / Gruppieren | 145 (90,1 %) | 2 (1,2 %) |
| 4 Flächenfenster 150…6000 px | 132 (82,0 %) | 13 (**8,1 %**) |

Nach Lage zum Aufdruck:

| | Rahmen | gefunden | Verlust an der Ortsfest-Maske |
|---|---|---|---|
| über dem Aufdruck | 141 | 79,4 % | 8,6 % |
| frei vom Aufdruck | 20 | **100,0 %** | 0,0 % |

**Damit ist die Ursache benannt.** Die Ortsfest-Maske löscht die dunkle Aufdruckfläche (plus 9 px Rand) —
und mit ihr die Tiere, die gerade darüber liegen. Frei vom Aufdruck findet die Regel jedes Tier.
Gleich groß ist der Verlust am Flächenfenster: Gebiete unter 150 oder über 6000 px fallen heraus.

Vorbehalt: diese Messung nimmt die Rahmen des Beobachters als Wahrheit. Für die 43 von Hand nachgetragenen
Tiere (die auch der Beobachter übersah) lässt sie sich noch nicht wiederholen, weil zu diesen Lernbildern
keine Videos mehr liegen. Dafür müssen neue Lernbilder aus Sätzen gezogen werden, die noch ein Video haben
(937 stehen bereit) — und die muss er bewerten.

## 7. Was folgt (nichts davon ist getan, alles braucht sein Wort)

| Maßnahme | erwartete Wirkung | Risiko |
|---|---|---|
| Livedienst-Schwelle von 0,40 auf 0,25 senken | rund dreimal so viele erkannte Tiere, Genauigkeit 71 statt 80 % | gering, eine Zahl, sofort umkehrbar |
| Mehr Lernbilder bewerten (243 liegen bereit) | der Weg zu Gents Größenordnung; nur so lernt das Modell Korn und Maßstab | kostet seine Zeit |
| Ortsfest-Maske nicht über bewegten Gebieten anwenden | die 7,5 % über dem Aufdruck zurück | ändert die Bezugsregel aller bisherigen Messungen |
| Flächenfenster 150…6000 px überprüfen | die 8,1 % am oberen und unteren Rand | dito |
| Gruppierungsabstand von 15 px erhöhen | Rumpf und Schwanz blieben ein Objekt (siehe Problem 7) | dito |

## 8. Zu abstract64.pdf
Die Auswertung steht seit dem 06.11. 17:08 in `LITERATUR_2026-11-06.md`, Abschnitt 4 — die heutige Meldung
„noch offen" war falsch, sie stammte aus einem Standblatt von 16:01. Neu ist, dass Gents Maßstab jetzt
gemessen ist: **99,6 % bei Gent (4671 Objekte, 250 Lernbilder) gegen 62,5 % bei uns (40 Objekte,
52 Lernbilder, Schwelle 0,10).** Der Abstand ist in erster Linie eine Frage der Menge bewerteter Bilder.

## Gemessen mit
`jetson_zaehlgenauigkeit_1.0/1.1.py`, `jetson_farbschwelle_1.0.py`, `jetson_farbfilter_1.0.py`.
Zahlen in `befund_problem9_2026-11-07.json`, `befund_farbschwelle_2026-11-07.json`,
`befund_farbfilter_2026-11-07.json`. Bilder: `MONTAGE_STREITFAELLE_2026-11-07.jpg`.
