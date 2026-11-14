#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_vergleich_rev2_rev3_1.0.py -- laeuft AUF dem Jetson (~/yolo_umgebung/bin/python): Pi-Auswertung 1.4_rev2 (feste Farbschwelle 40)
gegen 1.4_rev3 (mitlaufende Farbschwelle) an denselben echten Videos der letzten Stunden, Bild fuer Bild mit Erkenner und Verfolger der
jeweiligen Fassung. Bezugsgroessen, beide unabhaengig von OpenCV: (a) heutiges YOLO-Modell (Tiere, conf 0,4), (b) Farbwahrheit
<satz>_farbe.jsonl (soweit vorhanden). Gemessen je Fassung: gemeldete Punkte je Bild, Anteil der YOLO-Tiere mit Punkt, Anteil der Farbtiere
mit Punkt, Punkte ohne YOLO- und ohne Farbtier ("unbelegt", Geisterverdacht). rev3 wird vorher an WARM Saetzen eingeschwungen (Ring der
Saettigungen gefuellt, Schwelle gesetzt). Ausgabe ~/mikroskop/vergleich_rev2_rev3_1.0.txt.
1.1 (14.11.2026): Seitencache leeren, bei GPU-Speichernot auf den Prozessor; 1.0 brach mit NVML-Fehler ab. Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, sys, glob, json, time, importlib.util, collections
import numpy as np, cv2
H = os.path.expanduser("~/mikroskop"); A = os.path.join(H, "aufnahmen"); M_DIR = os.path.join(H, "vergleich_rev")
N_SAETZE, WARM, BILDER_MAX = 12, 4, 400
def lade_modul(name):
    sp = importlib.util.spec_from_file_location(name.replace(".", "_"), os.path.join(M_DIR, name + ".py")); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    m.log = lambda s: print("   [" + name + "]", s, flush=True); return m
R2, R3 = lade_modul("auswertung_1.4_rev2"), lade_modul("auswertung_1.4_rev3")
import subprocess
from ultralytics import YOLO
subprocess.run("sudo -n /usr/local/sbin/cache_leeren >/dev/null 2>&1", shell=True)
Y = YOLO(os.path.join(H, "yolo", "modell", "best.pt")); GERAET, HALB = 0, True
try: Y.predict(np.zeros((480, 640, 3), np.uint8), imgsz=640, half=True, device=0, verbose=False)
except Exception as e:                                   # 1.1: GPU-Speicher belegt (Livedienst) -> Prozessor
    print("GPU nicht nutzbar:", str(e)[:80], "-> CPU", flush=True); GERAET, HALB = "cpu", False
saetze = sorted((os.path.basename(p)[:-4] for p in glob.glob(A + "/*.avi") if not p.endswith("_rahmen.avi")), reverse=True)
saetze = [s for s in saetze if os.path.getsize(os.path.join(A, s + ".avi")) > 200000][:WARM + N_SAETZE]
print(f"{len(saetze)} Saetze mit Video; {WARM} zum Einschwingen von rev3, {len(saetze) - WARM} zum Vergleich", flush=True)
def bilder(s):
    cap = cv2.VideoCapture(os.path.join(A, s + ".avi")); n = 0
    while n < BILDER_MAX:
        ok, im = cap.read()
        if not ok: break
        yield n, im; n += 1
    cap.release()
# Einschwingen rev3: Erkenner ueber die WARM Saetze, Ring fuellen, Schwelle setzen
for s in saetze[:WARM]:
    E = R3.Erkenner()
    for n, im in bilder(s):
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); E.schritt(g[R3.AUS], im[R3.AUS])
R3.schwelle_nachfuehren(jetzt=time.time() + 1e6)
print(f"rev3 eingeschwungen: BRAUN_S {R3.BRAUN_S} (Median {R3.Z.get('braun_s_median')}, {len(R3.S_RING)} Werte); rev2 BRAUN_S {R2.BRAUN_S}", flush=True)
def in_box(x, y, b, rand=8): return b[0] - rand <= x <= b[2] + rand and b[1] - rand <= y <= b[3] + rand
summe = {v: collections.Counter() for v in ("rev2", "rev3")}
for s in saetze[WARM:]:
    fp = os.path.join(A, s + "_farbe.jsonl"); wahr = {}
    if os.path.exists(fp):
        try: wahr = {w["b"]: w.get("tiere", []) for w in [json.loads(l) for l in open(fp) if l.strip()][1:]}
        except Exception: wahr = {}
    zust = {v: (M.Erkenner(), M.Verfolger()) for v, M in (("rev2", R2), ("rev3", R3))}; zs = {v: collections.Counter() for v in zust}
    for n, im in bilder(s):
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        r = Y.predict(im, conf=0.4, imgsz=640, half=HALB, device=GERAET, verbose=False)[0]
        yb = [b for b, k in zip(r.boxes.xyxy.cpu().numpy().tolist(), r.boxes.cls.cpu().numpy().astype(int)) if k == 0] if r.boxes is not None and len(r.boxes) else []
        ft = wahr.get(n, [])
        for v, M in (("rev2", R2), ("rev3", R3)):
            E, V = zust[v]; _, erk = E.schritt(g[M.AUS], im[M.AUS]); bew, ruh = V.schritt(erk); pk = bew + ruh
            if n < 60: continue                                                  # MOG lernt; beide gleich behandelt
            c = zs[v]; c["bilder"] += 1; c["punkte"] += len(pk); c["yolo"] += len(yb); c["farbe"] += len(ft)
            c["yolo_mit_punkt"] += sum(any(in_box(p["x"], p["y"], b) for p in pk) for b in yb)
            c["farbe_mit_punkt"] += sum(any(abs(p["x"] - t["x"]) < 30 and abs(p["y"] - t["y"]) < 30 for p in pk) for t in ft)
            c["unbelegt"] += sum(not any(in_box(p["x"], p["y"], b) for b in yb) and not any(abs(p["x"] - t["x"]) < 30 and abs(p["y"] - t["y"]) < 30 for t in ft) for p in pk)
    for v in zs:
        summe[v].update(zs[v]); c = zs[v]
        print(f"{s} {v}: Bilder {c['bilder']}, Punkte/Bild {c['punkte']/max(c['bilder'],1):.2f}, YOLO-Tiere mit Punkt {c['yolo_mit_punkt']}/{c['yolo']}, Farbtiere mit Punkt {c['farbe_mit_punkt']}/{c['farbe']}, unbelegt {c['unbelegt']}", flush=True)
zeilen = [f"Vergleich Pi-Auswertung 1.4_rev2 (BRAUN_S {R2.BRAUN_S}) gegen 1.4_rev3 (BRAUN_S {R3.BRAUN_S}, Median {R3.Z.get('braun_s_median')}) an {len(saetze)-WARM} Saetzen, {time.strftime('%Y-%m-%d %H:%M')}",
          "Fassung  Bilder  Punkte/Bild  YOLO-Tiere mit Punkt  Farbtiere mit Punkt  unbelegte Punkte"]
for v, c in summe.items():
    zeilen.append(f"{v}     {c['bilder']:6d}  {c['punkte']/max(c['bilder'],1):10.2f}  {c['yolo_mit_punkt']:6d}/{c['yolo']:<6d} = {100*c['yolo_mit_punkt']/max(c['yolo'],1):5.1f} %  {c['farbe_mit_punkt']:6d}/{c['farbe']:<6d} = {100*c['farbe_mit_punkt']/max(c['farbe'],1):5.1f} %  {c['unbelegt']:6d} ({100*c['unbelegt']/max(c['punkte'],1):4.1f} % der Punkte)")
open(os.path.join(H, "vergleich_rev2_rev3_1.0.txt"), "w").write("\n".join(zeilen) + "\n"); print("\n".join(zeilen)); print("FERTIG", flush=True)
