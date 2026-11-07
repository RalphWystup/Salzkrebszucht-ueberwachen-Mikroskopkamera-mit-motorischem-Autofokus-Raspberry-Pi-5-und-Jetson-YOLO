#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_lernbilder_1.0.py -- laeuft auf dem Jetson (Auftrag): zieht Lernbilder fuer YOLO aus den Aufnahmen. Aus jedem Satz mit Video und
Farbwahrheit (Lernarchiv zuerst) die drei Bilder mit den meisten Tieren (mindestens 25 Bilder auseinander); Vorschlagsrahmen = Farbwahrheit (Rumpf) vereinigt mit den Objekten der
Auswertung (Rahmen um Koerper), doppelte zusammengelegt (Ueberdeckung > 0,5). Ablage ~/mikroskop/lernen/bilder/<satz>_b<n>.jpg + .json
({"boxen": [{"x0","y0","x1","y1","quelle"}], "status": "offen"}). Bestehende .json werden nicht ueberschrieben (seine Korrekturen bleiben).
  python3 jetson_lernbilder_1.0.py [hoechstens_bilder=300]"""
import os, glob, json, sys, cv2
A = os.path.expanduser("~/mikroskop/aufnahmen"); Z = os.path.expanduser("~/mikroskop/lernen/bilder"); os.makedirs(Z, exist_ok=True)
HOECHSTENS = int(sys.argv[1]) if len(sys.argv) > 1 else 300; RAND = 6
def lade(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def box(t, rand=RAND): return [max(0, t["rx"] - rand), max(0, t["ry"] - rand), min(640, t["rx"] + t["rb"] + rand), min(480, t["ry"] + t["rh"] + rand)]
def ueberdeckung(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / max(1e-9, (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i)
saetze = sorted(p[:-6] for p in glob.glob(A + "/*.jsonl") if not p.endswith("_farbe.jsonl") and os.path.exists(p[:-6] + "_farbe.jsonl") and os.path.exists(p[:-6] + ".avi"))
saetze = [s for s in saetze if os.path.basename(s)[14:15] == "0"] + [s for s in saetze if os.path.basename(s)[14:15] != "0"]   # Lernarchiv zuerst
neu = 0; vorhanden = len(glob.glob(Z + "/*.jpg"))
for s in saetze:
    if vorhanden + neu >= HOECHSTENS: break
    name = os.path.basename(s); zeilen = lade(s + ".jsonl"); obj = {b["b"]: b.get("objekte", []) for b in zeilen[1:]}; wahr = {w["b"]: w.get("tiere", []) for w in lade(s + "_farbe.jsonl")[1:]}
    # 1.0: aussagekraeftige Bilder: die drei Bilder mit den meisten Tieren (Wahrheit + Auswertung), mindestens 25 Bilder auseinander, ab Bild 10
    kand = sorted(((len(wahr.get(n, [])) + len(obj.get(n, [])), n) for n in range(10, max(list(wahr) + list(obj) + [0]) + 1) if wahr.get(n) or obj.get(n)), reverse=True)
    auswahl = []
    for z, n in kand:
        if all(abs(n - m) >= 25 for m in auswahl): auswahl.append(n)
        if len(auswahl) == 3: break
    cap = cv2.VideoCapture(s + ".avi")
    for n in sorted(auswahl):
        stamm = f"{Z}/{name}_b{n}"
        if os.path.exists(stamm + ".jpg"): continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, im = cap.read()
        if not ok: continue
        boxen = [{"box": box(t), "quelle": "farbe"} for t in wahr.get(n, [])]
        for o in obj.get(n, []):
            b = box(o)
            if not any(ueberdeckung(b, x["box"]) > 0.5 for x in boxen): boxen.append({"box": b, "quelle": "auswertung"})
        cv2.imwrite(stamm + ".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 90])
        json.dump({"satz": name, "bild": n, "boxen": [{"x0": b["box"][0], "y0": b["box"][1], "x1": b["box"][2], "y1": b["box"][3], "quelle": b["quelle"]} for b in boxen], "status": "offen"}, open(stamm + ".json", "w"))
        neu += 1
    cap.release()
alle = glob.glob(Z + "/*.json"); status = {}
for p in alle:
    try: st = json.load(open(p)).get("status", "offen")
    except Exception: st = "kaputt"
    status[st] = status.get(st, 0) + 1
print("LERNBILDER", json.dumps({"neu": neu, "gesamt": len(alle), "status": status, "saetze_mit_video": len(saetze)}))
