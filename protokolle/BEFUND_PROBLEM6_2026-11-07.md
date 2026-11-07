# Befund Problem 6 — Lichtfarbe über die Zeit, 07.11.2026

**Auftrag:** Punkt 6 des Plans lautete „Lichtfarbe: Aussehensprüfung (S > 40) auf heutiges Licht geeicht; nur
Helligkeitssprünge werden erkannt; Kontrolle über die Zeit fehlt."

**Ergebnis in einem Satz:** Das Licht ist stabil — die Sorge vor dem Weglaufen der Eichung ist für die
gemessenen 25 Stunden unbegründet. Dafür ist die Schwelle selbst falsch gewählt: in keinem einzigen der
160 Sätze ist 40 die beste Schwelle, und das kostet rund ein Viertel der Trennkraft.

## Wie gemessen wurde (jetson_lichtfarbe_1.1.py, 160 Sätze vom 06.11. 10:31 bis 07.11. 11:17)

Wo ein Tier ist, sagt **nicht** die Farbregel — das wäre ein Zirkelschluss —, sondern der Beobachter mit
seinen Rahmen. Gemessen wird dann die Farbe:

- **Tier:** Punkte im mittleren Drittel jedes bewegten Rahmens
- **Hintergrund:** Punkte außerhalb aller um 20 px verbreiterten Rahmen
- beides nur im Helligkeitsfenster der Regel (40 < V < 235), denn über alles andere entscheidet sie nie

Die erste Fassung (1.0) maß ohne dieses Fenster und bekam deshalb in jedem Satz einen Hintergrund mit
Sättigung 255 im 99. Hundertstel — gemessen wurde dunkler Aufdruck und ausgebrannte Stellen, über die die
Regel gar nicht urteilt. Der Fehler fiel auf, weil das Ergebnis in **jedem** Satz gleich unsinnig war.

## Ergebnis

| Größe | Median | Spanne |
|---|---|---|
| Trefferfläche bei S > 40 (Anteil der Tierpunkte) | 35,7 % | 0,3 … 71,9 % |
| Fehlfläche bei S > 40 (Anteil der Hintergrundpunkte) | 0,94 % | 0,68 … 2,35 % |
| Hintergrund-Sättigung, 99,9. Hundertstel | 137 | 133 … 142 |
| Helligkeit des Hintergrunds | 163 | 156 … 176 |
| Blau/Rot des Hintergrunds | 0,990 | 0,980 … 0,996 |
| beste Schwelle je Satz | 20 | 20 … 30 |

**Zur Stabilität (die eigentliche Frage von Punkt 6):** Blau zu Rot schwankt über 25 Stunden um 1,6 %, die
Hintergrund-Sättigung bleibt zwischen 133 und 142. Es gab in diesem Zeitraum keinen Lampenwechsel und keine
Farbdrift. Die Helligkeit schwankt um 12 % — das ist der einzige Wert, der sich bewegt, und genau den
überwacht die Auswahl heute schon.

**Zur Schwelle:** In **0 von 160** Sätzen ist 40 die beste Schwelle. Die beste liegt durchweg bei 20 bis 30.
Die Trennkraft (Trefferfläche minus Fehlfläche) steht bei 40 im Median bei 34,9 %, bei der jeweils besten
Schwelle bei 60,7 % — die feste 40 kostet 25,8 Punkte.

21 der 160 Sätze fallen auf weniger als die Hälfte der üblichen Trennkraft, die schlechtesten auf 1,8 bis
4,3 % Trefferfläche. Sie liegen gehäuft am 06.11. zwischen 15:41 und 15:58.

## Was das bedeutet — und was nicht

Eine größere Trefferfläche ist **nicht** von selbst besser: die Farbregel arbeitet nach der Schwelle noch
mit Öffnen, Schließen, Gruppieren und einem Flächenfenster (150 bis 6000 px). Ob eine niedrigere Schwelle
wirklich mehr Tiere findet, entscheidet erst die Messung an seinen Rahmen. Diese Messung läuft als
`jetson_farbschwelle_1.0.py`; ihr Ergebnis steht in `BEFUND_PROBLEM9_2026-11-07.md`.

**Nicht getan:** Die Schwelle in `tiere_nach_farbe_1.6.py` wurde nicht angefasst. Sie ist der Bezugspunkt
aller bisherigen Messungen; eine Änderung macht alte und neue Zahlen unvergleichbar und braucht sein Wort.

## Offen geblieben
Die Messung deckt 25 Stunden ab (so weit reichen die Videos im Lernarchiv zurück). Für eine Aussage über
Wochen muss sie regelmäßig laufen — dafür ist sie gebaut: ein Aufruf, eine Tabelle, eine Kennzahl.

## Gemessen mit
`jetson_lichtfarbe_1.1.py`; Zahlen in `befund_problem6_2026-11-07.json`.
