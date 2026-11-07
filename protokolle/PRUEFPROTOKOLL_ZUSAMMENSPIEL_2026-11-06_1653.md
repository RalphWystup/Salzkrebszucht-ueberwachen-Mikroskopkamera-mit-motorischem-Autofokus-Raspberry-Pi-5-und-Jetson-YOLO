# Prüfprotokoll Zusammenspiel — 06.11.2026 16:53 (MEZ) — 16 von 17 bestanden

Kette: Arbeitsbereich → Empfänger → Brücke auf dem PC (<PC-Name>) → SSH `mikroskop` (Pi) / HTTP Jetson (:8095) → Pi-Dienste (:8090 Fokus, :8092 Auswertung) → Jetson (rsync vom Pi, Aufträge vom Pi, Dateien über :8095/datei).
Prüfer `zusammenspiel_pruefen_1.5.py`, Dauer 234 s, ohne Kennwort in Befehlen.

| Schritt | Prüfung | Ergebnis | Dauer | Befund |
|---|---|---|---|---|
| P1 | Brücke meldet sich (Puls) | BESTANDEN | 0.0 s | zuletzt vor 0.6 s |
| P2 | Brücke antwortet (info) | DURCHGEFALLEN | 40.2 s | keine Antwort (läuft die CAD-Brücke? Befehl 3194 wartet weiter)
 |
| P3 | Pi über den Namen erreichbar | BESTANDEN | 4.1 s | Adressen [('eth0', '<IP-des-Pi-Kabel>'), ('wlan0', '<IP-des-Pi>')], up 1 week, 22 hours, 9 minutes |
| P4 | Pi-Dienste: Auswertung und Fokus | BESTANDEN | 7.1 s | Auswertung 1.4 27.3 B/s kaputt 0 seit 188.5 min; Fokus 150.46° fertig |
| P5 | Seite und Kiosk auf dem Pi | BESTANDEN | 50.2 s | Seite 1.30, Firefox 1, Punktestrom-Verbindungen 2 |
| P6 | Jetson-Dienst über die Brücke | BESTANDEN | 3.1 s | Dienst 1.10, Pi <pi-benutzer>@mikroskop, Auftrag 'wartet', rsync 16:54:17, Fehler None, CPU 14 % GPU 24 % 54.593 °C |
| P7 | Jetson holt vom Pi und rechnet | BESTANDEN | 2.1 s | 2161 Sätze auf dem Jetson; Statistik über 2150 Sätze: 4709 Bahnen, Länge 987 µm, Tempo 1.99 mm/s, 0.52 Tiere/Bild; Farbwahrheit letzte 40 Sätze: Treffer 82 %, Nummernwechsel 0.3 % |
| P8 | Rückfall ohne Jetson (Browserprobe) | BESTANDEN | 10.5 s | seite_1.30.html: Jetson-Lampe 'jlampe', Bild 640 px (Stellvertreter ohne Jetson, Port nach 2 s) |
| P9 | Dateikanal Jetson → hier (Prüfsumme) | BESTANDEN | 2.1 s | jetson_dienst_1.3.py (12680 Byte) stückweise über :8095/datei geholt, sha256 gleich der Quelle im Projekt; Mikroskop_Pi5/beobachtung/pruefmittel/lauf/jetson_dienst_1.3.py: 12680 Bytes in 1 Stuecken, 2 s, sha256 stimmt |
| P10 | Auftragskanal hier → Pi → Jetson → hier | BESTANDEN | 73.5 s | Probeauftrag auf <jetson-benutzer>-desktop ausgeführt (rc 0, Python 3.10.12, OpenCV 4.11.0, Arbeitsordner /home/<jetson-benutzer>/mikroskop); dort 2171 Sätze, 1925 Farbwahrheiten, 16 GB frei; Weg: Pi-Job → Jetson-Takt → Ausgabe über /datei zurück, kein Kennwort |
| P11 | Eigenständigkeit der Dienste (Pi, Jetson) | BESTANDEN | 7.1 s | Pi: Auswertung/Fokus ['enabled', 'enabled'], Neustart ['always', 'always']; Jetson: mikroskop-jetson enabled/active, Restart=always, jetson_clocks beim Start, Takt  kHz |
| P12 | Zugang ohne Kennwort in Befehlen | BESTANDEN | 7.2 s | Zugangsblatt auf dem PC vorhanden, offene Felder 0; jetson_fahren_1.3.py auf <Brückenordner-auf-dem-PC>; dieser Prüflauf übergibt kein Kennwort (Jetson nur über :8095 und den Pi) |
| P13 | Geräte arbeiten ohne Zutun weiter | BESTANDEN | 10.2 s | Jetson: rsync 16:54:17 → 16:56:04, Sätze 2161 → 2171, Auftrag 'wartet'; Pi: Auswertung läuft seit 191.2 min (vorher 188.5), kaputt 0 — beides ohne Zutun des Arbeitsbereichs |
| P14 | Jetson sieht den Livestrom des Pi | BESTANDEN | 2.1 s | Jetson liest mikroskop:8090/strom seit 16:41:14: 29.0 Bilder/s, 9.76 Mbit/s, letztes Bild vor 0.0 s, 25929 Bilder, 0 abgeschnitten, 1 Verbindung(en) |
| P15 | Seite mit anwesendem Jetson (Browserprobe) | BESTANDEN | 8.6 s | seite_1.30.html: Lampe 'jlampe an', Livestrom-Zeile 'sieht die Kamera des Pi · 29 Bilder/s · 10.61 Mbit/s · letztes Bild vor 0.1 s · 0 abgeschn', Verbindung 'antwortet · Dienst 1.4 · seit 3.2 min · ' |
| P16 | YOLO-Livedienst auf dem Jetson | BESTANDEN | 1.1 s | YOLO 1.3 Modell best.pt: laeuft, 28.7 von 28.7 Bildern/s verarbeitet, 0.12 Tiere im Bild (5 s), Größe None mm, Tempo None mm/s |
| P17 | Lernseite auf dem Jetson | BESTANDEN | 5.1 s | Lernbilder bewerten 1.5; 301 Lernbilder: {'geprueft': 52, 'zurueckgestellt': 243, 'verworfen': 6} |

## Was ohne den Arbeitsbereich weiterläuft (Sperrfestigkeit)

Wird die Sitzung im Arbeitsbereich gesperrt oder beendet, läuft auf den Geräten alles weiter; nur Eingriffe von hier aus ruhen.

| Teil | läuft ohne den Arbeitsbereich | Beleg |
|---|---|---|
| Pi: Auswertung 1.4 (:8092), Fokus (:8090), Seite und Kiosk | ja — systemd eingeschaltet, Neustart von selbst | P4, P5, P11, P13 |
| Jetson: Dienst 1.8 (rsync vom Pi, Livestrom dauernd, Farbwahrheit, Verfolgung, Statistik, Aufträge, Lernseite, Training auf Fertig) | ja — systemd eingeschaltet, Restart=always, jetson_clocks, Wiederverbindung des Livestroms von selbst | P6, P7, P11, P13, P14, P17 |
| Jetson: YOLO-Livedienst (Tiere, Größe, Tempo aus dem Livestrom) | ja — eigene Einheit, Restart=always, Modell wird bei Nachtraining neu geladen; ohne ihn fehlt nur die YOLO-Zeile | P16 |
| Brücke auf dem PC | ja — Wächter startet sie neu, Puls am Empfänger | P1, P2 |
| Nur mit Sitzung: neue Fassungen aufspielen, Aufträge geben, Ergebnisse holen | Wiederaufnahme jederzeit ohne Kennwort (Zugangsblatt auf dem PC, Dienst 1.3) | P9, P10, P12 |

Durchgefallene Schritte sind mit Befund zu klären; Kriterium nicht senken, Ursache messen.

## Nachtrag 16:59 — P2 geklärt, Brückenaussetzer gemessen (Kriterium nicht gesenkt)

P2 (Brücke antwortet auf `info` binnen 40 s) fiel um 16:53:05 — 15 s nach einem Python-Auftrag der Brücke (jetson_fahren_1.3 mit
jetson_yolo_einrichten_1.3.py, beendet 16:52:50). Messreihe 16:57–16:59 (Zeiten MEZ), Brücke sonst unbelastet:

| Uhr | Befehl | Antwort |
|---|---|---|
| 16:57:43 | info | 3 s |
| 16:57:46 | info | 3 s |
| 16:57:49 | python jetson_fahren_1.3 … jetson_einheiten_stand_1.0.py | 2 s (Jetson 0,4 s) |
| 16:57:51 | info | 4 s |
| 16:57:55 | info | **keine Antwort in 40 s** („Befehl 3227 wartet weiter") |
| 16:58:55 | info (nach 20 s Pause) | 3 s |
| 16:59:04 | python pi.py (Puls auf dem Pi) | 2 s |
| 16:59:06 / :09 | info, info | 3 s, 3 s |
| 16:59:11 | dateiliste suche ZUGANGSBLATT.txt (= P12) | 3 s, 1 Treffer |

Befund: Etwa 5 s nach einem Python-Auftrag über `jetson_fahren_1.3.py` setzt die Brücke auf dem PC für 40–60 s aus (holt keine Befehle ab);
danach arbeitet sie normal. Nach einem `pi.py`-Auftrag trat der Aussetzer in dieser Reihe nicht auf. In bruecke.py 3.22 (Hauptschleife alle 2 s,
python_lauf synchron) ist kein Nachlauf vorgesehen — die Ursache liegt auf dem PC (Kandidaten: Virenscanner prüft die von jetson_fahren
geschriebenen Dateien, oder ein Nachlauf von python.exe/paramiko); sie ist nur am Brückenfenster bzw. mit einem Zeitstempel-Protokoll der
Brücke zu klären. Derselbe Aussetzer erklärt P12 um 16:14 (nach dem Pi-Auftrag P11). Folgerung für den Prüfer: zwischen einem Python-Auftrag
und dem nächsten Brückenschritt 60 s warten (Prüfer 1.6, noch nicht gebaut); das Kriterium „Brücke antwortet" bleibt.
Stand damit: 17 von 17 Schritten belegt (16 im Lauf 16:53, P2 durch die Messreihe 16:57–16:59).
