#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_verlauf_woche_1.0.py -- laeuft AUF dem Jetson (~/yolo_umgebung/bin/python, abgeloest per nohup): Verlauf der Erkennung
ueber die Tage. Sein Wort 14.11.2026: "die Identifikation mit YOLO und eventuell auch die einfache Objekterkennung mit OpenCV
funktioniert immer schlechter seit dem Start vor ca. 1 Woche -- analysieren und bestaetigen, wenn das so waere".
Je Satz (~/mikroskop/aufnahmen/<name>.jsonl, Beobachter des Pi) und Farbwahrheit (<name>_farbe.jsonl):
  OpenCV: Objekte je Bild, Helligkeit; Farbe: Tiere je Bild, Flaeche je Tier (Wachstum), Treffer (verfolgung_pruefen_1.1.py)
  YOLO: das HEUTIGE Modell (best.pt, conf 0,4 und 0,25) ueber 40 Bilder je Satz mit Video, Tiere je Bild, mittleres Vertrauen,
        Verhaeltnis zur Farbwahrheit derselben Bilder -- festes Modell, wechselndes Bildmaterial => Drift des Materials;
  dazu Modell-/Trainingsstaende (Dateidaten). Ausgabe: ~/mikroskop/verlauf_woche_1.0.json und .txt, Fortschritt im .log.
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, sys, glob, json, re, time, subprocess, collections, statistics as st
import numpy as np
H = os.path.expanduser("~/mikroskop"); A = os.path.join(H, "aufnahmen"); AUS = os.path.join(H, "verlauf_woche_1.0")
JE_TAG_YOLO = 3; BILDER_JE_SATZ = 40; CONFS = (0.4, 0.25)
def log(s): print(time.strftime("%H:%M:%S"), s, flush=True)
def lade(p):
    with open(p, encoding="utf-8") as f: return [json.loads(l) for l in f if l.strip()]

saetze = sorted(os.path.basename(p)[:-6] for p in glob.glob(A + "/*.jsonl") if not p.endswith("_farbe.jsonl"))
log(f"{len(saetze)} Saetze in {A}")
tage = collections.defaultdict(list)
for n in saetze:
    m = re.match(r"(\d{8})_(\d{4})", n)
    if not m: continue
    tag = m.group(1); e = {"name": n, "uhr": m.group(2), "video": os.path.exists(os.path.join(A, n + ".avi")), "farbe": os.path.exists(os.path.join(A, n + "_farbe.jsonl"))}
    try:
        z = lade(os.path.join(A, n + ".jsonl")); kopf, bilder = z[0], z[1:]
        e["fassung"] = kopf.get("fassung"); e["bilder"] = len(bilder)
        e["cv_je_bild"] = float(np.mean([len(b.get("objekte", [])) for b in bilder])) if bilder else None
        hell = [b.get("hell") for b in bilder if b.get("hell") is not None]; e["hell"] = float(np.mean(hell)) if hell else None
        if e["farbe"]:
            fz = lade(os.path.join(A, n + "_farbe.jsonl"))[1:]; tiere = [t for w in fz for t in w.get("tiere", [])]
            e["farbe_je_bild"] = len(tiere) / max(len(fz), 1); e["flaeche_median_px"] = float(np.median([t["a"] for t in tiere])) if tiere else None
            e["farbe_bilder"] = {w["b"]: len(w.get("tiere", [])) for w in fz}
    except Exception as ex:
        e["fehler"] = str(ex)[:120]
    tage[tag].append(e)

# YOLO: heutiges Modell
modell = next((p for p in (os.path.join(H, "yolo/modell/best.pt"), os.path.join(H, "yolo/modell/best.engine")) if os.path.exists(p)), None)
info_modell = {"pfad": modell, "geaendert": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(modell))) if modell else None,
               "modellordner": sorted((os.path.basename(p), time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))) for p in glob.glob(os.path.join(H, "yolo/modell/*"))),
               "trainingslaeufe": sorted((os.path.basename(p), time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))) for p in glob.glob(os.path.join(H, "yolo/runs/*/*")) + glob.glob(os.path.join(H, "yolo/*/train*")))[-12:]}
log(f"Modell: {info_modell}")
try:
    from ultralytics import YOLO; import cv2
    M = YOLO(modell) if modell else None
except Exception as ex:
    M = None; log(f"YOLO nicht ladbar: {ex}")

def yolo_satz(e):
    p = os.path.join(A, e["name"] + ".avi"); cap = cv2.VideoCapture(p); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n <= 0: cap.release(); return None
    idx = np.linspace(0, n - 1, min(BILDER_JE_SATZ, n)).astype(int); erg = {c: {"tiere": [], "conf": []} for c in CONFS}; farbe_n = []; laplace = []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i)); ok, im = cap.read()
        if not ok: continue
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); laplace.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))
        fb = e.get("farbe_bilder") or {}; farbe_n.append(fb.get(int(i), fb.get(str(int(i)))))
        for c in CONFS:
            r = M.predict(im, conf=c, imgsz=640, half=True, device=0, verbose=False)[0]
            kl = r.boxes.cls.cpu().numpy().astype(int) if r.boxes is not None and len(r.boxes) else np.array([], int)
            cf = r.boxes.conf.cpu().numpy() if r.boxes is not None and len(r.boxes) else np.array([])
            t = kl == 0; erg[c]["tiere"].append(int(t.sum())); erg[c]["conf"].extend(cf[t].tolist())
    cap.release()
    out = {"bilder": len(laplace), "schaerfe_laplace": float(np.median(laplace)) if laplace else None}
    fn = [x for x in farbe_n if x is not None]
    for c in CONFS:
        out[f"yolo_je_bild_{c}"] = float(np.mean(erg[c]["tiere"])) if erg[c]["tiere"] else None
        out[f"conf_mittel_{c}"] = float(np.mean(erg[c]["conf"])) if erg[c]["conf"] else None
        if fn and len(fn) == len(erg[c]["tiere"]):
            paare = [(y, f) for y, f in zip(erg[c]["tiere"], fn) if f is not None]
            out[f"yolo_zu_farbe_{c}"] = float(sum(min(y, f) for y, f in paare) / max(sum(f for _, f in paare), 1))   # Anteil der Farbtiere, den YOLO (hoechstens je Bild) findet
    return out

def treffer(e):
    try:
        aus = subprocess.run(["python3", os.path.join(H, "verfolgung_pruefen_1.1.py"), os.path.join(A, e["name"] + ".jsonl")], capture_output=True, text=True, timeout=240).stdout
        m = re.search(r"Tiere nach Farbe (\d+), getroffen (\d+)", aus); return (int(m.group(1)), int(m.group(2))) if m else None
    except Exception as ex:
        log(f"verfolgung_pruefen {e['name']}: {ex}"); return None

ergebnis = {"erzeugt": time.strftime("%Y-%m-%d %H:%M"), "modell": info_modell, "tage": {}}
for tag in sorted(tage):
    S = tage[tag]; mitv = [e for e in S if e["video"] and e["farbe"]]
    wahl = [mitv[int(k)] for k in np.linspace(0, len(mitv) - 1, min(JE_TAG_YOLO, len(mitv))).astype(int)] if mitv else []
    T = {"saetze": len(S), "mit_video": len(mitv), "fassungen": sorted({e.get("fassung") for e in S if e.get("fassung")}),
         "cv_je_bild": float(np.mean([e["cv_je_bild"] for e in S if e.get("cv_je_bild") is not None])) if any(e.get("cv_je_bild") is not None for e in S) else None,
         "farbe_je_bild": float(np.mean([e["farbe_je_bild"] for e in S if e.get("farbe_je_bild") is not None])) if any(e.get("farbe_je_bild") is not None for e in S) else None,
         "flaeche_median_px": float(np.median([e["flaeche_median_px"] for e in S if e.get("flaeche_median_px")])) if any(e.get("flaeche_median_px") for e in S) else None,
         "hell": float(np.mean([e["hell"] for e in S if e.get("hell") is not None])) if any(e.get("hell") is not None for e in S) else None, "proben": []}
    for e in wahl:
        log(f"{tag} {e['name']}: Treffer und YOLO …"); pr = {"name": e["name"], "uhr": e["uhr"]}
        tr = treffer(e); pr["treffer"] = {"farbe": tr[0], "getroffen": tr[1], "prozent": round(100 * tr[1] / max(tr[0], 1), 1)} if tr else None
        if M is not None:
            try: pr["yolo"] = yolo_satz(e)
            except Exception as ex: pr["yolo"] = {"fehler": str(ex)[:160]}
        T["proben"].append(pr); log(f"   {pr}")
    ergebnis["tage"][tag] = T
    json.dump(ergebnis, open(AUS + ".json", "w"), indent=1)

# Tafel
zeilen = ["Tag       Saetze Video  CV/Bild  Farbe/Bild  Flaeche px  Hell  Treffer%  YOLO/Bild(.4)  conf(.4)  YOLO/Farbe(.4)  YOLO/Farbe(.25)  Schaerfe"]
for tag, T in sorted(ergebnis["tage"].items()):
    P = T["proben"]; f = lambda k, d=2: (lambda v: "   -  " if not v else f"{np.mean(v):{6}.{d}f}")([p[k[0]][k[1]] for p in P if p.get(k[0]) and p[k[0]].get(k[1]) is not None])
    zeilen.append(f"{tag}  {T['saetze']:5d} {T['mit_video']:5d}  {T['cv_je_bild'] or 0:7.2f}  {T['farbe_je_bild'] or 0:9.2f}  {T['flaeche_median_px'] or 0:9.0f}  {T['hell'] or 0:5.0f}  {f(('treffer','prozent'),0):>7}  {f(('yolo','yolo_je_bild_0.4')):>12}  {f(('yolo','conf_mittel_0.4')):>8}  {f(('yolo','yolo_zu_farbe_0.4')):>13}  {f(('yolo','yolo_zu_farbe_0.25')):>14}  {f(('yolo','schaerfe_laplace'),0):>8}")
open(AUS + ".txt", "w").write("\n".join(zeilen) + "\n"); print("\n".join(zeilen)); log("FERTIG")
