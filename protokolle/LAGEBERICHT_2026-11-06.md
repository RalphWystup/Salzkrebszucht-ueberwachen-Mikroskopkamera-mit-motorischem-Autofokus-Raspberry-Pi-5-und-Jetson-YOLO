# Lagebericht 06.11.2026, 14:05 — Mikroskop-Pi, Jetson, Brücke (kurz)

**Läuft:** Pi: Auswertung **1.4** (Rückfallebene, seit 13:45 wieder), Fokus, Seite 1.27 (Jetson-Block lesbar, Livestrom-Zeile), Kiosk.
Jetson: Dienst **1.5** (rsync, Farbwahrheit, Statistik, Livestrom 29 Bilder/s dauernd, Aufträge, Dateien, Platte räumt sich selbst).
Brücke 3.22 mit Wächter. Zusammenspiel geprüft 12:26: **15 von 15**. Kein Kennwort in Befehlen (Zugangsblatt). Sicherung und Wissensdatenbank auf C:.

| Nr | Problem | Stand | Nächster Schritt |
|---|---|---|---|
| 4 | **Ruhende Tiere übersehen** | gemessen: 75 % der Fehltreffer fehlen in der MOG2-Maske. 1.7 (Nachsuche) trifft an 70 Sätzen 83,5 % statt 76,8 %, ruhig 58,5 % statt 38,9 % — **live aber Marken ohne Tier (sein Auge)**: 51 Sätze zeigen 4643 Nachsuche-Marken ohne Tier und 21 stehende Bahnen; im Bild zwei graue **Körner** (im „O" des Aufdrucks, neben dem Schärfefenster), Bahn 30 hing 5 min daran. Die Nachsuche hält jeden dunklen braunen Körper für das Tier → zurück auf 1.4 (13:45) | Lebenszeichen messen (Eigenbewegung im Stand: Antennenschlag gegen totes Korn, läuft auf dem Jetson); 1.8 = Nachsuche nur mit Lebenszeichen und Frist ≤ 20 s; Freigabe nur mit seinem Auge am Schirm |
| 9 | Farbwahrheit blind | kennt **keine stillstehenden Tiere** (Medianbild) → „Geister" der Nachstellung sind oft echte Tiere | Wahrheit für Ruhende nur per Auge (Montagen) oder per Klassifikator (Weg B) |
| 8 | Dauerlauf / Jetson-Platte | 4,8 GB/h Videos; Dienst 1.5 löscht nach 3 h (Notregel 1 h), Lernarchiv jeder 10. Satz + behalten.txt ≤ 6 GB; 182 Sätze bereits bereinigt, 21 GB frei | Beobachten; Auswertung 1.4 läuft 24 h ohne Ausfall |
| GPU | YOLO auf dem Jetson | Umgebung ~/<yolo-umgebung>: torch 2.11 (Nachtbau) + ultralytics + TensorRT 10.7, cuDSS nachinstalliert — **CUDA „out of memory" beim ersten Zugriff** | torch 2.8.0 aus dem Jetson-Index wird gerade eingerichtet; dann Messung yolov8n PyTorch/TensorRT/Livestrom |
| 2 | Stundenzähler auf Platte | in 1.5–1.7 gebaut (zaehler.json), mit dem Rückfall auf 1.4 wieder nur im Speicher | kommt mit 1.8 |
| 1 | Pi-Last 8–9 | Kiosk-Firefox 1,1 Kerne, Wache 0,3, w1_bus 0,5 | **sein Wort**: Wache aus? Kiosk? |
| 5 | Längenmaß | Rumpf+Schwanz 0,95 mm (jetzt) oder Rumpf 0,3 mm; Maßstab ±0,9 % mit Fokus | **sein Wort** |
| 6 | Lichtfarbe | Brauntest auf heutiges Licht geeicht | Sättigung je Stunde auf dem Jetson mitschreiben |
| 7 | Zwei Tiere dicht | Nummernwechsel 0,3 % | gezielt messen, bevor etwas geändert wird |
| 3 | Vermessung | erledigt, Jetson rechnet laufend (≈ 900 Sätze, 950 µm, 1,9 mm/s, 0,48 Tiere/Bild) | — |
| B | Brücke / Aufträge | Kiosk-Neustart hielt die SSH-Sitzung (gelöst: abgelöst starten); Jetson-Dienst zeigt Auftragsbuch nach Neustart leer (1.6 bereit) | 1.6 wechseln, wenn kein Auftrag läuft |
| L | Literatur | OASIS, ARTiMiS, INVE/SnappArt ausgewertet (LITERATUR_2026-11-06.md); **abstract64.pdf nicht gefunden** | PDF nach <USB-Ordner-auf-dem-PC>\Pi_Beobachter legen |

**Offen für ihn:** 1, 5, Weg B (YOLO) freigeben, Dunkelfeld-Versuch (Ring-LED), abstract64.pdf.

## Nachtrag 16:15 — YOLO-Weg steht
- **Läuft:** Pi unverändert (Auswertung 1.4, Fokus, Kiosk), Seite **1.29** mit neuem Reiter „Statistik" (YOLO-Livebild mit Rahmen in Echtzeit, Tiere im
  Bild, bewegt/ruhend, Größe, Tempo, Bilder/s, Stundentafel; Reiter „Bedienen" wie bisher). Jetson: Dienst **1.9**, YOLO-Dienst **1.2** mit dem Modell
  aus seinen **52 bewerteten Bildern** (20–25 Bilder/s, erkennt Tiere live). Lernseite 1.5 mit Fertig-Knopf → nächste Runde automatisch.
- **Gelöst heute:** Kennwort nie in Befehlen (Zugangsblatt); Platte räumt sich (Dienst ≥ 1.5); Lernseite mit Maus; Training als eigene Einheit;
  Speicher: Cache leeren vor GPU-Start, kein TensorRT-Export, FEM-Dienst/Desktop als Speicherfresser benannt.
- **Offen / sein Wort:** FEM-Dienst des Rechenverbunds (1,6 GB Auslagerung) und GNOME-Desktop auf dem Jetson abschalten? Pi-Last (Wache, Kiosk); Problem 4
  klassisch geparkt (1.5–1.8), YOLO übernimmt; abstract64.pdf; Dichte je mL (Volumen kalibrieren); Lebend/Tot aus Tempo.
