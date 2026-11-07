# Befund Problem 1 — Rechenlast des Pi, gemessen am 07.11.2026

**Auftrag:** Punkt 1 des Plans vom 06.11.2026 lautete „Rechenlast Pi knapp (Auswertung 1,5 Kerne,
Kiosk-Firefox 1,1, Wache 0,3, Fokus 0,4, Kernfaden w1_bus_master 0,4–0,6 ohne erkennbaren Zweck)".

**Ergebnis in einem Satz:** Der Prozessor ist nicht eng. Eng ist die Speicherkarte, und fast die Hälfte
dessen, was auf sie geschrieben wird, liest kein Programm.

## 1. Was wirklich rechnet (pi_last_messen_1.0.py, 20 s, aus /proc/<pid>/stat)

| Programm | Kerne | Anteil eines Kerns |
|---|---|---|
| `auswertung_1.4.py` | 0,74 | 74 % |
| `autofokus4.py` | 0,39 | 39 % |
| Kiosk-Firefox (3 Prozesse) | 0,54 | 54 % |
| `wache_pi_1.6.py` | 0,25 | 25 % |
| `w1_bus_master1` (Kernfaden) | 0,11 | 11 % |
| übrige (kworker, wayfire) | 0,09 | 9 % |
| **Summe** | **2,12 von 4** | **53 %** |

Die Zahlen des Plans waren rund doppelt so hoch. Sie stammten aus einer Momentanzeige, nicht aus einem
Zeitfenster. Temperatur 53 °C, `throttled=0x0` — der Pi drosselt nicht.

## 2. Warum das Lastmittel trotzdem bei 4,3 bis 5,1 steht (pi_warten_messen_1.0.py, 40 Stichproben)

| Zustand | Mittel | höchstens |
|---|---|---|
| rechnend (R) | 2,35 | 5 |
| wartend (D, ununterbrechbar) | 2,20 | 5 |
| Summe (das ist das Lastmittel) | 4,55 | |

Die wartende Hälfte sind ausschließlich Kernfäden des Rückschreibens: `kworker/u17:0+flush-179:0` (30 %
der Stichproben), `jbd2/mmcblk0p2-8` (ext4-Tagebuch, 17,5 %), `systemd-journald` (27,5 %). Gerät 179 ist
die Speicherkarte. Im Fenster von 20 s: 34,6 MB geschrieben, und **9,0 s lang (44 % der Zeit) standen
Aufträge in der Warteschlange der Karte**.

Das Lastmittel ist hier also keine Aussage über den Prozessor. `/proc/pressure` gibt es auf diesem Kern
nicht, darum die Zustandszählung.

## 3. Wer schreibt (pi_schreiber_messen_1.0.py, 32 s, aus /proc/<pid>/io, über sudo auch fremde Prozesse)

| Programm | MB/s | je Tag |
|---|---|---|
| `auswertung_1.4.py` | 0,517 | 45 GB |
| `systemd-journald` | 0,009 | 0,8 GB |
| `wache_pi_1.6.py` | 0,003 | 0,3 GB |
| **Summe** | **0,54** | **47 GB** |

## 4. Was geschrieben wird (48 Sätze in /home/pi/wache/aufnahmen)

| Art | Dateien | MB | Anteil | je Satz |
|---|---|---|---|---|
| `_rahmen.avi` (Video mit eingezeichneten Rahmen) | 57 | 396,6 | 48,2 % | 8,26 MB |
| `.avi` (Rohvideo) | 57 | 393,1 | 47,8 % | 8,19 MB |
| `_tafel.jpg` | 49 | 28,5 | 3,5 % | 0,59 MB |
| `_ausschnitte.jpg` | 48 | 2,8 | 0,3 % | 0,06 MB |
| `.jsonl` (die Messdaten) | 48 | 1,1 | 0,1 % | 0,02 MB |
| **gesamt** | **259** | **822,1** | | **17,13 MB** |

**Der Kern des Befunds:** `_rahmen.avi` ist die Hälfte der Schreiblast und des rsync-Verkehrs zum Jetson.
Gelesen wird die Datei von keinem Auswertungsprogramm — Farbwahrheit, Lernbilder, Vermessung und alle
Messungen dieses Tages arbeiten am Rohvideo `.avi`. Sie wird einzig von `hole_aufnahme_2.4.py` geholt,
wenn jemand sich eine Aufnahme ansehen will, und nach drei Stunden vom Jetson wieder gelöscht. Dieselben
Rahmen stehen in `<satz>.jsonl`, das heißt das Bild mit Rahmen lässt sich jederzeit aus Rohvideo plus
Messdaten nachzeichnen — dann, wenn jemand es sehen will, statt bei jeder Aufnahme.

## 5. Der 1-Wire-Bus (w1_bus_master1)

`dtoverlay=w1-gpio` steht in Zeile 49 von `/boot/firmware/config.txt`. Am Bus hängen drei Geräte mit den
Kennungen `00-10bc00000000`, `00-50bc00000000`, `00-90bc00000000`. Die Familienkennung 00 gibt es nicht —
das sind Geisterfunde auf einem Anschluss ohne Sensor. Der Suchlauf steht auf unbegrenzt
(`w1_master_search = -1`, Takt 10 s) und kostet dafür dauernd 0,11 Kerne.

## 6. Was daraus folgt (nichts davon ist getan, alles braucht sein Wort)

| Maßnahme | Wirkung | Eingriff |
|---|---|---|
| `_rahmen.avi` nicht mehr mitschreiben, sondern auf Abruf aus `.avi` + `.jsonl` zeichnen | Schreiblast und rsync-Verkehr je etwa halbiert (−22 GB je Tag) | Änderung an `auswertung_1.4.py`, die nach seinem Wort „wie sie ist" bleiben soll — daher als eigene Fassung 1.9 neben der laufenden |
| Suchlauf des 1-Wire-Busses anhalten: `w1_master_search` auf 0 | 0,11 Kerne frei, sofort und ohne Neustart rücknehmbar | Eingriff ins laufende System, aber folgenlos und umkehrbar |
| `dtoverlay=w1-gpio` aus `config.txt` nehmen | dasselbe dauerhaft | braucht einen Neustart des Pi und beendet den Dauerlauf |
| Systemtagebuch auf flüchtig stellen (`Storage=volatile`) | 800 MB auf der Karte frei, ein kleiner Teil der Schreiblast weg | Protokolle überstehen dann keinen Neustart — beim Suchen von Fehlern hinderlich |

Der Kiosk-Firefox (0,54 Kerne) und die Wache (0,25 Kerne) stehen nicht auf dieser Liste: zusammen sind sie
weniger als ein Kern von vieren, und beide erfüllen einen Zweck. Mit 53 % Prozessorlast gibt es keinen
Grund, an ihnen zu sparen.

## Gemessen mit
`pi_last_messen_1.0.py`, `pi_warten_messen_1.0.py`, `pi_schreiber_messen_1.0.py` (alle im Projekt,
laufen auf dem Pi, lesen nur).
