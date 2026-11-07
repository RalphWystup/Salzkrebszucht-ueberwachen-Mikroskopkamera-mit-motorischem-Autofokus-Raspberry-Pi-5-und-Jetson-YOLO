#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_lernbilder_auswahl_1.0.py -- laeuft auf dem Jetson: sein Wort "ich will nur 50 aussagekraeftige bilder fuer den ersten versuch".
Von den OFFENEN Lernbildern bleiben die 50 besten offen (Wert = Zahl der Vorschlagsrahmen + Schaerfe (Laplace-Varianz, auf 0..3 skaliert),
hoechstens zwei je Satz, ueber die Zeit verteilt), alle anderen offenen bekommen den Stand "zurueckgestellt" (nicht geloescht, spaeter wieder
aufrufbar). Geprueft/verworfen bleiben unberuehrt. Ausgabe AUSWAHLJSON."""
import os, glob, json, cv2, numpy as np, collections
L = os.path.expanduser("~/mikroskop/lernen/bilder"); N = 50
kand = []
for pj in sorted(glob.glob(L + "/*.json")):
    d = json.load(open(pj, encoding="utf-8"))
    if d.get("status") != "offen": continue
    pb = pj[:-5] + ".jpg"; im = cv2.imread(pb, cv2.IMREAD_GRAYSCALE)
    if im is None: continue
    schaerfe = float(cv2.Laplacian(im, cv2.CV_64F).var()); kand.append((pj, d, len(d.get("boxen", [])), schaerfe))
if kand:
    s_max = max(k[3] for k in kand) or 1.0
    bewertet = sorted(((k[2] + 3 * k[3] / s_max, k) for k in kand), key=lambda x: -x[0])
    gewaehlt = []; je_satz = collections.Counter()
    for w, k in bewertet:
        satz = k[1].get("satz", os.path.basename(k[0])[:15])
        if je_satz[satz] >= 2: continue
        gewaehlt.append(k); je_satz[satz] += 1
        if len(gewaehlt) >= N: break
    namen = {k[0] for k in gewaehlt}; zurueck = 0
    for pj, d, nb, sch in kand:
        if pj not in namen:
            d["status"] = "zurueckgestellt"; json.dump(d, open(pj, "w", encoding="utf-8")); zurueck += 1
    z = collections.Counter(json.load(open(p)).get("status") for p in glob.glob(L + "/*.json"))
    print("AUSWAHLJSON", json.dumps({"offen_vorher": len(kand), "gewaehlt": len(gewaehlt), "zurueckgestellt": zurueck, "staende": dict(z), "rahmen_in_auswahl": sum(k[2] for k in gewaehlt), "saetze": len(je_satz)}))
else: print("AUSWAHLJSON", json.dumps({"offen_vorher": 0}))
