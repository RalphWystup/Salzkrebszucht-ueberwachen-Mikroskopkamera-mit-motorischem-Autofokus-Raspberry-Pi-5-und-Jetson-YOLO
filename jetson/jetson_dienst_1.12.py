#!/usr/bin/env python3
# 1.9 (06.11.2026, 15:55): Training ueber jetson_yolo_training_1.4 (ohne TensorRT-Export, der zweimal im Speicher hing).
# 1.10 (06.11.2026, 16:58): Trainingsstart dauerhaft gemerkt (lernen/TRAINING_START.json, Uhr der Fertig-Meldung) -- Befund 16:35: nach jedem
#     Dienstneustart war Z["training"]["gestartet"] leer, eine vorhandene FERTIG.json haette darum jedes Mal ein neues Training ausgeloest
#     (Livedienst 4 min angehalten, gleiches Modell). Dazu meldet /stand.yolo waehrend eines Trainings "pausiert: Training laeuft" statt
#     "nicht erreichbar" (die Trainingseinheit haelt den Livedienst an, jetson_yolo_einrichten_1.2.py). Sonst 1.9 unveraendert.
# 1.12 (07.11.2026, sein Wort: "kann man auch die anlernkurven von yolo darstellen? damit man den fortschritt sieht?"):
#     GET /yolo/verlauf liefert den Lernverlauf: je Trainingslauf die Kurve aus laeufe/<lauf>/results.csv
#     (mAP50, mAP50-95, Genauigkeit, Trefferquote je Epoche) und je Runde, mit wie vielen bewerteten Bildern
#     sie gerechnet wurde. Damit die Bilderzahl spaeter noch bekannt ist, schreibt der Dienst beim Start einer
#     Runde eine Zeile nach yolo/verlauf.json -- vorher ging sie verloren, weil modell/info.json jedes Mal
#     ueberschrieben wird.
# 1.11 (07.11.2026, sein Wort: "auch einen button alles gelernet zurücksetzen und eine anzeige was bereit"):
#     POST /lernen/zuruecksetzen setzt alle Lernbilder auf "offen" zurueck -- VORHER wird der vollstaendige Stand
#     (Status und Rahmen jedes Bildes) nach lernen/sicherung_<stamp>.json geschrieben, damit nichts verloren geht;
#     die gezeichneten Rahmen bleiben erhalten, das angelernte Modell wird nicht angefasst. Dazu nimmt das Speichern
#     jetzt auch den Stand "zurueckgestellt" an -- den gab es in den Daten, war aber ueber die Seite nicht setzbar.
# 1.8 (06.11.2026, 15:25, sein Wort: "erstelle die html so dass es einen fertig button gibt"): POST /lernen/fertig schreibt lernen/FERTIG.json;
#     der Takt startet daraufhin abgeloest Datensatz + Training (jetson_yolo_datensatz_1.0, jetson_yolo_training_1.2), wenn keins laeuft
#     (Stand in /stand unter training). Statistik (Vermessung ueber alle Saetze) nur noch alle STATISTIK_TAKT s, damit Auftraege nicht minutenlang warten.
# 1.7 (06.11.2026, 14:20, sein Wort: "du erstellst eine html auf der die krebse in bildern zu sehen [sind] um ein yolo modell damit anzulernen"):
#     Lernseite /lernen (lernen.html im Arbeitsordner), /lernen/liste, /lernen/bild/<name>.jpg, /lernen/boxen/<name> (GET, POST speichert
#     Rahmen und Stand geprueft/verworfen/offen nach lernen/bilder/<name>.json). Lernbilder erzeugt jetson_lernbilder_1.0.py als Auftrag.
# 1.6 (06.11.2026, 13:20): Auftragsbuch (auftraege/erledigt.json) beim Start in /stand uebernehmen -- nach einem Fassungswechsel zeigte der neue
#     Dienst 'erledigt 0, letzter None', und der Aufgeber im Arbeitsbereich wartete vergeblich auf den gerade erledigten Auftrag.
# 1.5 (06.11.2026, 13:05, Kernforderung 43 -- sein Wort: "alle alten videos die nicht mehr zum lernen benoetigt werden koennen ja geloescht
#     werden"): Aufraeumen je Takt -- Rohvideos (.avi, _rahmen.avi) geprueft er Saetze aelter als VIDEO_FRIST_H werden geloescht, bei weniger als
#     FREI_MIN_GB frei schon ab NOT_FRIST_H; Lernarchiv (jeder 10. Satz: Sekunde endet auf 0, dazu behalten.txt) behaelt seine Videos bis LERN_GB,
#     darueber verlieren die aeltesten automatischen Archivsaetze ihre Videos; Rahmen, Farbwahrheiten, Tafeln, Ausschnitte, Statistik bleiben immer;
#     jede Loeschung in aufraeumen.log; Stand in /stand unter platte. Dazu /datei: Schnappschuss je Datei fuer 300 s, damit sich eine Datei
#     (z. B. live_letztes.jpg) zwischen zwei Stuecken nicht aendert.
# 1.4 (06.11.2026, 12:20, sein Wort: "der jetson soll im livestream die bilder der usb mikroskop kamera sehen koennen", "der schnelle
#     datenaustausch muss gehen und zwar autonom"): liest den Livestrom des Pi (:8090/strom) DAUERND mit Wiederverbindung, haelt das letzte
#     Bild (/live.jpg, alle 5 s auch als live_letztes.jpg), zaehlt Bilder/s, Mbit/s und abgeschnittene Teile (/live, auch in /stand);
#     holt die Live-Daten der Auswertung (:8092/stand) alle 2 s (pi_live in /stand); Fassungswechsel ohne sudo: steht in
#     jetson_dienst_FASSUNG.txt eine andere Datei, endet der Dienst und systemd startet sie ueber jetson_dienst_lauf.py.
# 1.3 (06.11.2026, 12:30): Dateien stueckweise ueber HTTP (/dateien, /datei/<name>/<stueck>; die Bruecke kappt Antworten bei 60 000 Zeichen),
#     Auftraege vom Pi (halten/jetson_auftraege/*.py: jeder einmal, Ausgabe auftraege/<name>.aus.txt) -- damit braucht kein Aufruf mehr das
#     Jetson-Kennwort; geprueft = vorhandene Farbwahrheiten; tegrastats-Fehlen wird gemeldet statt den Faden zu toeten.
# 1.2 (06.11.2026, 11:05): vermessung_1.3 (flache Ablage), sonst wie 1.1
# -*- coding: utf-8 -*-
"""jetson_dienst_1.9.py -- 1.1 (06.11.2026, 10:30): Pi ueber den Namen "mikroskop" (Fritz!Box-DNS) mit Rueckfall auf
bekannte Adressen (Kabel/WLAN), neue Hostschluessel annehmen, rsync mit Zeitgrenze -- der Pi haengt seit heute am Kabel.

jetson_dienst_1.0.py -- Mikroskop-Dienst auf dem Jetson (06.11.2026). Holt Aufnahmesaetze per rsync vom Pi, prueft sie
(Farbwahrheit, Verfolgung) und rechnet die Statistik; meldet Zustand und Auslastung als JSON fuer die Seite.
Sein Wort: "in der html muss eine live anzeige fuer die Verbindung und die Arbeitsauslastung des jetsons. Ich moechte sehen
dass er arbeitet und wenn er da ist" und "so dass die Grundfunktionen der Rueckfalloption auch funktionieren wenn der
jetson nicht aktiv ist" -- der Pi braucht diesen Dienst nicht; die Seite zeigt ihn nur, wenn er antwortet.
  :8095/stand     Zustand, Auslastung (tegrastats), aktuelle Arbeit, letzte Statistik, Auftraege
  :8095/ergebnis  die ganze Statistik (JSON der vermessung)
  :8095/dateien   Dateien in ~/mikroskop (oben und auftraege/), Name/Bytes/Zeit
  :8095/live      Livestrom-Empfang: verbunden, Bilder/s, Mbit/s, abgeschnitten, letztes Bild vor s (1.4)
  :8095/live.jpg  das letzte vom Pi empfangene Bild (1.4)
  :8095/lernen    Bewertungsseite fuer YOLO-Lernbilder (1.7); /lernen/liste, /lernen/bild/<name>.jpg, /lernen/boxen/<name> (GET/POST)
  :8095/datei/<name>/<stueck>  Stueck i der base64-Kodierung (45 000 Zeichen) mit sha256 des Ganzen -- Abholer: jetson_datei_holen_1.0.py
  Auftraege: Pi:/home/pi/wache/halten/jetson_auftraege/<name>.py -> ~/mikroskop/auftraege/, einmal ausgefuehrt (python3 -u, Arbeitsordner
  ~/mikroskop, 30 min Grenze), Ausgabe auftraege/<name>.aus.txt, Buch erledigt.json -- Aufgeber: jetson_auftrag_1.0.py
Prüfung hier ohne Jetson: JETSON_HIER=<Ordner> JETSON_PI_HTTP=127.0.0.1 python3 jetson_dienst_1.9.py (tegrastats und SSH zum Pi fehlen dann;
HTTP geht, der Livestrom kommt vom Stellvertreter pruefmittel/stub8090.py auf 127.0.0.1:8090).
"""
import os, sys, time, json, threading, subprocess, glob, re, http.server, socketserver, collections, base64, hashlib, urllib.request
PORT = 8095; PI_ABLAGE = "/home/pi/wache/aufnahmen"; PI_AUFTRAEGE = "/home/pi/wache/halten/jetson_auftraege"; STUECK = 45000
PI_KANDIDATEN = ["mikroskop", "<IP-des-Pi-Kabel>", "<IP-des-Pi>"]   # Name zuerst (DNS der Fritz!Box), dann Kabel, dann WLAN
SSH = "ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new"
PI = None
VIDEO_FRIST_H, NOT_FRIST_H, FREI_MIN_GB, LERN_GB = 3.0, 1.0, 10.0, 6.0   # 1.5: Aufraeumregel (Kernforderung 43)
SCHNAPPSCHUSS = {}                                      # 1.5: /datei: name -> (roh, sha256, zeit)
PI_HTTP = os.environ.get("JETSON_PI_HTTP")             # Pruefung hier: Rechner des Stellvertreters (127.0.0.1); sonst der Pi
LIVE = {"bytes": b"", "zeit": 0.0, "gesichert": 0.0}    # letztes vollstaendiges Bild vom Pi und seine Ankunftszeit
HIER = os.environ.get("JETSON_HIER") or os.path.expanduser("~/mikroskop"); ABLAGE = os.path.join(HIER, "aufnahmen"); AUFTRAEGE = os.path.join(HIER, "auftraege")
os.makedirs(ABLAGE, exist_ok=True); os.makedirs(AUFTRAEGE, exist_ok=True)
TAKT = 60; STATISTIK_TAKT = 300
Z = {"fassung": "1.12", "pi": None, "seit": time.time(), "auftrag": "start", "letzter_rsync": None, "letzter_fehler": None, "saetze": 0,
     "neue_saetze": 0, "geprueft": 0, "statistik": None, "verfolgung": None, "cpu": None, "gpu": None, "ram": None, "temp": None,
     "platte_frei_gb": None, "uhr": None, "auftraege": {"erledigt": 0, "letzter": None, "rc": None, "ende": None, "laeuft": None},
     "live": {"verbunden": False, "pi": None, "seit": None, "bilder": 0, "abgeschnitten": 0, "neuverbindungen": 0, "bilder_je_s": 0.0, "mbit_je_s": 0.0,
              "letztes_bild": None, "bild_kb": None, "fehler": None}, "pi_live": None,
     "training": {"angefordert": None, "gestartet": None, "laeuft": False, "letzte_runde": None}, "statistik_uhr": 0.0, "yolo": None,
     "platte": {"videos_gb": None, "lernarchiv_gb": None, "lernarchiv_saetze": None, "geloescht_saetze": 0, "geloescht_gb": 0.0, "letztes": None, "frei_gb": None, "regel": f"Videos nach {VIDEO_FRIST_H:.0f} h, bei < {FREI_MIN_GB:.0f} GB frei nach {NOT_FRIST_H:.0f} h; Lernarchiv jeder 10. Satz + behalten.txt bis {LERN_GB:.0f} GB"}}
sperre = threading.Lock()
def log(s): print(time.strftime("%H:%M:%S "), s, flush=True)
def sh(c, t=600):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t); return r.stdout, r.stderr, r.returncode


def tegrastats():
    """CPU-, GPU-, RAM- und Temperaturwerte aus tegrastats, eine Zeile je Sekunde."""
    try: p = subprocess.Popen(["tegrastats", "--interval", "1000"], stdout=subprocess.PIPE, text=True)
    except FileNotFoundError: log("tegrastats fehlt (kein Jetson?) -- keine Auslastungswerte"); return
    for zeile in p.stdout:
        try:
            m_cpu = re.findall(r"(\d+)%@\d+", zeile); m_gpu = re.search(r"GR3D_FREQ (\d+)%", zeile)
            m_ram = re.search(r"RAM (\d+)/(\d+)MB", zeile); m_t = re.search(r"cpu@([\d.]+)C", zeile)
            with sperre:
                if m_cpu: Z["cpu"] = round(sum(map(int, m_cpu)) / len(m_cpu))
                if m_gpu: Z["gpu"] = int(m_gpu.group(1))
                if m_ram: Z["ram"] = f"{int(m_ram.group(1))/1024:.1f}/{int(m_ram.group(2))/1024:.1f} GB"
                if m_t: Z["temp"] = float(m_t.group(1))
                Z["uhr"] = time.strftime("%H:%M:%S")
        except Exception: pass


def setze(**k):
    with sperre: Z.update(k)


def pi_finden():
    global PI
    for k in ([PI] if PI else []) + PI_KANDIDATEN:
        if not k: continue
        ziel = k if "@" in k else "<pi-benutzer>@" + k
        aus, err, rc = sh(f"{SSH} {ziel} hostname", 20)
        if rc == 0 and "mikroskop" in aus: PI = ziel; setze(pi=ziel); return ziel
    raise RuntimeError("Pi nicht erreichbar unter " + ", ".join(PI_KANDIDATEN))


def holen():
    """Nur vollstaendige Saetze (mit Rahmendatei) vom Pi, die hier noch fehlen."""
    ziel = pi_finden()
    aus, err, rc = sh(f"{SSH} {ziel} 'ls {PI_ABLAGE}/*.jsonl 2>/dev/null'", 30)
    if rc != 0: raise RuntimeError("Pi nicht erreichbar: " + err.strip()[-120:])
    namen = sorted(os.path.basename(p)[:-6] for p in aus.split())
    neu = [n for n in namen if not os.path.exists(os.path.join(ABLAGE, n + ".jsonl"))]
    if neu:
        liste = os.path.join(HIER, "holliste.txt")
        with open(liste, "w") as f:
            for n in neu:
                for t in (".jsonl", ".avi", "_rahmen.avi", "_tafel.jpg", "_ausschnitte.jpg"): f.write(n + t + "\n")
        aus, err, rc = sh(f"rsync -a --timeout=60 --ignore-missing-args -e '{SSH}' --files-from={liste} {ziel}:{PI_ABLAGE}/ {ABLAGE}/", 900)
        if rc not in (0, 24): raise RuntimeError("rsync: " + err.strip()[-120:])
    return neu


def pruefen(neu):
    """Farbwahrheit und Verfolgungspruefung je neuem Satz (Werkzeuge aus dem Projekt)."""
    for n in neu:
        stamm = os.path.join(ABLAGE, n)
        if os.path.exists(stamm + ".avi") and not os.path.exists(stamm + "_farbe.jsonl"):
            sh(f"cd {HIER} && python3 tiere_nach_farbe_1_6.py {stamm} > /dev/null 2>&1", 300)


def verfolgung_gesamt():
    dateien = sorted(glob.glob(os.path.join(ABLAGE, "*.jsonl"))); dateien = [d for d in dateien if not d.endswith("_farbe.jsonl")][-40:]
    if not dateien: return None
    aus, _, _ = sh(f"cd {HIER} && python3 verfolgung_pruefen_1.1.py " + " ".join(dateien) + " 2>/dev/null | grep '^GESAMT'", 600)
    m = re.search(r"Tiere (\d+), getroffen (\d+) = (\d+) %; Bahnen (\d+); Nummernwechsel (\d+) von (\d+) = ([\d.]+) %", aus)
    return {"saetze": len(dateien), "tiere": int(m.group(1)), "getroffen_prozent": int(m.group(3)), "bahnen": int(m.group(4)), "wechsel_prozent": float(m.group(7))} if m else None


def statistik():
    aus, _, _ = sh(f"cd {HIER} && python3 vermessung_1.3.py {ABLAGE} 2>/dev/null", 600)
    try:
        j = json.load(open(sorted(glob.glob(os.path.join(HIER, "vermessung_*.json")))[-1]))
        bahnen = [b for s in j["saetze"] for b in s["bahnen"]]
        import statistics as st
        L = [b["laenge_um"] for b in bahnen]; V = [b["tempo_mm_s"] for b in bahnen if b["tempo_mm_s"] is not None]
        tjb = j.get("tiere_je_bild", {}); n_b = sum(tjb.values()); mittel = sum(int(k) * v for k, v in tjb.items()) / max(n_b, 1)
        return {"saetze": len(j["saetze"]), "bilder": n_b, "bahnen": len(bahnen), "laenge_um_median": round(st.median(L)) if L else None,
                "tempo_mm_s_median": round(st.median(V), 2) if V else None, "tiere_je_bild": round(mittel, 2), "stand": j.get("stand")}
    except Exception as e:
        return {"fehler": str(e)[:80]}


def auftraege_holen(ziel):
    """Auftragsskripte vom Pi (der Ordner darf dort fehlen)."""
    sh(f"rsync -a --timeout=60 -e '{SSH}' --include='*.py' --exclude='*' {ziel}:{PI_AUFTRAEGE}/ {AUFTRAEGE}/ 2>/dev/null", 120)


def auftraege_ausfuehren():
    """Jedes Skript in auftraege/ genau einmal: python3 -u im Arbeitsordner ~/mikroskop, Ausgabe <name>.aus.txt, Buch erledigt.json."""
    buch = os.path.join(AUFTRAEGE, "erledigt.json")
    try: erledigt = json.load(open(buch))
    except Exception: erledigt = {}
    for p in sorted(glob.glob(os.path.join(AUFTRAEGE, "*.py"))):
        n = os.path.basename(p)
        if n in erledigt: continue
        with sperre: Z["auftrag"] = f"Auftrag {n}"; Z["auftraege"]["laeuft"] = n
        t0 = time.strftime("%H:%M:%S"); aus = os.path.join(AUFTRAEGE, n[:-3] + ".aus.txt")
        try: rc = subprocess.run(f"python3 -u {p} > {aus} 2>&1", shell=True, cwd=HIER, timeout=1800).returncode
        except subprocess.TimeoutExpired: rc = -9; open(aus, "a").write("\nABGEBROCHEN nach 1800 s\n")
        erledigt[n] = {"start": t0, "ende": time.strftime("%H:%M:%S"), "rc": rc}; json.dump(erledigt, open(buch, "w"), indent=1)
        with sperre: Z["auftraege"].update(erledigt=len(erledigt), letzter=n, rc=rc, ende=erledigt[n]["ende"], laeuft=None)
        log(f"Auftrag {n}: rc {rc}")


def pi_http():
    """Rechnername des Pi fuer HTTP: Stellvertreter aus der Umgebung, sonst der per SSH gefundene Pi, sonst die Kandidaten der Reihe nach."""
    if PI_HTTP: return PI_HTTP
    if PI: return PI.split("@")[-1]
    for k in PI_KANDIDATEN:
        try: urllib.request.urlopen(f"http://{k}:8090/status", timeout=3).read(); return k
        except Exception: pass
    return None


def live_lesen():
    """1.4: Liest den Livestrom des Pi (:8090/strom, MJPEG) dauernd, haelt das letzte Bild, zaehlt Bilder/s, Mbit/s und abgeschnittene
    Teile (jedes Teil muss mit FF D9 enden und so lang sein wie sein Content-Length -- Lehre "MJPEG-Leser: Streifen") und verbindet
    nach jedem Abriss von selbst neu (2 s ... 30 s). Alle 5 s liegt das letzte Bild als live_letztes.jpg im Arbeitsordner."""
    L = Z["live"]; pause = 2.0
    while True:
        host = pi_http()
        if not host:
            with sperre: L.update(verbunden=False, fehler="Pi nicht erreichbar", bilder_je_s=0.0, mbit_je_s=0.0)
            time.sleep(pause); pause = min(pause * 2, 30); continue
        try:
            r = urllib.request.urlopen(f"http://{host}:8090/strom", timeout=10)
            with sperre: L.update(verbunden=True, pi=host, seit=time.strftime("%H:%M:%S"), fehler=None); L["neuverbindungen"] += 1
            pause = 2.0; puffer = b""; grenze = None; fenster = collections.deque(); groessen = collections.deque()
            while True:
                teil = r.read(65536)
                if not teil: raise ConnectionError("Strom zu Ende")
                puffer += teil; jetzt = time.time()
                if grenze is None:
                    m = re.search(rb"--([A-Za-z0-9_-]+)\r?\n", puffer)
                    if m: grenze = b"--" + m.group(1)
                    elif len(puffer) > 1_000_000: raise ValueError("keine Teilegrenze im Strom")
                    else: continue
                while True:
                    a = puffer.find(grenze)
                    if a < 0: break
                    b = puffer.find(grenze, a + len(grenze))
                    if b < 0: break
                    stueck = puffer[a + len(grenze):b]; puffer = puffer[b:]
                    k = stueck.find(b"\r\n\r\n")
                    if k < 0: continue
                    kopf = stueck[:k]; koerper = stueck[k + 4:].rstrip(b"\r\n")
                    cl = re.search(rb"Content-Length:\s*(\d+)", kopf, re.I); soll = int(cl.group(1)) if cl else None
                    ganz = koerper.endswith(b"\xff\xd9") and (soll is None or len(koerper) == soll)
                    if ganz: fenster.append(jetzt); groessen.append((jetzt, len(koerper)))
                    while fenster and jetzt - fenster[0] > 5: fenster.popleft()
                    while groessen and jetzt - groessen[0][0] > 5: groessen.popleft()
                    with sperre:
                        L["bilder"] += 1
                        if ganz: LIVE["bytes"] = koerper; LIVE["zeit"] = jetzt; L["letztes_bild"] = time.strftime("%H:%M:%S", time.localtime(jetzt)); L["bild_kb"] = round(len(koerper) / 1024, 1)
                        else: L["abgeschnitten"] += 1
                        L["bilder_je_s"] = round(len(fenster) / 5, 1); L["mbit_je_s"] = round(sum(n for _, n in groessen) * 8 / 5 / 1e6, 2)
                if jetzt - LIVE["gesichert"] > 5 and LIVE["bytes"]:
                    tmp = os.path.join(HIER, "live_letztes.jpg.tmp"); open(tmp, "wb").write(LIVE["bytes"]); os.replace(tmp, os.path.join(HIER, "live_letztes.jpg")); LIVE["gesichert"] = jetzt
        except Exception as e:
            with sperre: L.update(verbunden=False, fehler=str(e)[:80], bilder_je_s=0.0, mbit_je_s=0.0)
            log(f"Livestrom: {e} -- neuer Versuch in {pause:.0f} s"); time.sleep(pause); pause = min(pause * 2, 30)


def pi_live_lesen():
    """1.4: Live-Daten der Auswertung (:8092/stand) alle 2 s -- der schnelle Datenaustausch neben dem Bildstrom."""
    while True:
        host = pi_http()
        try:
            a = json.load(urllib.request.urlopen(f"http://{host}:8092/stand", timeout=5))
            with sperre: Z["pi_live"] = {k: a.get(k) for k in ("fassung", "bilder_s", "kaputt", "laeuft_min")} | {"pi": host, "uhr": time.strftime("%H:%M:%S")}
        except Exception as e:
            with sperre: Z["pi_live"] = {"fehler": str(e)[:80], "uhr": time.strftime("%H:%M:%S")}
        time.sleep(2)


def yolo_lesen():
    """1.8: Zahlen des YOLO-Livedienstes (:8096/stand) alle 2 s -- fuer die Pi-Seite, die nur den Jetson-Dienst abfragt."""
    while True:
        try:
            y = json.load(urllib.request.urlopen("http://127.0.0.1:8096/stand", timeout=3))
            with sperre: Z["yolo"] = {k: y.get(k) for k in ("fassung", "modell", "phase", "tiere", "tiere_mittel_5s", "bewegt", "ruhend", "koerner", "groesse_mm_median", "tempo_mm_s_median", "bilder_s", "verarbeitet_s", "laeuft_min", "fehler")} | {"uhr": time.strftime("%H:%M:%S")}
        except Exception as e:
            ph = "pausiert: Training laeuft" if training_laeuft() else "nicht erreichbar"           # 1.10
            with sperre: Z["yolo"] = {"phase": ph, "fehler": None if ph.startswith("pausiert") else str(e)[:60], "uhr": time.strftime("%H:%M:%S")}
        time.sleep(2)


def fassung_wache():
    """1.4: Steht in jetson_dienst_FASSUNG.txt ein anderer Dateiname als dieser und wurde der Dienst ueber jetson_dienst_lauf.py
    gestartet (JETSON_LAUF=1), endet der Dienst; systemd (Restart=always) startet ueber den Starter die genannte Fassung --
    Wechsel und Rueckfall ohne sudo, als Auftrag vom Pi."""
    if os.environ.get("JETSON_LAUF") != "1": return
    eigen = os.path.basename(__file__); f = os.path.join(HIER, "jetson_dienst_FASSUNG.txt")
    while True:
        time.sleep(10)
        try: soll = open(f).read().strip()
        except Exception: continue
        if soll and soll != eigen and os.path.isfile(os.path.join(HIER, soll)):
            log(f"Fassungswechsel {eigen} -> {soll} (jetson_dienst_FASSUNG.txt): Dienst endet, systemd startet neu"); sys.stdout.flush(); os._exit(0)


def satz_zeit(name):
    """Aufnahmezeit aus dem Satznamen JJJJMMTT_HHMMSS (Ortszeit); sonst None."""
    try: return time.mktime(time.strptime(name[:15], "%Y%m%d_%H%M%S"))
    except Exception: return None


def frei_gb():
    aus, _, _ = sh("df -BM --output=avail ~ | tail -1", 5)
    try: return int(aus.strip().rstrip("M")) / 1024
    except Exception: return None


def aufraeumen(jetzt=None, frei=None, lern_gb=None, protokoll=True):
    """1.5: Rohvideos alter, geprüfter Sätze löschen (Kernforderung 43). Nie: Rahmen, Farbwahrheiten, Tafeln, Ausschnitte, Statistik.
    Lernarchiv: Sätze, deren Sekunde auf 0 endet (jeder 10.), und Namen in behalten.txt -- deren Videos bleiben; übersteigen die
    automatischen Archivsätze LERN_GB, verlieren die ältesten von ihnen ihre Videos (behalten.txt zählt nicht mit und wird nie gelöscht). Liefert den Plattenstand für /stand."""
    jetzt = jetzt or time.time(); frei = frei_gb() if frei is None else frei; lern_gb = LERN_GB if lern_gb is None else lern_gb
    try: behalten = {z.strip() for z in open(os.path.join(HIER, "behalten.txt"), encoding="utf-8") if z.strip() and not z.startswith("#")}
    except Exception: behalten = set()
    saetze = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(ABLAGE, "*.jsonl")) if not p.endswith("_farbe.jsonl"))
    def videos(n): return [p for p in (os.path.join(ABLAGE, n + ".avi"), os.path.join(ABLAGE, n + "_rahmen.avi")) if os.path.exists(p)]
    def groesse(n): return sum(os.path.getsize(p) for p in videos(n))
    frist_h = NOT_FRIST_H if (frei is not None and frei < FREI_MIN_GB) else VIDEO_FRIST_H
    archiv = [n for n in saetze if (n in behalten or n[14:15] == "0") and videos(n)]
    archiv_bytes = sum(groesse(n) for n in archiv if n not in behalten)       # Grenze nur fuer die automatischen Lernsaetze; behalten.txt zaehlt nicht
    geloescht = []
    for n in archiv:                                            # Lernarchiv über der Obergrenze: älteste automatische zuerst
        if archiv_bytes <= lern_gb * 1e9: break
        if n in behalten: continue
        g = groesse(n); [os.remove(p) for p in videos(n)]; archiv_bytes -= g; geloescht.append((n, "Lernarchiv ueber Grenze", g))
    for n in saetze:
        if n in behalten or n[14:15] == "0": continue
        t = satz_zeit(n)
        if t is None or jetzt - t < frist_h * 3600: continue
        if not os.path.exists(os.path.join(ABLAGE, n + "_farbe.jsonl")): continue      # erst nach der Prüfung
        vs = videos(n)
        if not vs: continue
        g = groesse(n); [os.remove(p) for p in vs]; geloescht.append((n, f"aelter als {frist_h:.0f} h", g))
    if geloescht and protokoll:
        with open(os.path.join(HIER, "aufraeumen.log"), "a", encoding="utf-8") as f:
            for n, grund, g in geloescht: f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {n} {grund} {g} Byte\n")
    video_bytes = sum(groesse(n) for n in saetze); archiv = [n for n in saetze if (n in behalten or n[14:15] == "0") and videos(n)]
    with sperre:
        P = Z["platte"]; P["videos_gb"] = round(video_bytes / 1e9, 2); P["lernarchiv_gb"] = round(sum(groesse(n) for n in archiv) / 1e9, 2); P["lernarchiv_saetze"] = len(archiv)
        P["geloescht_saetze"] += len(geloescht); P["geloescht_gb"] = round(P["geloescht_gb"] + sum(g for _, _, g in geloescht) / 1e9, 2)
        if geloescht: P["letztes"] = time.strftime("%H:%M:%S") + f" {len(geloescht)} Saetze"
        P["frei_gb"] = None if frei is None else round(frei, 1)
    if geloescht: log(f"Aufraeumen: {len(geloescht)} Saetze ohne Videos ({sum(g for _, _, g in geloescht)/1e9:.2f} GB), Frist {frist_h:.0f} h, frei {frei}")
    return geloescht


LERNEN = os.path.join(HIER, "lernen", "bilder")


def lern_name_ok(name): return bool(re.fullmatch(r"[A-Za-z0-9_]+", name or ""))


def training_laeuft(): return subprocess.run("systemctl is-active mikroskop-training", shell=True, capture_output=True, text=True).stdout.strip() in ("active", "activating")   # 1.8: eigene Einheit


def training_pruefen():
    """1.8: nach einer Fertig-Meldung (lernen/FERTIG.json neuer als der letzte Start) Datensatz bauen und Training abgeloest starten."""
    f = os.path.join(HIER, "lernen", "FERTIG.json")
    if not os.path.exists(f): return
    try: d = json.load(open(f, encoding="utf-8"))
    except Exception: return
    start_f = os.path.join(HIER, "lernen", "TRAINING_START.json")
    with sperre: T = Z["training"]; T["angefordert"] = d.get("uhr"); T["laeuft"] = training_laeuft()
    if T["gestartet"] is None and os.path.exists(start_f):                        # 1.10: letzten Start aus der Datei (Dienstneustart)
        try: T["gestartet"] = json.load(open(start_f, encoding="utf-8")).get("uhr")
        except Exception: pass
    if T["gestartet"] == d.get("uhr") or T["laeuft"]: return
    json.dump({"uhr": d.get("uhr"), "start": time.strftime("%Y-%m-%d %H:%M:%S")}, open(start_f, "w", encoding="utf-8"))   # 1.10
    aus, err, rc = sh(f"cd {HIER} && python3 jetson_yolo_datensatz_1.1.py", 600); log("Datensatz: " + aus.strip()[-200:])
    try:                                                                          # 1.12: Runde im Verlauf festhalten
        ds = json.loads(aus[aus.index("DATENSATZJSON") + 13:].strip()) if "DATENSATZJSON" in aus else {}
        vp = os.path.join(HIER, "yolo", "verlauf.json")
        try: v = json.load(open(vp, encoding="utf-8"))
        except Exception: v = []
        v.append({"uhr": time.strftime("%Y-%m-%d %H:%M:%S"), "runde_angefordert": d.get("uhr"),
                  "staende": d.get("staende", {}), "datensatz": ds})
        os.makedirs(os.path.dirname(vp), exist_ok=True); json.dump(v[-200:], open(vp, "w", encoding="utf-8"), indent=1)
    except Exception as e: log(f"Verlauf nicht geschrieben: {e}")
    aus2, err2, rc2 = sh(f"cd {HIER} && python3 jetson_yolo_training_1.4.py", 120); log("Training: " + (aus2 + err2).strip()[-200:])
    with sperre: T["gestartet"] = d.get("uhr"); T["laeuft"] = True; T["letzte_runde"] = d


def yolo_verlauf():
    """1.12: Lernverlauf fuer die Anzeige. Je Trainingslauf die Kurve aus results.csv (das schreibt ultralytics
    Zeile fuer Zeile waehrend des Trainings -- die Kurve ist also auch WAEHREND eines Laufs schon zu sehen),
    dazu die Runde aus verlauf.json (wie viele bewertete Bilder, welche Staende)."""
    Y = os.path.join(HIER, "yolo")
    try: runden = json.load(open(os.path.join(Y, "verlauf.json"), encoding="utf-8"))
    except Exception: runden = []
    laeufe = []
    for d in sorted(glob.glob(os.path.join(Y, "laeufe", "lauf_*"))):
        csv = os.path.join(d, "results.csv")
        if not os.path.isfile(csv): continue
        try:
            zeilen = [z.strip() for z in open(csv, encoding="utf-8") if z.strip()]
            if len(zeilen) < 2: continue
            kopf = [s.strip() for s in zeilen[0].split(",")]
            def spalte(teil):
                for i, s in enumerate(kopf):
                    if teil in s: return i
                return None
            i_e, i_m50, i_m95 = spalte("epoch"), spalte("mAP50(B)"), spalte("mAP50-95(B)")
            i_p, i_r = spalte("precision(B)"), spalte("recall(B)")
            def hol(w, i):
                try: return round(float(w[i]), 4) if i is not None and i < len(w) else None
                except Exception: return None
            kurve = []
            for z in zeilen[1:]:
                w = [s.strip() for s in z.split(",")]
                kurve.append({"epoche": hol(w, i_e), "mAP50": hol(w, i_m50), "mAP50_95": hol(w, i_m95),
                              "genauigkeit": hol(w, i_p), "trefferquote": hol(w, i_r)})
            letzte = kurve[-1] if kurve else {}
            laeufe.append({"lauf": os.path.basename(d), "epochen": len(kurve),
                           "uhr": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(csv))),
                           "mAP50": letzte.get("mAP50"), "mAP50_95": letzte.get("mAP50_95"),
                           "kurve": kurve})
        except Exception as e:
            laeufe.append({"lauf": os.path.basename(d), "fehler": str(e)[:100]})
    try: info = json.load(open(os.path.join(Y, "modell", "info.json"), encoding="utf-8"))
    except Exception: info = {}
    return {"laeufe": laeufe, "runden": runden, "modell": info, "laeuft": training_laeuft()}


def lern_liste():
    aus = []
    for p in sorted(glob.glob(os.path.join(LERNEN, "*.json"))):
        try: d = json.load(open(p, encoding="utf-8")); aus.append({"name": os.path.basename(p)[:-5], "status": d.get("status", "offen"), "n_boxen": len(d.get("boxen", []))})
        except Exception: aus.append({"name": os.path.basename(p)[:-5], "status": "kaputt", "n_boxen": 0})
    return aus


def datei_pfad(name):
    """Nur Dateien unter ~/mikroskop (oben oder auftraege/), keine Pfadspruenge."""
    if not name or name.startswith(("/", ".")) or ".." in name or "\\" in name: return None
    p = os.path.realpath(os.path.join(HIER, name))
    return p if p.startswith(os.path.realpath(HIER) + os.sep) and os.path.isfile(p) else None


def arbeit():
    while True:
        try:
            setze(auftrag="hole Saetze vom Pi (rsync)"); neu = holen()
            setze(letzter_rsync=time.strftime("%H:%M:%S"), neue_saetze=len(neu), saetze=len([p for p in glob.glob(os.path.join(ABLAGE, "*.jsonl")) if not p.endswith("_farbe.jsonl")]))
            setze(auftrag="hole Auftraege vom Pi"); auftraege_holen(PI); auftraege_ausfuehren()
            setze(auftrag="raeume Videos auf"); aufraeumen()                      # 1.5
            setze(auftrag="Training pruefen"); training_pruefen()                 # 1.8
            if neu:
                setze(auftrag=f"pruefe {len(neu)} Saetze (Farbwahrheit)"); pruefen(neu)
                setze(geprueft=len(glob.glob(os.path.join(ABLAGE, "*_farbe.jsonl"))))
                setze(auftrag="Verfolgungspruefung"); setze(verfolgung=verfolgung_gesamt())
                if time.time() - Z["statistik_uhr"] >= STATISTIK_TAKT:             # 1.8: nicht in jedem Takt
                    setze(auftrag="Statistik (Vermessung)"); setze(statistik=statistik(), statistik_uhr=time.time())
            setze(auftrag="wartet", letzter_fehler=None)
        except Exception as e:
            setze(auftrag="Fehler", letzter_fehler=str(e)[:160]); log(f"Fehler: {e}")
            try: auftraege_ausfuehren()                      # 1.3: schon geholte Auftraege laufen auch, wenn der Pi gerade fehlt
            except Exception as e2: log(f"Auftraege: {e2}")
        time.sleep(TAKT)


class Auskunft(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, d):
        b = json.dumps(d).encode(); self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _roh(self, b, typ):
        self.send_response(200); self.send_header("Content-Type", typ); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_POST(self):                                                     # 1.7: Rahmen und Stand eines Lernbilds speichern
        p = self.path.split("?")[0]
        if p == "/lernen/fertig":                                          # 1.8: Bewertungsrunde abgeschlossen -> FERTIG.json, Training im naechsten Takt
            try:
                liste = lern_liste(); z = {}
                for e in liste: z[e["status"]] = z.get(e["status"], 0) + 1
                d = {"uhr": time.strftime("%Y-%m-%d %H:%M:%S"), "staende": z}; json.dump(d, open(os.path.join(HIER, "lernen", "FERTIG.json"), "w", encoding="utf-8"))
                laeuft = training_laeuft(); self._json({"ok": True, "uhr": d["uhr"][11:], "staende": z, "training": not laeuft, "grund": "ein Training laeuft noch" if laeuft else None})
            except Exception as e: self._json({"ok": False, "fehler": str(e)[:120]})
        elif p == "/lernen/zuruecksetzen":                                 # 1.11: alle Bewertungen zurueck auf "offen", mit Sicherung
            try:
                stand = {}; 
                for pj in sorted(glob.glob(os.path.join(LERNEN, "*.json"))):
                    try: stand[os.path.basename(pj)[:-5]] = json.load(open(pj, encoding="utf-8"))
                    except Exception: pass
                stamp = time.strftime("%Y%m%d_%H%M%S")
                sich = os.path.join(HIER, "lernen", f"sicherung_{stamp}.json")
                json.dump({"uhr": time.strftime("%Y-%m-%d %H:%M:%S"), "bilder": stand}, open(sich, "w", encoding="utf-8"))
                n = 0
                for name, d in stand.items():
                    if d.get("status") == "offen": continue
                    d2 = dict(d); d2["status"] = "offen"; d2.pop("geprueft_uhr", None)
                    pf = os.path.join(LERNEN, name + ".json"); tmp = pf + ".tmp"
                    json.dump(d2, open(tmp, "w", encoding="utf-8")); os.replace(tmp, pf); n += 1
                log(f"Lernstand zurueckgesetzt: {n} Bilder, Sicherung {os.path.basename(sich)}")
                self._json({"ok": True, "zurueckgesetzt": n, "gesamt": len(stand), "sicherung": os.path.basename(sich)})
            except Exception as e: self._json({"ok": False, "fehler": str(e)[:160]})
        elif p.startswith("/lernen/boxen/") and lern_name_ok(p[14:]):
            name = p[14:]; pf = os.path.join(LERNEN, name + ".json")
            try:
                n = int(self.headers.get("Content-Length") or 0); neu = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
                d = json.load(open(pf, encoding="utf-8")) if os.path.exists(pf) else {}
                boxen = [{"x0": int(b["x0"]), "y0": int(b["y0"]), "x1": int(b["x1"]), "y1": int(b["y1"]), "quelle": str(b.get("quelle", "hand"))[:12], "klasse": (b.get("klasse") if b.get("klasse") in ("tier", "korn", "massstab") else "tier")} for b in neu.get("boxen", []) if b["x1"] > b["x0"] and b["y1"] > b["y0"]]
                status = neu.get("status") if neu.get("status") in ("offen", "geprueft", "verworfen", "zurueckgestellt") else d.get("status", "offen")   # 1.11: zurueckstellen moeglich
                d.update(boxen=boxen, status=status, geprueft_uhr=time.strftime("%H:%M:%S")); tmp = pf + ".tmp"; json.dump(d, open(tmp, "w", encoding="utf-8")); os.replace(tmp, pf)
                self._json({"ok": True, "name": name, "status": status, "n_boxen": len(boxen)})
            except Exception as e: self._json({"ok": False, "fehler": str(e)[:120]})
        else: self.send_response(404); self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/lernen":                                                 # 1.7: Lernseite
            try: self._roh(open(os.path.join(HIER, "lernen.html"), "rb").read(), "text/html; charset=utf-8")
            except Exception: self._roh(b"lernen.html fehlt im Arbeitsordner", "text/plain; charset=utf-8")
        elif p == "/yolo/verlauf": self._json(yolo_verlauf())                   # 1.12: Lernkurven
        elif p == "/lernen/liste": self._json(lern_liste())
        elif p == "/favicon.ico": self.send_response(204); self.end_headers()
        elif p.startswith("/lernen/bild/") and p.endswith(".jpg") and lern_name_ok(p[13:-4]):
            pf = os.path.join(LERNEN, p[13:])
            if os.path.isfile(pf): self._roh(open(pf, "rb").read(), "image/jpeg")
            else: self.send_response(404); self.end_headers()
        elif p.startswith("/lernen/boxen/") and lern_name_ok(p[14:]):
            pf = os.path.join(LERNEN, p[14:] + ".json")
            try: self._json(json.load(open(pf, encoding="utf-8")))
            except Exception as e: self._json({"fehler": str(e)[:120]})
        elif p in ("/", "/stand"):
            with sperre: d = json.loads(json.dumps(Z))
            d["laeuft_min"] = round((time.time() - Z["seit"]) / 60, 1); aus, _, _ = sh("df -BG --output=avail ~ | tail -1", 5); d["platte_frei_gb"] = int(aus.strip().rstrip("G") or 0)
            d["live"]["letztes_bild_vor_s"] = round(time.time() - LIVE["zeit"], 1) if LIVE["zeit"] else None
            self._json(d)
        elif p == "/live":
            with sperre: d = dict(Z["live"])
            d["letztes_bild_vor_s"] = round(time.time() - LIVE["zeit"], 1) if LIVE["zeit"] else None; self._json(d)
        elif p == "/live.jpg":
            with sperre: b = LIVE["bytes"]
            if not b: self.send_response(503); self.end_headers(); return
            self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif p == "/ergebnis":
            try: self._json(json.load(open(sorted(glob.glob(os.path.join(HIER, "vermessung_*.json")))[-1])))
            except Exception as e: self._json({"fehler": str(e)})
        elif p == "/dateien":
            ds = sorted(glob.glob(os.path.join(HIER, "*")) + glob.glob(os.path.join(AUFTRAEGE, "*")))
            self._json([{"name": os.path.relpath(d, HIER), "bytes": os.path.getsize(d), "zeit": time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(d)))} for d in ds if os.path.isfile(d)])
        elif p.startswith("/datei/"):
            teile = p[7:].rsplit("/", 1); name = teile[0]; i = int(teile[1]) if len(teile) > 1 and teile[1].isdigit() else 0; pf = datei_pfad(name)
            if not pf: self._json({"fehler": "keine solche Datei", "name": name}); return
            alt = SCHNAPPSCHUSS.get(name)                                   # 1.5: Stueck > 0 aus dem Schnappschuss von Stueck 0 (300 s)
            if i > 0 and alt and time.time() - alt[2] < 300: roh, sha = alt[0], alt[1]
            else:
                roh = open(pf, "rb").read(); sha = hashlib.sha256(roh).hexdigest(); SCHNAPPSCHUSS[name] = (roh, sha, time.time())
                for k in [k for k, v in SCHNAPPSCHUSS.items() if time.time() - v[2] > 300]: SCHNAPPSCHUSS.pop(k, None)
            s = base64.b64encode(roh).decode(); n = (len(s) + STUECK - 1) // STUECK
            self._json({"name": name, "bytes": len(roh), "sha256": sha, "stuecke": n, "stueck": i, "b64": s[i * STUECK:(i + 1) * STUECK]})
        else:
            self.send_response(404); self.end_headers()


def auftragsbuch_laden():
    """1.6: Stand der Auftraege aus erledigt.json, damit /stand nach einem Neustart nicht bei null anfaengt."""
    try:
        erledigt = json.load(open(os.path.join(AUFTRAEGE, "erledigt.json")))
        if erledigt:
            n, d = max(erledigt.items(), key=lambda kv: (kv[1].get("ende") or "", kv[0]))
            with sperre: Z["auftraege"].update(erledigt=len(erledigt), letzter=n, rc=d.get("rc"), ende=d.get("ende"))
    except Exception: pass


def main():
    auftragsbuch_laden()
    class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
    threading.Thread(target=tegrastats, daemon=True).start(); threading.Thread(target=arbeit, daemon=True).start()
    for f in (live_lesen, pi_live_lesen, fassung_wache, yolo_lesen): threading.Thread(target=f, daemon=True).start()
    log(f"Jetson-Dienst {Z['fassung']} auf :{PORT}"); S(("", PORT), Auskunft).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
