# Prüfprotokoll 07.11.2026 — Mikroskop, Lernseite, Brücke und Netz

Sein Auftrag: „alles prüfen und zwar vollständig mit tests und Protokoll" sowie „wenn irgendwas stecken
bleibt oder abbricht, immer nach dem Fehler suchen — nicht gleich Umwege bauen".

---

## Teil 1 · Browserproben der Lernseite

Alle Proben laufen im echten Browser (Chromium über Playwright) gegen echte Daten vom Gerät: die Liste mit
301 Einträgen, vier verschiedene echte Lernbilder mit ihren echten Rahmen. Der Jetson wird durch einen
Stellvertreter ersetzt, der den Serverzustand mitführt; sein Gerät wird dabei nicht angefasst.

| Probe | Prüft | 1.5 | 1.7 | 1.8 | 1.9 |
|---|---|---|---|---|---|
| `pruefe_lernseite_knopf_1.1.js` | jeder Knopf, Auswahl, Zahlen, Platzanzeige | 11/16 | 16/16 | 16/16 | 16/16 |
| `pruefe_lernseite_stabil_1.0.js` | Bildabriss, Doppelklick, Listenausfall, Wettlauf | 1/4 | 4/4 | 4/4 | 4/4 |
| `pruefe_lernseite_bild_1.0.js` | Bildwechsel mit vier verschiedenen Bildern | — | 8/8 | 8/8 | 8/8 |
| `pruefe_lernseite_neu_1.0.js` | Namensfeld, Bereit-Anzeige, Zurücksetzen, Zurückstellen | — | 11/11 | 11/11 | 11/11 |
| `pruefe_lernseite_platz_1.0.js` | Lage bei fünf Bildschirmgrößen | — | — | 16/16 | 21/21 |
| `pruefe_lernseite_maus_1.0.js` | gezogener Rahmen auf der skalierten Leinwand | — | — | 5/5 | 5/5 |
| `pruefe_lernseite_reiter_1.0.js` | im Rahmen der Pi-Seite (960 px, wie im Reiter) | — | — | 3/8 | 8/8 |

**Jede Probe fällt an der jeweils vorigen Fassung durch.** Eine Probe, die nie rot wird, beweist nichts.

### Was die Proben gefunden haben
1. **1.5:** Auswahl stand fest auf „nur offene", davon gibt es null → Liste leer, jeder Weiterknopf meldete
   „Keine weiteren Bilder". Das war seine Meldung „die Lernseite arbeitet nicht".
2. **1.5:** kam ein Bild nicht an, blieb das vorige stehen und das Bewerten war weiter möglich — wer dann
   bewertet, zeichnet Rahmen auf das falsche Bild.
3. **1.7:** die Seite war 2240 px hoch bei 1080 px Fenster und sprang beim Laden selbst 1050 px nach unten.
4. **1.8:** bei 1366×768 wurde die Leinwand 944×355 statt 4:3 — das Bild war flachgedrückt. Ursache:
   `max-width` und `max-height` zusammen klemmen unabhängig voneinander.
5. **1.8:** im Reiter „Lernen" der Pi-Seite griff die Umschaltung auf zwei Spalten nie, weil der Rahmen dort
   nur 960 px breit ist und die Bedingung bei 1001 px lag. Und `scrollIntoViewIfNeeded` auf der Listenzeile
   riss beim Weiterschalten die ganze Seite nach unten.

### Eine Probe war selbst falsch
Die erste Knopfprobe bestand 16 von 16 und war für seinen Befund „es wird immer dasselbe Bild angezeigt"
**blind**: der Stellvertreter lieferte für jeden Bildnamen dasselbe JPEG. Seither bekommt jeder Fall eigene
echte Daten, und geprüft wird die Prüfsumme der Bildpunkte auf der Leinwand, nicht der Listeneintrag daneben.

---

## Teil 2 · Prüfung am echten Gerät

| Probe | Ergebnis |
|---|---|
| `jetson_ruecksetzprobe_1.0.py` — Knopf „alles Gelernte zurücksetzen" an seinen echten Bewertungen | **8 von 8** |

Ablauf: eigene Vollkopie des Ordners, Stand festhalten, zurücksetzen über den Dienst, nachsehen dass alles
auf „offen" steht, **aus der Sicherung des Dienstes** wiederherstellen, Datei für Datei vergleichen.
Ergebnis: 301 Bilder zurückgesetzt, 301 zurückgeschrieben, kein einziger Unterschied. Damit ist nicht nur
der Knopf geprüft, sondern auch der Weg zurück.

---

## Teil 3 · Messungen zu den Punkten 1, 6, 7, 9

| Punkt | Programm | Ergebnis |
|---|---|---|
| 1 Rechenlast | `pi_last_messen_1.0.py`, `pi_warten_messen_1.0.py`, `pi_schreiber_messen_1.0.py` | Prozessor 2,12 von 4 Kernen; die Last kommt von der Speicherkarte; 47 GB/Tag, davon 48 % eine Datei, die kein Programm liest |
| 6 Lichtfarbe | `jetson_lichtfarbe_1.1.py`, 160 Sätze über 25 h | Licht stabil (Blau/Rot 1,6 %); Schwelle 40 in **0 von 160** Sätzen die beste |
| 7 dichte Tiere | `jetson_nummernwechsel_1.1.py`, 191 214 Bilder | 0,006 % der Bilder; Verschmelzungsverdacht 1,09 %, im Bild aber 9 von 12 ein einziges Tier |
| 9 blinde Flecken | `jetson_zaehlgenauigkeit_1.1.py`, `jetson_farbschwelle_1.0.py`, `jetson_farbfilter_1.0.py` | Verlust: Sättigung 1,2 %, Ortsfest-Maske 7,5 %, Form 1,2 %, Flächenfenster 8,1 %; über dem Aufdruck 79,4 % gefunden, frei davon 100 % |

Zwei eigene Fehlmessungen sind dabei aufgefallen und berichtigt worden: die Lichtfarbe wurde zuerst außerhalb
des Helligkeitsfensters der Regel gemessen (Ergebnis unsinnig in **jedem** Satz), und die Farbregel wurde
zuerst ohne die Ortsfest-Maske nachgerechnet, die es zu diesen Bildern nicht mehr gab.

---

## Teil 4 · Brücke und Netz (der heutige Ausfall)

**Befund: die Strecke zwischen seinem Rechner und dem Arbeitsbereich überträgt zwar noch, aber nur mit
etwa 20 Byte je Sekunde. Alles über ein paar Kilobyte scheitert.**

### Erster Verdacht geprüft und verworfen
Die Brücke selbst lebt. `/puls` zeigt, dass sein Rechner alle Projekte regelmäßig abfragt — zeitweise alle
4 Sekunden. Blockiert war sie zweimal durch **meine eigenen** langen Befehle: erst hängende SSH-Übertragungen
zum Pi (sein Wort: „ssh sollte wieder funktionieren"), dann eine Netzdiagnose mit Pings und Wegverfolgung,
die über zehn Minuten lief. Die Brücke arbeitet die Projekte nacheinander ab; ein langer Befehl hält den
ganzen Durchlauf auf.

### Die eigentliche Messung
Der Empfänger im Arbeitsbereich liefert alle Dateien **örtlich in 11 bis 17 Millisekunden** aus — die Quelle
ist also in Ordnung. Über die Brücke zu seinem Rechner:

| Übertragung | Größe | 15:41 | 16:01 |
|---|---|---|---|
| `info` (Antwort rund 3 kB) | 3 kB | 20 s | **keine Antwort in 40 s** |
| `update probe_200.txt` | 200 B | 29 s | 149 s |
| `update probe_2000.txt` | 2 000 B | 122 s | 180 s |
| `update probe_20000.txt` | 20 000 B | **keine Antwort in 300 s** | — |
| `update nk.py` | 1 076 B | — | **keine Antwort in 300 s** |
| `hole` Jetson-Stand (Gegenrichtung) | 1,9 kB | 35 s | **keine Antwort in 90 s** |

Beide Richtungen sind betroffen, und es wird im Lauf der Stunde schlechter. Kleine Anfragen (das Abfragen
der Brücke) kommen durch, große Antworten nicht.

### Was dieses Muster bedeutet
Kleine Pakete gehen, große bleiben stecken — das ist die Signatur von zwei Ursachen:
1. **Paketgröße (MTU / Path MTU Discovery).** Die Verbindung kommt zustande, aber sobald volle Pakete
   fließen, verschwinden sie. Typisch bei DS-Lite, VPN-Tunneln und manchen Routern.
2. **Paketverlust auf der Strecke.** Jedes verlorene Paket wird wiederholt, der Durchsatz bricht ein.

Das deckt sich mit seiner Beobachtung „manche Seiten im Netz nicht erreichbar": Seiten mit wenig Inhalt
laden, Seiten mit viel Inhalt hängen.

### Was ich nicht mehr tun konnte
Die Kurzdiagnose `nk.py` (1 076 Byte) kam nicht mehr über die Strecke. `netz_pruefen_1.0.py` liegt seit
14:11 auf seinem Rechner unter `<Brückenordner-auf-dem-PC>\`, ihre Ausgabe ist aber zu lang für die jetzige Strecke.

### Was er selbst tun kann
Ein Eingabeaufforderungsfenster öffnen und diese Zeilen eingeben. Sie ändern nichts, sie messen nur:

```
ping -n 20 1.1.1.1
ping -n 1 -f -l 1472 1.1.1.1
ping -n 1 -f -l 1452 1.1.1.1
ping -n 1 -f -l 1420 1.1.1.1
ping -n 20 -l 1400 1.1.1.1
nslookup www.heise.de
```

- Zeile 1: Verlust und Laufzeit. Über 1 % Verlust ist auffällig.
- Zeilen 2 bis 4: die größte Paketgröße, die ohne Zerteilen durchkommt. Kommt 1472 nicht durch, 1452 aber
  schon, ist die Paketgröße die Ursache (1492 statt 1500).
- Zeile 5: zwanzig **große** Pakete. Geht hier der Verlust hoch, während Zeile 1 sauber war, ist es bewiesen.
- Zeile 6: ob die Namensauflösung antwortet.

Dazu die Fritz!Box unter `http://fritz.box` öffnen: *Internet · Online-Monitor* zeigt Störungen und
Verbindungsabbrüche, *Internet · Zugangsdaten · Verbindungseinstellungen* die eingestellte Paketgröße.

Wenn `netz_pruefen_1.0.py` auf seinem Rechner laufen soll, geht das auch ohne mich:
```
"<Python-auf-dem-PC>" <Brückenordner-auf-dem-PC>\netz_pruefen_1.0.py
```

---

## Teil 5 · Was ausgeliefert ist und was nicht

| Stand | wo |
|---|---|
| Lernseite **1.8** | auf dem Jetson im Einsatz |
| Lernseite **1.9** (Spalte im Reiter, kein Sprung) | fertig und geprüft, **nicht übertragen** — Strecke zu langsam |
| Jetson-Dienst **1.11** | im Einsatz |
| Jetson-Dienst **1.12** (Lernkurven) | fertig und geprüft, **nicht übertragen** |
| Pi-Seite **1.33** | im Einsatz |
| Pi-Seite **1.34** (Reiter breit, Statistik zweispaltig, Lernkurve, YOLO in Beschreibung und Manuskript) | fertig und geprüft, **nicht übertragen** |

**Nachtrag 18:50 — alles ausgeliefert.** Die Leitung kam um 17:42 zurück (45 MB in 14 s). Stand jetzt am Gerät:

| | Fassung | geprüft am Gerät |
|---|---|---|
| Lernseite | **1.9** | Titel zurückgeholt |
| Jetson-Dienst | **1.12** | `/stand` meldet 1.12, `/yolo/verlauf` liefert 4 echte Trainingsläufe |
| Pi-Seite | **1.34** | `seite.html` 132 560 Byte, Fußzeile „Seite 1.34" |
| YOLO-Livedienst | 1.3 | 28,8 Bilder/s, Livestrom verbunden, 0 abgeschnitten |
| Pi-Auswertung | 1.4 | 29 Stunden ohne ein kaputtes Bild |

Sein Lernstand ist dabei gewachsen: 71 geprüft, 224 zurückgestellt, 6 verworfen.

### Drei Fehler beim Ausliefern, alle gesucht statt umgangen
1. **`pi.py` löscht `pi_hochladen.txt` nach dem Hochladen** (Zeile 79, `HOCHLADEN.unlink()`). Beim zweiten
   Lauf fehlte die Liste, und der Auftrag kopierte die ALTE Datei weiter — die Pi-Seite blieb 126 535 Byte
   statt 132 560. Die Liste muss vor jedem Lauf neu übertragen werden.
2. **Der Wächter führte den falschen Auftrag aus.** `pi_auftrag.txt` auf `<Brückenordner-auf-dem-PC>` war noch der
   Dienstwechsel, weil meine Seiten-Anweisung nie angekommen war. Erkennbar an der Ausgabe `PI_OK 155355`
   statt `SEITE_GESETZT`.
3. **Meine Platzprobe war zu schwach.** Sie verlangte nur, dass die Stundentafel rechts *steht*, nicht dass
   sie neben dem Bild steht. Sie bestand, während die Tafel in Wahrheit darunter saß und nur rechtsbündig
   war. Jetzt verlangt sie auch senkrechte Überlappung — und fällt an der alten Seite durch.

### Lernkurve mit echten Werten
`/yolo/verlauf` liefert vier Läufe vom 06.11.:

| Lauf | Epochen | mAP50 am Ende |
|---|---|---|
| lauf_1433 | 1 | 0,054 |
| lauf_1503 | 40 | 0,634 |
| lauf_1544 | 39 | 0,488 |
| lauf_1643 | 39 | 0,488 |

Im Einsatz ist ein Modell mit mAP50 0,526. **Der beste Lauf war nicht der letzte.** Bei 52 Lernbildern
schwankt das Ergebnis von Lauf zu Lauf stärker als der Fortschritt zwischen den Runden — ein weiteres
Argument dafür, zuerst die Zahl der bewerteten Bilder zu erhöhen.

Alles Fertige liegt in `<Arbeitsbereich>/Mikroskop_Pi5/`, gesichert als
`2026-11-07_Mikroskop_Pi5_endstand.tar.gz` (45 MB) und gespiegelt auf `<Sicherungsordner-auf-dem-PC>`.
