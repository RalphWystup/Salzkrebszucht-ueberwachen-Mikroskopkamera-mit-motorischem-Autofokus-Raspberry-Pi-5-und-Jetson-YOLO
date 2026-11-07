# Literaturauswertung 06.11.2026 — Planktonkameras und Lebendfutter-Zählung, bezogen auf unser Mikroskop

Auftrag (sein Wort, 13:45): „werte noch aus: abstract64.pdf, OASIS | PLANKTONKAMERA – SOOP, How technology is redefining live food management
in the hatchery (Artemia Knowledge Hub), Introducing ARTiMiS (PMC)". **abstract64.pdf wurde weder im Arbeitsbereich noch auf C: gefunden**
(Suche auf dem PC ohne Treffer) — bitte nach `<Projektordner-auf-dem-PC>` legen, dann wird sie nachgetragen.

## 1. OASIS (openUC2) im Helmholtz-Projekt SOOP
Quellen: https://www.soop-platform.earth/measurement-technology/oasis/ , https://github.com/openUC2/openUC2_SOOP (archiviert 13.01.2026).
Durchfluss-Planktonmikroskop im IP66-Koffer: Objektiv 10×/0,3 NA, USB-3-Kamera (Sony IMX179), Peristaltikpumpe (Nema 17), Fokus über
Schneckentrieb, Raspberry Pi 5, LED-Durchlicht, 7-Zoll-Touchscreen, 12 V, 35 × 20 × 12 cm, Auflösung etwa 3–5 µm, Durchflusszelle (ibidi).
Software ImSwitch in Docker (Browser auf :8001), „Durchfluss-Stopp-Mikroskopie" (Pumpe stoppt, Bild, weiter), Ablage als JPG auf SSD.
Lizenzen CERN-OHL 1.2 / GPLv3 / CC-BY-NC, Reifegrad TRL 6. **Keine veröffentlichte Erkennung oder Klassifikation**, keine Durchsatzzahlen.
Bezug zu uns: gleiche Rechnerklasse (Pi 5 + USB-Kamera), aber Standbilder aus dem Durchfluss statt dauernder Beobachtung; keine
Verfolgung bewegter Tiere. Übernehmbar: die Bauform „Messkoffer mit Pumpe" für Probenbetrieb, nichts für die Live-Auswertung.

## 2. ARTiMiS (Gincley et al., Environ. Sci. Technol. 2024)
Quellen: https://www.biorxiv.org/content/10.1101/2024.02.27.582145v1.full , https://pmc.ncbi.nlm.nih.gov/articles/PMC11295125/ (PMC war
durch eine Browserprüfung gesperrt, Inhalt aus bioRxiv).
Mikroalgen-Durchflussmikroskop: zwei M12-Objektive in Umkehrstellung, 7,8-fach, Auflösung 1,55 µm, Pi-Kamera V2 (IMX219, 1,12 µm Pixel),
Raspberry Pi 4 (4 GB), Durchflusskanal 200 µm tief, programmierbares LED-Feld für Hell- und Dunkelfeld. Zwei Erkenner („Fast Detector"
für gleichförmige Objekte, „Segmenter" für komplexe Proben); Klassifikation Random Forest (98,5 % Chlorella/Scenedesmus, 85 % an
Feldproben) und CNN (97,9 % binär, > 90 % je Klasse bei fünf Klassen), 1500–2000 Lernobjekte je Klasse, 85:15 Aufteilung.
Nachweisgrenzen: LoB 2,7·10³, LoD 3,2·10³, LoQ ≈ 5·10³ Partikel/mL, Messbereich bis ≈ 10⁶ Zellen/mL (darüber Überlagerungen).
Falle: unscharfe Partikel erscheinen größer und werden falsch klassifiziert. Rechenzeit auf dem Pi: Minuten je Probe (Segmenter).
Bezug zu uns: Maßstab 1,55 µm/px gegen unsere 10,5 µm/px (Algen gegen 1-mm-Tiere), Standbilder statt 29 Bilder/s. Übernehmbar:
(a) **Klassifikator aus eigenen Bildausschnitten** mit 1500–2000 Beispielen je Klasse — unsere Farbwahrheit liefert sie (Tier / Krümel /
Druckkante), das ist der Weg B auf dem Jetson; (b) **Dunkelfeld-Beleuchtung** als Schalter, um durchscheinende Tiere vom schwarzen
Aufdruck zu trennen (billiger Versuch mit Ring-LED); (c) die Nachweisgrenzen-Methodik (Leerprobe, LoD, LoQ) für unsere Dichteangabe.

## 3. INVE Artemia Knowledge Hub: „How technology is redefining live food management" und SnappArt
Quellen: https://artemia.inveaquaculture.com/dont-fall-behind-stay-up-to-date-with-how-technology/ , https://artemia.inveaquaculture.com/snappart/ ,
https://aquaculturemag.com/2024/04/03/dont-fall-behind-stay-up-to-date-with-how-technology-redefining-live-food-management-in-the-hatchery/
Inhalt: SEP-Art (magnetisch beschichtete Zysten, Ernte ohne Chemie, bis 10 USD/kg Ersparnis, AutoMag: 5-t-Tank in unter einer Stunde) und
**SnappArt** (INVE mit Aris): „KI-gestützte" automatische Zählung von Artemia-Nauplien und Rotatorien, Module L-SENSE (Lebendfutter),
S-SENSE (Garnelenlarven), E-SENSE (Fischeier), „schnelle, präzise, konsistente" Zählung, Datenberichte. **Keine technischen Zahlen
veröffentlicht** (keine Kamera, kein Probenvolumen, keine Genauigkeit, keine Dauer, kein Preis).
Bezug zu uns: Das ist der Markt für ein Gerät wie unseres — Brutanlagen zählen Dichte und Qualität des Lebendfutters. SnappArt zählt in
einer entnommenen Probe; unser Aufbau beobachtet dauernd und misst zusätzlich Bewegung (Tempo 1,9 mm/s), Größe (0,95 mm) und Ruheverhalten.
Was uns fehlt und dort selbstverständlich ist: **Dichte je Milliliter** (braucht ein bekanntes Beobachtungsvolumen: Schichtdicke der
Kammer × Sichtfeld), **Lebend/Tot** (bewegt/ruhend über Minuten ist ein Ansatz) und ein Bericht je Charge (Schlupfverlauf über Stunden —
den Stundenzähler haben wir).

## 4. Wang & De Baets 2019: „Automated Artemia detection and length measurement using deep convolutional networks" (abstract64.pdf)

**Quelle:** Erweiterte Kurzfassung, 3 Seiten, Gang Wang und Bernard De Baets, KERMIT, Universität Gent, 2019, CC BY 4.0 (Tagungsband-Beitrag;
die Datei lag unter <Projektordner-auf-dem-PC>, geholt 17:08). Zwei Aufgaben an Stereomikroskop-Standbildern von Artemia:

| Aufgabe | Verfahren | Daten | Ergebnis |
|---|---|---|---|
| Erkennen und Zählen (Zysten, Nauplien) | „Marker-CNN": UNet schlägt Zielmarken vor (trennt benachbarte Tiere), ein CNN-Klassierer ordnet jede Marke Zyste/Nauplius/kein Ziel zu | Prüfbilder mit 1336 Zysten und 3335 Nauplien | Erkennungsgenauigkeit 99,6 % |
| Körperlänge | UNet zieht eine „Messlinie" entlang des gekrümmten Körpers, anisotrope Gauß-Kerne 2. Ordnung dünnen sie zur Mittellinie aus; Länge = Linienlänge | 250 Lernbilder, 100 Prüfbilder | mittlerer Betragsfehler 1,16 % |

Die Vollfassungen (Quellen 8 und 9 im Abstract, damals „under review") sind nach meiner Kenntnis 2020 in *Computers and Electronics in
Agriculture* (Längenmessung) und *Aquaculture* (Erkennen/Zählen) erschienen — nicht nachgeprüft, ohne Netzzugriff hier.

**Was das für unser Mikroskop bedeutet:**
- **Klassen:** Gent trennt Zysten von Nauplien. Unsere Lernseite kennt Tier/Korn/Maßstab; Zysten (runde braune Kugeln, ~250 µm) landen
  bei uns als „Korn". Sobald in seinen Proben Zysten vorkommen, lohnt eine vierte Klasse „Zyste" — die Schlupfrate (Nauplien je Zyste) ist
  genau die Kennzahl, die Gent mit 99,6 % zählt. Eine Klasse mehr kostet auf der Lernseite nur einen Knopf, im Training nichts.
- **Länge:** Gent misst entlang der Mittellinie des gekrümmten Körpers, nicht über einen Rahmen. Unsere YOLO-Größe ist die längste
  Rahmenseite mal µm/px (1,0–1,2 mm) — bei gekrümmten Tieren zu kurz, bei schräg liegenden zu lang. Die Auswertung 1.4 auf dem Pi nimmt
  die Ellipsen-Hauptachse der Maske (Länge-Median 987 µm). Der Gent-Weg lässt sich bei uns ohne neues Netz nachbauen: Maske im YOLO-Rahmen
  (Farbwahrheit), Skelett (cv2.ximgproc.thinning), Länge des längsten Skelettpfads. Das ist ein Jetson-Auftrag für später, geprüft gegen
  10 von Hand vermessene Tiere (Maßstab im Fokus, Kernforderung „Maßstab gilt nur im Fokus").
- **Datenmenge:** 250 Lernbilder reichten Gent für 1,16 % Längenfehler, ein Prüfsatz von 4671 Objekten für die Zählung. Unsere 52 Bilder
  (209 Tierrahmen) sind der Anfang; die 243 zurückgestellten Bilder bringen uns in Gents Größenordnung. Das stützt die kleinen Runden.
- **Echtzeit:** Marker-CNN ist zweistufig (UNet + CNN je Kandidat) und für Standbilder gedacht — kein Livebetrieb. YOLO auf dem Jetson ist
  das Echtzeit-Gegenstück (28 Bilder/s); Gents 99,6 % sind der Maßstab, an dem wir unsere Zählung auf Standbildern messen sollten:
  10 Bilder, von Hand gezählt, gegen /stand des Livedienstes.
- **Benchmark-Gedanke:** Gent prüft gegen von Hand gezählte Bilder. Dasselbe fehlt uns noch; die Lernseite liefert die Wahrheit gratis
  (geprüfte Rahmen = Handzählung). Ein Auftrag „Zählung YOLO gegen geprüfte Rahmen" ergibt Genauigkeit und Trefferquote je Klasse.

## Folgerungen für die nächsten Schritte
1. Weg B (Jetson, GPU): Klassifikator/YOLO mit eigenen Ausschnitten, 1500–2000 je Klasse; die Farbwahrheit liefert die Beispiele; so werden
   ruhende Tiere ohne Bewegungsmaske erkannt (Problem 4) und Krümel/Druckkanten getrennt (Geister).
2. Dunkelfeld als Versuch (Ring-LED seitlich), gemessen mit demselben Prüfer: Treffer über dem Aufdruck vorher/nachher.
3. Kennzahlen wie in der Brutanlage: Dichte je mL (Volumen kalibrieren), Größenverteilung, Aktivität (Anteil bewegt), Verlauf je Stunde.
4. abstract64.pdf nachreichen; dann Ergänzung dieses Blatts.

**Nachtrag 17:15 (abstract64.pdf ausgewertet):** Klasse „Zyste" vorsehen, sobald Zysten in den Proben sind; Länge entlang der Mittellinie (Skelett) statt Rahmenseite als späterer Jetson-Auftrag; Zählgenauigkeit auf 10 Standbildern gegen die geprüften Rahmen messen (Gent: 99,6 %).
