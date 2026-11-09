# Salzkrebszucht überwachen: Mikroskopkamera mit motorischem Autofokus am Raspberry Pi 5, Jetson Orin Nano erkennt und zählt mit YOLO

<img src="Foto_Ralph_Wystup.jpg" align="right" width="140" alt="Prof. Dr.-Ing. Ralph Wystup">

**Autoren:** Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt · Fassung 1.2 vom 09.11.2026

**Seite:** https://ralphwystup.github.io/Salzkrebszucht-ueberwachen-Mikroskopkamera-mit-motorischem-Autofokus-Raspberry-Pi-5-und-Jetson-YOLO/ —
Bedienen, Statistik, Lernen, Hardware, Beschreibung, Manuskript (Teil A Autofokus, Teil B Beobachtung und YOLO), Messungen,
Zusammenarbeit mit der KI. Dieselbe Seite läuft live auf dem Pi mit Bild, Kurve, Punkten und den Zahlen des Jetson.

**Kurzbeschreibung.** Eine Salzkrebszucht (*Artemia*, Lebendfutter der Aquakultur) wird unter einem einfachen USB-Mikroskop
überwacht. Der motorische Autofokus (Servo am Rändelrad, Teil A) hält das Bild scharf. Ein **Raspberry Pi 5** liefert Bild,
Schärfe, Anzeige und eine regelbasierte Verfolgung der Tiere — und läuft allein, wenn alles andere ausfällt. Ein **Jetson Orin Nano**
liest den Livestrom mit, sammelt die Aufnahmen, lässt sich Lernbilder vom Menschen bewerten (Lernseite mit der Maus), lernt daraus auf
dem Gerät ein **YOLOv8**-Modell und liefert die Statistik zurück auf die Seite des Pi: Tiere je Bild, bewegt oder ruhend, Körpergröße,
Tempo, Stundenzähler — mit einem Livebild, in dem jeder erkannte Rahmen in Echtzeit eingezeichnet ist.

**Anwendungsfall:** Überwachung der Salzkrebszucht — wie viele Tiere, ob sie leben und sich bewegen, wie groß sie werden. Die nächste
Runde Lernbilder startet das Nachtraining mit einem Knopf; das Modell wird im Lauf nachgeladen.

![YOLO bei der Arbeit: Livebild mit Rahmen, Klasse und Sicherheit](bilder/bild_yolo_1.jpg)

![Die Lernseite auf dem Jetson: Rahmen mit der Maus bewerten, Klassen Tier/Korn/Maßstab, Fertig-Knopf](bilder/lernseite.png)

## Was gemessen wurde (06.11.2026)

| Größe | Wert |
|:--|--:|
| YOLOv8n auf dem Jetson, PyTorch FP16 | 49,8 Bilder/s |
| YOLO-Livedienst am Strom des Pi, mit Verfolgung (ByteTrack) | 28,8 von 28,8 Bildern/s |
| Livestrom Pi → Jetson | 30 Bilder/s, 11 Mbit/s |
| Training mit 52 bewerteten Bildern (43/9), YOLOv8n, 40 Epochen | 215 s, mAP@0,5 = 0,53 |
| Erstes Modell aus 301 Bildern mit Vorschlagsrahmen | 12 min, mAP@0,5 = 0,65 |
| Problem „Pi verpasst Tiere": Anteil, der schon am Bewegungsmodell scheitert | 75 % |
| Zusammenspiel Pi · Jetson · Brücke · Browser, Prüfer mit 17 Schritten | 17 von 17 belegt |

## Was am 07.11.2026 dazukam

| Größe | Wert |
|:--|--:|
| YOLO gegen die Rahmen von Hand, Schwelle 0,40 (wie im Livedienst) | 10 % Trefferquote |
| dieselbe Messung bei Schwelle 0,25 | 32 bis 38 % |
| dieselbe Messung bei Schwelle 0,10 | 62 bis 78 % |
| Tiere, die der Mensch nachtragen musste (keine Maschine fand sie) | 43 von 209 |
| Farbregel: Verlust an der Ortsfest-Maske über dem Aufdruck | 8,6 %, daneben 0 % |
| Farbregel: Verlust am Flächenfenster | 8,1 % |
| zwei getrennt verfolgte Tiere näher als 50 px | 12 von 191 214 Bildern |
| Lichtfarbe über 25 Stunden, Blau zu Rot | 1,6 % Schwankung |
| Schwelle S > 40 als beste Schwelle, über 160 Sätze | in 0 von 160 |
| Rechenlast des Pi | 2,12 von 4 Kernen; die Last trägt die Speicherkarte |
| Browserproben der Lernseite und der Seite | 87 Prüfpunkte, alle bestanden |

Jede dieser Proben fällt an der jeweiligen Vorgängerfassung durch — eine Probe, die nie rot wird, beweist nichts.
Einzelheiten in `protokolle/PROTOKOLL_2026-11-07.md`.

## Was am 09.11.2026 dazukam: der Absturz der Nacht und das Nachziehen der Lernbilder

In der Nacht vom 08. auf den 09.11. fror der Pi ein. Das Journal zeigt die Ursache: die Schreibwarteschlange des Bildwächters 1.4 war
unbegrenzt, bei dichter Tierbewegung stieg der Verzug zwischen Auslösung und Ablage auf bis zu 34 Minuten, der Prozess wuchs auf 2,2 GB,
der Kern beendete ihn zweimal, dann stand der Speicher. Das „Stocken“ des Bildes am Nachmittag davor war Auslagern, kein Netzproblem.

| Größe | Vorher (1.4) | Jetzt (1.4_rev2) |
|:--|--:|--:|
| Schreibwarteschlange | unbegrenzt | höchstens 3 Sätze, Überzähliges wird verworfen und gezählt |
| Speicher des Bildwächters nach 2 Tagen / nach 54 min | 2,19 GB (Kern-Abschuss) | 260 MB; Speicherwache 1,2 GB, `MemoryMax` 1,5 GB wirkt (Kern-Controller eingeschaltet) |
| Versatz Anzeige hinter Bedienen (Median) | 0,51 s | 0,15 s |
| Aussetzer der Hauptschleife über 1 s | nicht gemessen | 0 in 54 min (Protokoll im Journal und in `/stand`) |
| Zähler nach einem Neustart | weg | 72 h Verlauf und Gesamtzähler von der Karte |
| Erkennung und Verfolgung (Rohaufnahme, 440 Bilder, dreimal) | — | Bild für Bild identisch mit 1.4 |
| Lernbilder nachziehen (Knopf, Lernseite 1.10) | — | 100 Bilder mit erkannten Tieren aus den letzten 6 h in 5 s, Zeitmarke je Runde |
| Training nach dem Nachziehen (398 Bilder, 40 Epochen, 1004 s) | Tier mAP@0,5 = 0,53 | **0,75** |

Der ältere Bildwächter („Wache“, 8091) zählte dasselbe zweimal und ist entfernt; die Seite 1.35 hat den Reiter nicht mehr.
Einzelheiten in `protokolle/STAND_2026-11-09.md` und im Manuskript, Kapitel 20.

Ein Filmausschnitt (5,9 s, der tierreichste Satz mit Video nach YOLO-Zählung, 06.11.2026 17:33 Uhr) liegt in `video/`: [roh](video/clip_roh_2026-11-06.mp4) und [mit den Rahmen des Modells](video/clip_yolo_2026-11-06.mp4); auf der Seite läuft er im Manuskript, Kapitel 13.

**Erklärvideo des Verfassers** (09.11.2026, 4:06 min, Hochformat, mit Ton, 65 MB): ein Rundgang am Aufbau — Mikroskop mit Servo am Rändelrad, Raspberry Pi mit Anzeige, Jetson, Verkabelung — [video/Erklaervideo_USB_Mikroskop_Salzkrebse_2026-11-09.mp4](video/Erklaervideo_USB_Mikroskop_Salzkrebse_2026-11-09.mp4).

## Aufbau

* **Pi:** `pi/autofokus4.py` (Fokusdienst mit Seite, Teil A), `pi/auswertung_1.4_rev2.py` (Bildwächter: MOG2, Form und Farbe,
  Verfolgung, Aufzeichnung; seit 09.11. begrenzte Warteschlange, Speicherwache, Zähler auf der Karte, Aussetzer-Protokoll),
  `pi/mikroskop-auswertung.service` (mit `MemoryMax`), `pi/pi_auswertung_wechsel_1.0.sh` (Fassungswechsel und Rückfall mit einem
  Befehl), systemd-Einheiten, `pi/EINRICHTEN.md`.
* **Jetson:** `jetson/jetson_dienst_1.13.py` (Sätze holen, Farbwahrheit, Statistik, Aufräumen, Livestrom, Aufträge, Dateien,
  Lernseite, Fertig → Training, `POST /lernen/nachziehen`), `jetson_yolo_live_1.3.py` (Livedienst mit `/stand` und `/strom`),
  `jetson_yolo_training_1.4.py`, `jetson_yolo_datensatz_1.2.py` (alle Runden mit Zeitmarke zusammen, Zusammensetzung im Verlauf),
  `jetson_lernbilder_1.1.py` (Nachziehen: nur Bilder mit erkannten Tieren, jüngste Aufnahmen zuerst), `jetson_lernbilder_auswahl_1.0.py`,
  `tiere_nach_farbe_1_6.py`, `jetson_yolo_einrichten_1.3.py` (Einheiten mikroskop-training und mikroskop-yolo, sudoers), Starter mit
  Fassungsdatei.
* **Lernseite:** `lernseite/lernen_1.10.html` — Rahmen bewerten mit der Maus, Klassen Tier/Korn/Maßstab, Fertig-Knopf, Knopf
  „100 neue Bilder aus aktuellem Material“, Auswahl „neueste Runde“.
* **Prüfung:** `pruefung/zusammenspiel_pruefen_1.5.py` (P1–P17), Browserproben mit Playwright, Stellvertreter des Fokusdienstes.
* **Messprogramme (07.11.2026):** `jetson/jetson_nummernwechsel_1.1.py` (dichte Tiere), `jetson_lichtfarbe_1.1.py` (Lichtfarbe über
  die Zeit), `jetson_zaehlgenauigkeit_1.1.py` (YOLO und Farbregel gegen die Rahmen von Hand), `jetson_farbschwelle_1.0.py`,
  `jetson_farbfilter_1.0.py` (an welcher Stufe die Farbregel verliert), `pi/pi_last_messen_1.0.py`, `pi_warten_messen_1.0.py`,
  `pi_schreiber_messen_1.0.py` (Rechenlast, Wartezeit, Schreiblast des Pi).
* **Protokolle und Befunde:** `protokolle/` — der Stand vom 09.11.2026 (Absturzursache, Abhilfe, Messungen, Rückfälle), das
  Prüfprotokoll vom 07.11.2026 mit 87 Prüfpunkten, die Befunde zu den Problemen 1, 6, 7 und 9, der Befund zur Lernseite, dazu
  Lagebericht und Befund zu Problem 4 vom 06.11.; `literatur/` (Auswertung mit der Kurzfassung von Wang und De Baets, Gent 2019, CC BY 4.0).
* **Manuskript:** `manuskript/Manuskript_Salzkrebszucht_1.2.pdf` (Teil A und B, Kapitel 20 Nachtrag vom 09.11.) und als Reiter in der Seite.
* **Prüfung der Seiten (09.11.2026):** `pruefung/pruefe_seite_1.35_1.0.js` (19 Proben), `pruefe_lernseite_nachziehen_1.0.js` (14 Proben).
* **Brücke:** `bruecke/` — die Werkzeuge, mit denen die KI über den PC des Verfassers Pi und Jetson erreicht (Aufträge, Dateien,
  Zugang ohne Kennwort in Befehlen). Adressen und Pfade sind durch Platzhalter ersetzt.

## Grundsätze, die hier gelten

* Der Pi wartet nie auf den Jetson; fällt der Jetson aus, fehlt nur die Statistik (Browserprobe P8).
* Jede Fassung daneben, Rückfall benannt; geprüfte Fassungen bleiben unverändert.
* Jede Seite wird im echten Browser durchgespielt, bevor sie auf das Gerät geht.
* Kennwörter nie in Befehlen; Aufträge und Dateien laufen über den Pi, nicht über Zugangsdaten.

## Stichworte

Artemia, Salzkrebse, brine shrimp, Lebendfutter, Aquakultur, Zuchtüberwachung, USB-Mikroskop, motorischer Autofokus, Raspberry Pi 5,
Jetson Orin Nano, YOLOv8, Objekterkennung, Edge-KI, Training auf dem Gerät, Lernbilder, Bildauswertung, Bewegungserkennung (MOG2),
Tierverfolgung, ByteTrack, OpenCV, Planktonkamera, Mikroskopie.

## Lizenz

MIT (siehe `LICENSE`). Die Kurzfassung in `literatur/` steht unter CC BY 4.0 bei ihren Verfassern.
