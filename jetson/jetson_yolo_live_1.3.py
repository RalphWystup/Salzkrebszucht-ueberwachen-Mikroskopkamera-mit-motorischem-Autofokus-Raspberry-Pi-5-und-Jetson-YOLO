#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_yolo_live_1.3.py (1.3, 06.11.2026 16:45: nimmt best.pt (PyTorch FP16, gemessen 49,8 B/s) VOR einem aelteren best.engine -- das Nachtraining 1.4
schreibt nur best.pt, der liegengebliebene best.engine vom Training 1.3 (16:03) haette nach jedem Neustart das neue Modell verdeckt; Modellpfad bei jedem
Anlauf neu gewaehlt (Modell darf spaeter erscheinen), Neuladen bei Dateiwechsel; abgerissene Verbindungen (Browser schliesst /strom) ohne Protokollspur; 1.2: /strom = MJPEG mit eingezeichneten Erkennungen, sein Wort: "eine Funktionsanzeige, eine reale, die wirklich
anzeigt, dass die Objekterkennung mit YOLO funktioniert, in Echtzeit"; 1.1: laedt ein geaendertes Modell von selbst neu) -- YOLO-Livedienst auf dem Jetson (laeuft in ~/<yolo-umgebung>, Dienst mikroskop-yolo, :8096). Sein Wort 06.11.2026:
"mit dem yolo machen wir dann eine Bildauswertung auf dem jetson, wie viele tiere, groesse, geschwindigkeit etc. und spielen die daten
zurueck auf den raspi zur anzeige". Der Pi haengt nie hieran (Kernforderung 42): die Seite auf dem Pi holt die Zahlen ueber den Jetson-Dienst.
  Quelle: Livestrom des Pi (http://mikroskop:8090/strom, MJPEG). Modell: ~/mikroskop/yolo/modell/best.pt (PyTorch), nur ohne best.pt ein best.engine (TensorRT).
  Je Bild: YOLO + eingebaute Verfolgung (ByteTrack, persist); je Bahn Lage/Zeit-Verlauf -> Tempo (mm/s ueber 0,5 s), Groesse (laengere
  Rahmenseite in mm, Massstab vom Pi :8092/stand massstab_um_px, sonst 10,55 um/px).
  :8096/stand  Zahlen: Tiere im Bild (Mittel 5 s), bewegt/ruhend (< 0,2 mm/s), Groesse Median mm, Tempo Median mm/s, Koerner, Bilder/s, Modell, Zaehler je Stunde
  :8096/bild.jpg  letztes Bild mit Rahmen
  :8096/strom     MJPEG-Strom der Bilder mit Rahmen (jedes verarbeitete Bild, Guete 60) -- die Funktionsanzeige in Echtzeit
Prüfung ohne Geraet: YOLO_QUELLE=<pfad.avi> YOLO_MODELL=<pfad> python3 jetson_yolo_live_1.2.py"""
import os, sys, time, json, threading, collections, re, http.server, socketserver, urllib.request, statistics as st
import numpy as np, cv2
PORT = int(os.environ.get("YOLO_PORT", "8096")); QUELLE = os.environ.get("YOLO_QUELLE", "http://mikroskop:8090/strom"); PI_STAND = "http://mikroskop:8092/stand"
def modell_pfad():
    """1.3: best.pt vor best.engine; Umgebung YOLO_MODELL geht vor."""
    return os.environ.get("YOLO_MODELL") or next((p for p in (os.path.expanduser("~/mikroskop/yolo/modell/best.pt"), os.path.expanduser("~/mikroskop/yolo/modell/best.engine")) if os.path.exists(p)), None)
MODELL = modell_pfad()
KLASSEN = {0: "tier", 1: "korn", 2: "massstab"}; CONF = 0.4; RUHE_MM_S = 0.2; MASSSTAB_VORGABE = 10.55
Z = {"fassung": "1.3", "modell": os.path.basename(MODELL) if MODELL else None, "phase": "start", "seit": time.time(), "bilder": 0, "bilder_s": 0.0, "verarbeitet_s": 0.0, "kaputt": 0,
     "massstab_um_px": MASSSTAB_VORGABE, "tiere": 0, "tiere_mittel_5s": 0.0, "bewegt": 0, "ruhend": 0, "koerner": 0, "groesse_mm_median": None, "tempo_mm_s_median": None,
     "bahnen_aktiv": 0, "fehler": None, "zaehler": {"stunden": [], "laufend": None}}
sperre = threading.Lock(); BILD = {"jpeg": None, "n": 0}; bild_da = threading.Condition(); LAENGE = re.compile(rb"Content-Length:\s*(\d+)")
def log(s): print(time.strftime("%H:%M:%S "), s, flush=True)


def strom():
    """MJPEG-Teile vom Pi (oder Bilder aus einer Videodatei zur Pruefung), mit Wiederverbindung."""
    if not QUELLE.startswith("http"):
        cap = cv2.VideoCapture(QUELLE)
        while True:
            ok, im = cap.read()
            if not ok: cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
            yield im, time.time(); time.sleep(1 / 29)
    while True:
        try:
            r = urllib.request.urlopen(QUELLE, timeout=20); puf = b""
            while True:
                s = r.read(65536)
                if not s: break
                puf += s; t = time.time()
                while True:
                    a = puf.find(b"\r\n\r\n")
                    if a < 0: break
                    m = LAENGE.search(puf[:a])
                    if not m: puf = puf[a + 4:]; break
                    n = int(m.group(1))
                    if len(puf) < a + 4 + n: break
                    b = puf[a + 4:a + 4 + n]; puf = puf[a + 4 + n:]
                    if b[-2:] != b"\xff\xd9":
                        with sperre: Z["kaputt"] += 1
                        continue
                    im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                    if im is not None: yield im, t
        except Exception as e:
            with sperre: Z["fehler"] = f"Strom: {str(e)[:80]}"
            log(f"Strom abgerissen ({e}) -- neuer Versuch in 2 s"); time.sleep(2)


def massstab_holen():
    while True:
        try:
            d = json.load(urllib.request.urlopen(PI_STAND, timeout=5)); m = d.get("massstab_um_px")
            if m:
                with sperre: Z["massstab_um_px"] = float(m)
        except Exception: pass
        time.sleep(60)


def zaehlen(n_tiere, t):
    z = Z["zaehler"]; uhr = time.strftime("%Y-%m-%dT%H:00", time.localtime(t)); l = z["laufend"]
    if l is None or l["uhr"] != uhr:
        if l is not None: l["mittel"] = round(l["summe"] / max(l["bilder"], 1), 2); del l["summe"]; z["stunden"] = (z["stunden"] + [l])[-72:]
        l = z["laufend"] = {"uhr": uhr, "hoechstens": 0, "summe": 0, "bilder": 0}
    l["bilder"] += 1; l["summe"] += n_tiere; l["hoechstens"] = max(l["hoechstens"], n_tiere)


def lauf():
    global MODELL
    MODELL = modell_pfad()                                                      # 1.3: bei jedem Anlauf neu waehlen
    with sperre: Z["modell"] = os.path.basename(MODELL) if MODELL else None
    if not MODELL:
        with sperre: Z["phase"] = "wartet auf Modell (~/mikroskop/yolo/modell/best.pt oder best.engine)"
        log(Z["phase"]); return
    from ultralytics import YOLO
    m = YOLO(MODELL); log(f"Modell {MODELL} geladen"); modell_zeit = os.path.getmtime(MODELL)
    bahnen = {}; fenster = collections.deque(maxlen=150); t_rate = time.time(); n_rate = 0; n_verarb = 0
    with sperre: Z["phase"] = "laeuft"
    for im, t in strom():
        with sperre: Z["bilder"] += 1
        if Z["bilder"] % 300 == 0 and (modell_pfad() != MODELL or not os.path.exists(MODELL) or os.path.getmtime(MODELL) != modell_zeit):      # 1.1/1.3: neues Modell -> neu laden
            log("Modell geaendert -- lade neu"); return
        n_rate += 1
        erg = m.track(im, persist=True, tracker="bytetrack.yaml", conf=CONF, imgsz=640, half=True, device=0, verbose=False)[0]
        n_verarb += 1; mst = Z["massstab_um_px"]; tiere = []; koerner = 0
        if erg.boxes is not None and len(erg.boxes):
            kl = erg.boxes.cls.cpu().numpy().astype(int); xyxy = erg.boxes.xyxy.cpu().numpy(); ids = erg.boxes.id.cpu().numpy().astype(int) if erg.boxes.id is not None else [-1] * len(kl)
            for k, box, i in zip(kl, xyxy, ids):
                if KLASSEN.get(int(k)) == "korn": koerner += 1; continue
                if KLASSEN.get(int(k)) != "tier": continue
                cx, cy = float((box[0] + box[2]) / 2), float((box[1] + box[3]) / 2); laenge_mm = float(max(box[2] - box[0], box[3] - box[1])) * mst / 1000
                b = bahnen.setdefault(int(i), {"spur": collections.deque(maxlen=30), "gesehen": t}); b["spur"].append((t, cx, cy)); b["gesehen"] = t
                tempo = None; frueher = [p for p in b["spur"] if t - p[0] >= 0.5]
                if frueher: p0 = frueher[-1]; dt = t - p0[0]; tempo = float(np.hypot(cx - p0[1], cy - p0[2])) * mst / 1000 / dt if dt > 0 else None
                tiere.append({"nr": int(i), "x": round(cx, 1), "y": round(cy, 1), "mm": round(laenge_mm, 2), "mm_s": None if tempo is None else round(tempo, 2)})
        for i in [i for i, b in bahnen.items() if t - b["gesehen"] > 5]: bahnen.pop(i, None)
        fenster.append((t, len(tiere))); zaehlen(len(tiere), t)
        tempi = [x["mm_s"] for x in tiere if x["mm_s"] is not None]; bewegt = sum(1 for v in tempi if v >= RUHE_MM_S); ruhend = sum(1 for v in tempi if v < RUHE_MM_S)
        with sperre:
            Z.update(tiere=len(tiere), bewegt=bewegt, ruhend=ruhend, koerner=koerner, bahnen_aktiv=len(bahnen), tiere_mittel_5s=round(st.mean([n for tt, n in fenster if t - tt <= 5] or [0]), 2),
                     groesse_mm_median=round(st.median([x["mm"] for x in tiere]), 2) if tiere else None, tempo_mm_s_median=round(st.median(tempi), 2) if tempi else None, fehler=None)
        if time.time() - t_rate >= 5:
            with sperre: Z["bilder_s"] = round(n_rate / (time.time() - t_rate), 1); Z["verarbeitet_s"] = round(n_verarb / (time.time() - t_rate), 1)
            t_rate, n_rate, n_verarb = time.time(), 0, 0
        ab = erg.plot(line_width=1, font_size=0.4, labels=True, conf=True); ok, jpg = cv2.imencode(".jpg", ab, [cv2.IMWRITE_JPEG_QUALITY, 60])   # 1.2: jedes Bild fuer den Strom
        if ok:
            with bild_da: BILD["jpeg"] = jpg.tobytes(); BILD["n"] += 1; bild_da.notify_all()


class Auskunft(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, b, typ):
        try:
            self.send_response(200); self.send_header("Content-Type", typ); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError, OSError): pass                # 1.3: Browser weg -- keine Fehlerspur im Protokoll
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/stand"):
            with sperre: d = json.loads(json.dumps(Z))
            d["laeuft_min"] = round((time.time() - Z["seit"]) / 60, 1); self._send(json.dumps(d).encode(), "application/json")
        elif p == "/bild.jpg" and BILD["jpeg"]: self._send(BILD["jpeg"], "image/jpeg")
        elif p == "/strom":                                                   # 1.2: MJPEG der Bilder mit Rahmen
            self.send_response(200); self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame"); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            n = -1
            try:
                while True:
                    with bild_da:
                        bild_da.wait_for(lambda: BILD["jpeg"] is not None and BILD["n"] != n, timeout=5); b = BILD["jpeg"]; n = BILD["n"]
                    if b: self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(b)).encode() + b"\r\n\r\n" + b + b"\r\n"); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError): pass
        else: self.send_response(404); self.end_headers()


def main():
    class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
    threading.Thread(target=S(("", PORT), Auskunft).serve_forever, daemon=True).start(); threading.Thread(target=massstab_holen, daemon=True).start()
    log(f"YOLO-Livedienst {Z['fassung']} auf :{PORT}, Modell {MODELL}, Quelle {QUELLE}")
    while True:
        try: lauf()
        except Exception as e:
            with sperre: Z["fehler"] = str(e)[:120]; Z["phase"] = "Fehler"
            log(f"Fehler: {e}")
        time.sleep(10)


if __name__ == "__main__": sys.exit(main())
