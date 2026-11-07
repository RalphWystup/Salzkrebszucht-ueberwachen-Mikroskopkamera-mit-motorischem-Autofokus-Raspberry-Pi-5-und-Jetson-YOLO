#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_verschmelzung_montage_1.0.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

jetson_nummernwechsel_1.1.py hat gemessen: in 1,09 % der Rahmen des Beobachters liegen ZWEI ODER MEHR
Farbgebiete, im Abstand von 30 bis 173 px (Median 76). Das ist ein VERDACHT auf Verschmelzung zweier Tiere
unter einer Nummer -- bewiesen ist er nicht. Die gleiche Messung passt auch auf ein einziges Tier, dessen
brauner Rumpf und dunkler Kopf von der Farbregel nicht zusammengelegt wurden (sie legt nur Teile naeher als
15 px zusammen). Zwischen beiden kann nur das Bild entscheiden.

Dieses Programm holt die Faelle aus den Rohvideos und legt sie 3-fach vergroessert nebeneinander:
gelb = Rahmen des Beobachters (eine Nummer), rot/gruen = die Farbgebiete darin, mit Abstand beschriftet.
Gewaehlt werden Faelle aus moeglichst vielen verschiedenen Saetzen und ueber die ganze Abstandsspanne.

Schreibt MONTAGE_VERSCHMELZUNG_<datum>.jpg und verschmelzung_<datum>.json. Sonst nur lesen.

  python3 jetson_verschmelzung_montage_1.0.py [--kacheln 12] [--grenze_s 600]
"""
import os, sys, json, glob, time
import numpy as np, cv2

A = os.path.join(os.path.expanduser("~/mikroskop"), "aufnahmen")


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1] if n in sys.argv else v)


def faelle_suchen(grenze):
    """Alle Rahmen mit zwei oder mehr Farbgebieten, in Saetzen die noch ein Video haben."""
    aus = []; t0 = time.time()
    staemme = sorted(p[:-6] for p in glob.glob(A + "/*.jsonl") if not p.endswith("_farbe.jsonl")
                     and os.path.exists(p[:-6] + "_farbe.jsonl") and os.path.exists(p[:-6] + ".avi"))
    for s in staemme:
        if time.time() - t0 > grenze: break
        try:
            z = [json.loads(l) for l in open(s + ".jsonl", encoding="utf-8") if l.strip()]
            fz = [json.loads(l) for l in open(s + "_farbe.jsonl", encoding="utf-8") if l.strip()]
        except Exception: continue
        farbe = {w["b"]: w.get("tiere", []) for w in fz[1:]}
        bahnen = {}
        for b in z[1:]:
            for o in b.get("objekte", []):
                if not o.get("ruht"): bahnen[o["nr"]] = bahnen.get(o["nr"], 0) + 1
        tiere = {n for n, c in bahnen.items() if c >= 5}
        for b in z[1:]:
            tt = farbe.get(b["b"])
            if not tt: continue
            for o in b.get("objekte", []):
                if o.get("ruht") or o["nr"] not in tiere: continue
                drin = [t for t in tt if o["rx"] <= t["x"] < o["rx"] + o["rb"] and o["ry"] <= t["y"] < o["ry"] + o["rh"]]
                if len(drin) >= 2:
                    d = min(((drin[i]["x"]-drin[j]["x"])**2 + (drin[i]["y"]-drin[j]["y"])**2) ** 0.5
                            for i in range(len(drin)) for j in range(i+1, len(drin)))
                    aus.append({"satz": os.path.basename(s), "bild": b["b"], "nr": o["nr"],
                                "rahmen": [o["rx"], o["ry"], o["rb"], o["rh"]],
                                "gebiete": [{"x": t["x"], "y": t["y"], "rx": t["rx"], "ry": t["ry"],
                                             "rb": t["rb"], "rh": t["rh"], "a": t["a"],
                                             "braun": t.get("braun"), "dunkel": t.get("dunkel")} for t in drin],
                                "abstand": round(d, 1)})
    return aus


def main():
    n_k = arg("--kacheln", 12); grenze = arg("--grenze_s", 600.0)
    f = faelle_suchen(grenze)
    print(f"Verschmelzungsverdacht: {len(f)} Faelle in Saetzen mit Video")
    if not f: print("nichts zu zeigen"); return 1
    # Auswahl: ueber die Abstandsspanne gestreut, moeglichst verschiedene Saetze
    f.sort(key=lambda x: x["abstand"])
    wahl = []; benutzt = {}
    for i in np.linspace(0, len(f) - 1, min(n_k * 3, len(f))).astype(int):
        c = f[int(i)]
        if benutzt.get(c["satz"], 0) >= 2: continue
        if any(w["satz"] == c["satz"] and abs(w["bild"] - c["bild"]) < 20 for w in wahl): continue
        wahl.append(c); benutzt[c["satz"]] = benutzt.get(c["satz"], 0) + 1
        if len(wahl) >= n_k: break
    print(f"gezeigt: {len(wahl)} Faelle aus {len(benutzt)} Saetzen, Abstand "
          f"{min(w['abstand'] for w in wahl):.0f} .. {max(w['abstand'] for w in wahl):.0f} px\n")
    GROSS = 3; KB, KH = 300, 230
    sp = 4; ze = (len(wahl) + sp - 1) // sp
    tafel = np.full((ze * (KH + 20), sp * KB, 3), 25, np.uint8)
    for i, c in enumerate(wahl):
        cap = cv2.VideoCapture(os.path.join(A, c["satz"] + ".avi"))
        cap.set(cv2.CAP_PROP_POS_FRAMES, c["bild"]); ok, im = cap.read(); cap.release()
        if not ok: continue
        x, y, w, h = c["rahmen"]; rand = 14
        x0, y0 = max(0, x - rand), max(0, y - rand)
        x1, y1 = min(im.shape[1], x + w + rand), min(im.shape[0], y + h + rand)
        aus = im[y0:y1, x0:x1].copy()
        aus = cv2.resize(aus, (0, 0), fx=GROSS, fy=GROSS, interpolation=cv2.INTER_NEAREST)
        cv2.rectangle(aus, ((x - x0) * GROSS, (y - y0) * GROSS), ((x - x0 + w) * GROSS, (y - y0 + h) * GROSS), (0, 220, 255), 1)
        for k, g in enumerate(c["gebiete"][:3]):
            farbe = [(60, 60, 255), (60, 255, 60), (255, 160, 60)][k]
            cv2.rectangle(aus, ((g["rx"] - x0) * GROSS, (g["ry"] - y0) * GROSS),
                          ((g["rx"] - x0 + g["rb"]) * GROSS, (g["ry"] - y0 + g["rh"]) * GROSS), farbe, 1)
            cv2.putText(aus, f"{g['a']}px br{g['braun']} du{g['dunkel']}", ((g["rx"] - x0) * GROSS, max(9, (g["ry"] - y0) * GROSS - 3)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, farbe, 1)
        sk = min((KB - 6) / aus.shape[1], (KH - 6) / aus.shape[0], 1.0)
        if sk < 1.0: aus = cv2.resize(aus, (0, 0), fx=sk, fy=sk)
        r, s_ = divmod(i, sp); oy = r * (KH + 20); ox = s_ * KB
        tafel[oy:oy + aus.shape[0], ox:ox + aus.shape[1]] = aus
        cv2.putText(tafel, f"{c['satz']} b{c['bild']} Nr{c['nr']} Abstand {c['abstand']:.0f}px",
                    (ox + 3, oy + KH + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
        print(f"  {c['satz']} Bild {c['bild']} Nummer {c['nr']}: Rahmen {w}x{h} px, {len(c['gebiete'])} Gebiete, "
              f"Abstand {c['abstand']:.0f} px, Flaechen {[g['a'] for g in c['gebiete']]}")
    heute = time.strftime("%Y-%m-%d"); p = f"MONTAGE_VERSCHMELZUNG_{heute}.jpg"
    cv2.imwrite(p, tafel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    json.dump({"faelle": len(f), "gezeigt": wahl}, open(f"verschmelzung_{heute}.json", "w", encoding="utf-8"))
    print(f"\ngeschrieben: {p} ({tafel.shape[1]}x{tafel.shape[0]}) und verschmelzung_{heute}.json")
    print("gelb = Rahmen des Beobachters, rot/gruen/blau = Farbgebiete darin (Flaeche, braune und dunkle Punkte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
