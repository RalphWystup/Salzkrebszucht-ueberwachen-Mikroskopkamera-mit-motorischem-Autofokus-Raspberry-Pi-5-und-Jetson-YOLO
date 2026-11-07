#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_farbschwelle_1.0.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Verbindet Problem 6 und Problem 9. Zwei Messungen dieses Tages zeigen in dieselbe Richtung:
  - Problem 6 (jetson_lichtfarbe_1.1): ueber 160 Saetze ist die Schwelle S > 40 in KEINEM einzigen die beste;
    die beste liegt bei 20 bis 30, und die feste 40 kostet 25,8 Punkte Trennkraft.
  - Problem 9 (Montage der Streitfaelle): die 116 Tiere, die die Farbregel verpasst, sind nach Augenschein
    durchweg BLASSE, kontrastarme Tiere -- also solche mit niedriger Saettigung.
Die Vermutung lautet daher: der blinde Fleck der Farbregel ist zu einem guten Teil einfach eine zu hohe
Schwelle. Dieses Programm prueft das an SEINEN Rahmen (Wahrheit) und misst fuer S = 15..55:

  A  Trefferquote und Genauigkeit der ganzen Farbregel (oeffnen, schliessen, Gruppieren, Flaechenfenster)
  B  Rohmass ohne jede Form: Anteil seiner Rahmen, in deren mittlerem Drittel mindestens 60 Punkte
     die Schwelle erfuellen -- unabhaengig von Morphologie und Flaechengrenzen

Vorbehalt, der mitgedruckt wird: zu diesen Lernbildern gibt es keine Videos mehr, also fehlt die
Ortsfest-Maske (dunkler Aufdruck, liegende Koerner). Das trifft JEDE Schwelle gleich, der VERGLEICH der
Schwellen bleibt also gueltig; die Genauigkeit ist durchweg zu niedrig angesetzt.

Nur lesen. Schreibt befund_farbschwelle_<datum>.json.

  python3 jetson_farbschwelle_1.0.py [--iou 0.3]
"""
import os, sys, json, glob, time
import numpy as np, cv2

H = os.path.expanduser("~/mikroskop"); LERN = os.path.join(H, "lernen", "bilder")
V_MIN, V_MAX, V_KOPF, GRUPPE = 40, 235, 120, 15
FLAECHE_MIN, FLAECHE_MAX = 150, 6000
AUS = (slice(40, 440), slice(60, 580))
KERN_AUF, KERN_ZU = np.ones((3, 3), np.uint8), np.ones((7, 7), np.uint8)
SCHWELLEN = [15, 20, 25, 30, 35, 40, 45, 50, 55]
ROH_MIN = 60


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1] if n in sys.argv else v)


def ueberdeckung(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / max(1e-9, (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)


def gebiete(im, sat):
    hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
    rumpf = ((hsv[:, :, 1] > sat) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint8)
    kopf = ((hsv[:, :, 2] < V_KOPF) & (hsv[:, :, 1] < 40)).astype(np.uint8)
    m = cv2.morphologyEx(np.maximum(rumpf, kopf), cv2.MORPH_OPEN, KERN_AUF)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, KERN_ZU)
    grob = cv2.dilate(m, np.ones((GRUPPE + 1, GRUPPE + 1), np.uint8))
    nn, labg, _, _ = cv2.connectedComponentsWithStats(grob, 8)
    lab = np.where(m > 0, labg, 0).astype(np.int32)
    aus = []
    for i in range(1, nn):
        ys, xs = np.nonzero(lab == i); a = int(len(xs))
        if not (FLAECHE_MIN <= a <= FLAECHE_MAX): continue
        aus.append([int(xs.min()) + AUS[1].start, int(ys.min()) + AUS[0].start,
                    int(xs.max()) + AUS[1].start + 1, int(ys.max()) + AUS[0].start + 1])
    return aus


def paaren(wahr, gef, iou_min):
    frei_w = set(range(len(wahr))); frei_g = set(range(len(gef))); n = 0
    for u, i, j in sorted(((ueberdeckung(wahr[i], gef[j]), i, j) for i in frei_w for j in frei_g), reverse=True):
        if u < iou_min: break
        if i in frei_w and j in frei_g: frei_w.discard(i); frei_g.discard(j); n += 1
    return n


def main():
    iou_min = arg("--iou", 0.3)
    bilder = []
    for pj in sorted(glob.glob(LERN + "/*.json")):
        try: d = json.load(open(pj, encoding="utf-8"))
        except Exception: continue
        if d.get("status") != "geprueft": continue
        pb = pj[:-5] + ".jpg"
        if not os.path.exists(pb): continue
        w = [[b["x0"], b["y0"], b["x1"], b["y1"]] for b in d.get("boxen", []) if b.get("klasse", "tier") == "tier"]
        q = [b.get("quelle", "hand") for b in d.get("boxen", []) if b.get("klasse", "tier") == "tier"]
        if w: bilder.append({"jpg": pb, "wahr": w, "quelle": q})
    print(f"Grundlage: {len(bilder)} gepruefte Lernbilder mit zusammen {sum(len(b['wahr']) for b in bilder)} Tier-Rahmen "
          f"(davon {sum(1 for b in bilder for x in b['quelle'] if x == 'hand')} von Hand nachgetragen)")
    print(f"Ohne Ortsfest-Maske (keine Videos mehr) -- Genauigkeit durchweg zu niedrig, der Vergleich der Schwellen gilt.\n")
    E = {s: {"wahr": 0, "funde": 0, "treffer": 0, "roh": 0, "roh_hand": 0, "wahr_hand": 0} for s in SCHWELLEN}
    t0 = time.time()
    for b in bilder:
        im = cv2.imread(b["jpg"])
        if im is None: continue
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); S = hsv[:, :, 1]; V = hsv[:, :, 2]
        fenster = (V > V_MIN) & (V < V_MAX)
        for s in SCHWELLEN:
            g = gebiete(im, s); e = E[s]
            e["wahr"] += len(b["wahr"]); e["funde"] += len(g); e["treffer"] += paaren(b["wahr"], g, iou_min)
            durch = (S > s) & fenster
            for box, q in zip(b["wahr"], b["quelle"]):
                x0, y0, x1, y1 = box; dx, dy = (x1-x0)//3, (y1-y0)//3
                k = durch[y0+dy:y1-dy, x0+dx:x1-dx]
                tr = k.size and int(k.sum()) >= ROH_MIN
                if tr: e["roh"] += 1
                if q == "hand":
                    e["wahr_hand"] += 1
                    if tr: e["roh_hand"] += 1
    print(f"gerechnet in {time.time()-t0:.0f} s\n")
    print("  S   | A: ganze Farbregel                      | B: Rohmass (nur Saettigung, keine Form)")
    print("      | Funde  Treffer  Trefferq.  Genauigk.    | Tiere erkannt   davon die von Hand")
    for s in SCHWELLEN:
        e = E[s]
        tq = 100.0*e["treffer"]/max(e["wahr"], 1); gn = 100.0*e["treffer"]/max(e["funde"], 1)
        rq = 100.0*e["roh"]/max(e["wahr"], 1); rh = 100.0*e["roh_hand"]/max(e["wahr_hand"], 1)
        marke = "  <= heute" if s == 40 else ""
        print(f" {s:3d}  | {e['funde']:5d}  {e['treffer']:7d}  {tq:8.1f}%  {gn:9.1f}%    | {rq:12.1f}%  {rh:16.1f}%{marke}")
    beste = max(SCHWELLEN, key=lambda s: 100.0*E[s]["treffer"]/max(E[s]["wahr"],1) - 100.0*(E[s]["funde"]-E[s]["treffer"])/max(E[s]["wahr"],1))
    e40, eb = E[40], E[beste]
    print(f"\n  Beste Schwelle nach Treffer minus Fehlalarm: S = {beste}")
    print(f"  Trefferquote {100.0*e40['treffer']/max(e40['wahr'],1):.1f} % bei 40  ->  "
          f"{100.0*eb['treffer']/max(eb['wahr'],1):.1f} % bei {beste}")
    print(f"  Fehlalarme {e40['funde']-e40['treffer']} bei 40  ->  {eb['funde']-eb['treffer']} bei {beste}")
    print(f"  Von Hand nachgetragene Tiere im Rohmass: {100.0*e40['roh_hand']/max(e40['wahr_hand'],1):.1f} % bei 40  ->  "
          f"{100.0*eb['roh_hand']/max(eb['wahr_hand'],1):.1f} % bei {beste}")
    json.dump({"schwellen": {str(s): E[s] for s in SCHWELLEN}, "beste": beste, "iou": iou_min},
              open(f"befund_farbschwelle_{time.strftime('%Y-%m-%d')}.json", "w", encoding="utf-8"))
    print(f"\ngeschrieben: befund_farbschwelle_{time.strftime('%Y-%m-%d')}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
