#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_yolo_datensatz_1.1.py -- laeuft auf dem Jetson (Auftrag): baut aus den bewerteten Lernbildern (~/mikroskop/lernen/bilder) den
YOLO-Datensatz ~/mikroskop/yolo/datensatz (images/labels je train/val, data.yaml). Klassen: 0 tier, 1 korn, 2 massstab.
Geprueft (sein Urteil) immer; offen (nur Vorschlaege) ebenfalls, ausser mit --nur-geprueft; verworfen nie. Aufteilung 85/15 nach Namen (fest).
  python3 jetson_yolo_datensatz_1.1.py [--nur-geprueft]      Ausgabe DATENSATZJSON"""
import os, glob, json, shutil, hashlib, sys
L = os.path.expanduser("~/mikroskop/lernen/bilder"); D = os.path.expanduser("~/mikroskop/yolo/datensatz"); KLASSEN = ["tier", "korn", "massstab"]
nur_geprueft = "--nur-geprueft" in sys.argv
for t in ("train", "val"):
    os.makedirs(f"{D}/images/{t}", exist_ok=True); os.makedirs(f"{D}/labels/{t}", exist_ok=True)
    for p in glob.glob(f"{D}/images/{t}/*") + glob.glob(f"{D}/labels/{t}/*"): os.remove(p)      # Datensatz ist ein Bauprodukt; Quelle bleibt lernen/bilder
z = {"geprueft": 0, "offen": 0, "verworfen": 0, "train": 0, "val": 0, "boxen": {k: 0 for k in KLASSEN}, "leer": 0}
for pj in sorted(glob.glob(L + "/*.json")):
    d = json.load(open(pj, encoding="utf-8")); st = d.get("status", "offen"); z[st] = z.get(st, 0) + 1
    if st not in ("geprueft", "offen") or (st == "offen" and nur_geprueft): continue      # 1.1: zurueckgestellte und verworfene nie
    name = os.path.basename(pj)[:-5]; pb = pj[:-5] + ".jpg"
    if not os.path.exists(pb): continue
    teil = "val" if int(hashlib.md5(name.encode()).hexdigest()[:4], 16) % 100 < 15 else "train"
    shutil.copy(pb, f"{D}/images/{teil}/{name}.jpg"); zeilen = []
    for b in d.get("boxen", []):
        k = KLASSEN.index(b.get("klasse", "tier")) if b.get("klasse", "tier") in KLASSEN else 0
        x0, y0, x1, y1 = max(0, b["x0"]), max(0, b["y0"]), min(640, b["x1"]), min(480, b["y1"])
        if x1 - x0 < 3 or y1 - y0 < 3: continue
        zeilen.append(f"{k} {(x0 + x1) / 2 / 640:.6f} {(y0 + y1) / 2 / 480:.6f} {(x1 - x0) / 640:.6f} {(y1 - y0) / 480:.6f}"); z["boxen"][KLASSEN[k]] += 1
    if not zeilen: z["leer"] += 1
    open(f"{D}/labels/{teil}/{name}.txt", "w").write("\n".join(zeilen) + ("\n" if zeilen else "")); z[teil] += 1
open(f"{D}/data.yaml", "w").write(f"path: {D}\ntrain: images/train\nval: images/val\nnames:\n  0: tier\n  1: korn\n  2: massstab\n")
print("DATENSATZJSON", json.dumps(z))
