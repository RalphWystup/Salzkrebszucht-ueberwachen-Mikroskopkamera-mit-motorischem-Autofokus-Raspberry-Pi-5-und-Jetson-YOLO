#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_farbfilter_1.0.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Problem 9, der entscheidende Schritt. Bisher ist belegt:
  - Die Farbregel findet 44,5 % seiner Tier-Rahmen; auf den von Hand nachgetragenen nur 1 von 43 (2,3 %).
  - Die Montage zeigt: die verpassten Tiere sind blass und liegen fast alle AUF oder NEBEN dem schwarzen Aufdruck.
  - Die Saettigung allein erklaert das NICHT: bei der heutigen Schwelle 40 haben 69,8 % der von Hand
    nachgetragenen Tiere genug gesaettigte Punkte (jetson_farbschwelle_1.0). Sie gehen also SPAETER verloren.

Dieses Programm misst, an WELCHER Stufe sie verloren gehen -- dieselbe Methode wie beim Befund zu Problem 4
(erst messen, an welchem Filter die Wahrheit scheitert, dann erst etwas aendern). Je Tierrahmen des
Beobachters wird der Reihe nach geprueft:

  Stufe 1  Saettigung   >= PUNKTE_MIN Punkte mit S > 40 bei 40 < V < 235 (oder dunkler Kopf) im Rahmen
  Stufe 2  Ortsfest     davon bleiben >= PUNKTE_MIN uebrig, nachdem die Ortsfest-Masken abgezogen sind
  Stufe 3  Form         Oeffnen/Schliessen/Gruppieren lassen >= PUNKTE_MIN zusammenhaengende Punkte uebrig
  Stufe 4  Flaeche      das Gebiet liegt im Fenster 150..6000 px  -> gefunden

Getrennt ausgewiesen wird, ob der Rahmen UEBER DEM AUFDRUCK liegt (Ueberschneidung mit der dunklen
Ortsfest-Maske) oder nicht. Damit ist zu sehen, ob die Ortsfest-Maske die Tiere ueber dem Aufdruck loescht.

Wahrheit sind hier die Rahmen des Beobachters (bewegte Tiere) -- unabhaengig von der Farbregel. Nur lesen.

  python3 jetson_farbfilter_1.0.py [--saetze 25] [--bilder 6] [--grenze_s 900]
"""
import os, sys, json, glob, time
import numpy as np, cv2

A = os.path.join(os.path.expanduser("~/mikroskop"), "aufnahmen")
SAT, V_MIN, V_MAX, V_KOPF, GRUPPE = 40, 40, 235, 120, 15
FLAECHE_MIN, FLAECHE_MAX = 150, 6000
AUS = (slice(40, 440), slice(60, 580))
KERN_AUF, KERN_ZU = np.ones((3, 3), np.uint8), np.ones((7, 7), np.uint8)
PUNKTE_MIN = 40


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1] if n in sys.argv else v)


def statische_masken(bilder, anteil=0.8):
    sb = None; n = 0
    for im in bilder[::3]:
        hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
        b = ((hsv[:, :, 1] > SAT) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint16)
        sb = b if sb is None else sb + b; n += 1
    k = np.ones((9, 9), np.uint8)
    med = np.median(np.stack([im[AUS] for im in bilder[::3]]), axis=0).astype(np.uint8)
    dunkel_fest = cv2.dilate((cv2.cvtColor(med, cv2.COLOR_BGR2HSV)[:, :, 2] < V_KOPF + 20).astype(np.uint8), k)
    return cv2.dilate((sb >= anteil * n).astype(np.uint8), k), dunkel_fest


def main():
    n_saetze = arg("--saetze", 25); n_bilder = arg("--bilder", 6); grenze = arg("--grenze_s", 900.0)
    staemme = sorted(p[:-4] for p in glob.glob(A + "/*.avi") if not p.endswith("_rahmen.avi") and os.path.exists(p[:-4] + ".jsonl"))
    if not staemme: print("keine Saetze mit Video"); return 1
    wahl = [staemme[i] for i in np.linspace(0, len(staemme) - 1, min(n_saetze, len(staemme))).astype(int)]
    print(f"{len(staemme)} Saetze mit Video, davon {len(wahl)} gemessen, je bis zu {n_bilder} Bilder.")
    print(f"Wahrheit: Rahmen des Beobachters (bewegte Tiere). Schwelle S > {SAT}, Punktgrenze {PUNKTE_MIN}.\n")
    Z = {"gesamt": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0}
    AUF = {True: dict(Z), False: dict(Z)}
    t0 = time.time(); n_s = 0
    for s in wahl:
        if time.time() - t0 > grenze: print(f"Zeitgrenze nach {n_s} Saetzen"); break
        try:
            z = [json.loads(l) for l in open(s + ".jsonl", encoding="utf-8") if l.strip()]
            rahmen = {b["b"]: [o for o in b.get("objekte", []) if not o.get("ruht")] for b in z[1:]}
            mit = [b for b, rr in rahmen.items() if rr]
            if not mit: continue
            cap = cv2.VideoCapture(s + ".avi"); alle = []
            while True:
                ok, im = cap.read()
                if not ok: break
                alle.append(im)
            cap.release()
            if len(alle) < 10: continue
            braun_fest, dunkel_fest = statische_masken(alle)
            n_s += 1
            for b in [mit[i] for i in np.linspace(0, len(mit) - 1, min(n_bilder, len(mit))).astype(int)]:
                if b >= len(alle): continue
                im = alle[b]; aus = im[AUS]; hsv = cv2.cvtColor(aus, cv2.COLOR_BGR2HSV)
                S_, V_ = hsv[:, :, 1], hsv[:, :, 2]
                rumpf = ((S_ > SAT) & (V_ > V_MIN) & (V_ < V_MAX)).astype(np.uint8)
                kopf = ((V_ < V_KOPF) & (S_ < 40)).astype(np.uint8)
                roh = np.maximum(rumpf, kopf)
                r2 = rumpf.copy(); k2 = kopf.copy(); r2[braun_fest > 0] = 0; k2[dunkel_fest > 0] = 0
                nach_fest = np.maximum(r2, k2)
                m = cv2.morphologyEx(nach_fest, cv2.MORPH_OPEN, KERN_AUF)
                m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, KERN_ZU)
                grob = cv2.dilate(m, np.ones((GRUPPE + 1, GRUPPE + 1), np.uint8))
                nn, labg, _, _ = cv2.connectedComponentsWithStats(grob, 8)
                lab = np.where(m > 0, labg, 0).astype(np.int32)
                flaechen = {i: int((lab == i).sum()) for i in range(1, nn)}
                for o in rahmen[b]:
                    x0 = max(0, o["rx"] - AUS[1].start); y0 = max(0, o["ry"] - AUS[0].start)
                    x1 = min(aus.shape[1], x0 + o["rb"]); y1 = min(aus.shape[0], y0 + o["rh"])
                    if x1 <= x0 or y1 <= y0: continue
                    ueber_druck = bool(dunkel_fest[y0:y1, x0:x1].mean() > 0.15)
                    T = AUF[ueber_druck]; T["gesamt"] += 1; Z["gesamt"] += 1
                    n1 = int(roh[y0:y1, x0:x1].sum())
                    if n1 < PUNKTE_MIN: continue
                    T["s1"] += 1; Z["s1"] += 1
                    n2 = int(nach_fest[y0:y1, x0:x1].sum())
                    if n2 < PUNKTE_MIN: continue
                    T["s2"] += 1; Z["s2"] += 1
                    n3 = int(m[y0:y1, x0:x1].sum())
                    if n3 < PUNKTE_MIN: continue
                    T["s3"] += 1; Z["s3"] += 1
                    teil = lab[y0:y1, x0:x1]; ids = [i for i in np.unique(teil) if i > 0]
                    if any(FLAECHE_MIN <= flaechen.get(int(i), 0) <= FLAECHE_MAX for i in ids):
                        T["s4"] += 1; Z["s4"] += 1
        except Exception as e:
            print(f"  {os.path.basename(s)}: {e}")
    g = max(Z["gesamt"], 1)
    print(f"gemessen: {n_s} Saetze, {Z['gesamt']} Tierrahmen, {time.time()-t0:.0f} s\n")
    print("Stufe                              bleiben uebrig   verloren an dieser Stufe")
    reihen = [("0  Tierrahmen des Beobachters", Z["gesamt"], 0),
              ("1  Saettigung S > 40 / dunkler Kopf", Z["s1"], Z["gesamt"] - Z["s1"]),
              ("2  Ortsfest-Masken abgezogen", Z["s2"], Z["s1"] - Z["s2"]),
              ("3  Oeffnen/Schliessen/Gruppieren", Z["s3"], Z["s2"] - Z["s3"]),
              ("4  Flaechenfenster 150..6000 px", Z["s4"], Z["s3"] - Z["s4"])]
    for name, bleibt, weg in reihen:
        print(f"{name:<36} {bleibt:6d} ({100.0*bleibt/g:5.1f} %)   {weg:6d} ({100.0*weg/g:5.1f} %)")
    print(f"\n=> die Farbregel findet {100.0*Z['s4']/g:.1f} % der Tiere, die der Beobachter meldet\n")
    print("Getrennt nach Lage zum schwarzen Aufdruck:")
    print(f"{'':<22}{'Rahmen':>8}{'nach 1':>9}{'nach 2':>9}{'nach 3':>9}{'gefunden':>10}")
    for lage, name in ((True, "UEBER dem Aufdruck"), (False, "frei vom Aufdruck")):
        T = AUF[lage]; gg = max(T["gesamt"], 1)
        print(f"{name:<22}{T['gesamt']:8d}{100.0*T['s1']/gg:8.1f}%{100.0*T['s2']/gg:8.1f}%"
              f"{100.0*T['s3']/gg:8.1f}%{100.0*T['s4']/gg:9.1f}%")
    vA = AUF[True]; vB = AUF[False]
    if vA["gesamt"] and vB["gesamt"]:
        print(f"\nVerlust an der Ortsfest-Maske (Stufe 2): ueber dem Aufdruck "
              f"{100.0*(vA['s1']-vA['s2'])/max(vA['s1'],1):.1f} %, frei davon {100.0*(vB['s1']-vB['s2'])/max(vB['s1'],1):.1f} %")
    json.dump({"gesamt": Z, "ueber_aufdruck": AUF[True], "frei": AUF[False], "saetze": n_s},
              open(f"befund_farbfilter_{time.strftime('%Y-%m-%d')}.json", "w", encoding="utf-8"))
    print(f"\ngeschrieben: befund_farbfilter_{time.strftime('%Y-%m-%d')}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
