# Befund Problem 4 — ruhende und langsame Tiere, 06.11.2026 12:42

**Messung:** `jetson_filter_messen_1.0.py` auf dem Jetson, jeder 3. Satz ab 20261106_10 (245 Sätze, Rohvideos + Farbwahrheit 1.6
+ Live-Ausgabe der Auswertung 1.4), je Wahrheitstier und Bild die Stufen der Auswertung 1.4 nachgerechnet (Ausgabe
`jetson_ausgaben/jetson_filter_messen_1.0_113745.aus.txt`). MOG2 startet im Video kalt (erste 60 Bilder nicht gewertet).

| Klasse | n | Vordergrund Median | ≥ 100 | Körper dunkel Median | ≥ 60 | braun Median | ≥ 150 | bewegt | y Median | Grund |
|---|---|---|---|---|---|---|---|---|---|---|
| getroffen, heller Grund | 9499 | 829 | 92 % | 596 | 100 % | 813 | 100 % | 88 % | 240 | 165 |
| **verfehlt, heller Grund** | 2983 | **15** | **25 %** | 219 | 92 % | 389 | 95 % | 53 % | 216 | 175 |
| getroffen, dunkler Grund | 754 | 1016 | 97 % | 424 | 96 % | 631 | 100 % | 90 % | 189 | 46 |
| **verfehlt, dunkler Grund** | 466 | **0** | **23 %** | 574 | 90 % | 316 | 95 % | 52 % | 332 | 66 |

**Erste Fehlstufe der Verfehlten:** Vordergrund (MOG2-Maske) < 100 px in **75 %** (heller Grund) bzw. **77 %** (dunkler Grund);
alle Stufen erfüllt, aber nicht gemeldet (Bahn noch jung: 3 Treffer und ⅓ Aussehen nötig) 22–23 %; Körpertest 0 %, Brauntest 0–2 %.

**Deutung.** Problem 4 ist ein Problem der Bewegungsmaske, nicht des Körper- oder Brauntests: Die verfehlten Tiere stehen zu 9 von 10
im Rohbild deutlich dunkler als der MOG2-Hintergrund (Median 219–574 px, Schwelle 60) und haben genug braune Punkte (Median 316–389,
Schwelle 150), aber MOG2 meldet sie nicht mehr als Vordergrund, weil ein Tier, das 1–2 s an derselben Stelle ruht oder nur um wenige
Pixel kriecht, in das Mischmodell aufgenommen wird (Gewicht seines Modus > 10 % bei history 400). Der dunkle Aufdruck ist NICHT die
Ursache: über dunklem Grund fällt der Körpertest ebenso wenig aus wie über hellem. Die Hälfte der verfehlten Bilder bewegt sich
noch (> 5 px in 5 Bildern), aber innerhalb der eigenen Fläche, sodass nur ein schmaler Saum in der Maske bleibt.

**Abhilfe (Auswertung 1.5, erst an Rohaufnahmen prüfen):** Nachsuche für bekannte Bahnen: bekommt eine gemeldete Bahn im Bild keinen
MOG2-Kandidaten, wird im letzten Rahmen (± Tor) direkt im Rohbild nach dem Körper gesucht (dunkler als der Hintergrund ≥ 60 px und
≥ 150 braune Punkte) und die Bahn mit dieser Beobachtung fortgeführt (grauer Punkt „ruht"); damit der Hintergrund unter einem ruhenden
Tier nicht mitlernt, wird das Hintergrundbild unter bekannten Bahnen eingefroren. Die 22 % „jung" bleiben (3 Treffer sind Absicht gegen Geister).
