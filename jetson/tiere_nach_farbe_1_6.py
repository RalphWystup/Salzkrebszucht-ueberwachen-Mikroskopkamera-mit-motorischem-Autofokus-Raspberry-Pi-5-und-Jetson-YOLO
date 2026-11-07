#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tiere_nach_farbe_1.6.py -- 1.6 (05.11.2026, 08:00): dunkler Teil wieder wie 1.2 (Maske aus dem Medianbild, V < 140,
breit), nur der braune Teil mit dem neuen Ausschluss ortsfester brauner Flaechen (>= 80 % der Bilder braun). 1.5 liess mit
der engen Dunkel-Maske ueberall dunkle Flackerstuecke durch (012856: 172 statt 95 "Tiere"). 1.5 (05.11.2026, 07:55): je Teil eine eigene Ortsfest-Maske. 1.3/1.4 nahmen EINE Maske
(dunkel ODER braun, dunkel hiess V < 140) und zogen sie auch vom braunen Rumpf ab -- der Untergrund liegt aber bei
V 130..160, also galt ein Drittel des Felds als "ortsfest dunkel", und Tiere darueber verschwanden (000749: 63 -> 25).
Jetzt: braune Flaeche, die in >= 80 % der Bilder braun ist, faellt aus dem Rumpf; dunkle Flaeche (V < 120, S < 40),
die in >= 80 % der Bilder dunkel ist, faellt aus dem Kopf. 1.4 (05.11.2026, 07:50): ortsfest heisst "in >= 80 % der Bilder braun bzw. dunkel"
(je Bildpunkt gezaehlt), nicht "im Medianbild". Das Medianbild (1.3) deckte in 004257 ein Tier ab, das 120 Bilder lang in
einer kleinen Gegend kreiste (109 -> 32 Tiere); ein liegendes Korn ist in 100 % der Bilder braun, ein kreisendes Tier
deckt keinen Bildpunkt 80 % der Zeit. 1.3 (05.11.2026, 07:40): auch BRAUNE ortsfeste Flaechen fallen heraus. Morgen-Saetze
(072037..072049) zeigten dunkelbraune, koernige, ortsfeste Objekte in Gruppen (~20 px), die 1.2 in jedem Bild als
"Tier" zaehlte (1,6 je Bild) -- der Beobachter verfolgt sie zu Recht nicht. Die Maske kommt aus dem Medianbild:
was dort braun ODER dunkel ist, ist ortsfest. Ein Tier, das die ganze Aufnahme (5 s) stillsteht, faellt damit
ebenfalls heraus -- wie beim Beobachter. 1.2 (05.11.2026): ein Tier ist brauner RUMPF (S > SAT) plus dunkelgrauer KOPF
(V < V_KOPF, S < 40, nicht ortsfest -- ortsfeste dunkle Flaechen wie Folienschrift kommen aus dem Medianbild);
Teile naeher als GRUPPE px gehoeren zusammen. Gemessen an 20261105_004257: der Kopf (205..418 px, dunkelgrau) lief
als eigenes Objekt 20..40 px neben dem braunen Rumpf, und 1.1 zaehlte ihn als "Rahmen ohne Tier". 1.1: Tierlagen je
Bild. -- misst an den ROHBILDERN einer Aufnahme, wo die Tiere sind, und haelt
das gegen die Rahmen des Beobachters (<name>.jsonl). Laeuft auf dem Pi (oder hier), liest
<name>.avi + <name>.jsonl, schreibt <name>_farbe.jsonl (je Bild) und <name>_farbe.jpg (Ausschnitte
der Rohbilder: weiss = Tier nach Farbe, farbig = Rahmen des Beobachters) sowie eine Zusammenfassung.

Sein Wort, 04.11.2026: "du brauchst die echten bilder! und die daten der dazugehoerigen rahmen und das
synchron so wie ich es auch sehe!" und "wenn du den versatz zwischen den rahmen und den tieren aus den
daten nicht erkennst liest du falsch!"

Tier nach Farbe: Saettigung > SAT (gemessen 05.11.2026 an 20261105_000749: Koerper S 40..140,
Hintergrund S 4..22, Folienschrift dunkel V<70, Blasen S<5), V in 40..235 (scharfe Tiere sind dunkelbraun, V 45..70), oeffnen 3x3, schliessen 7x7,
Gebiete ab FLAECHE_MIN. Das ist KEINE Bewegungserkennung -- es ist die unabhaengige zweite Messung,
gegen die der Melder gehalten wird (Grundsatz: zwei unabhaengige Wege).

  python3 tiere_nach_farbe_1.6.py /home/pi/wache/halten/20261105_000749
"""
import sys, os, json
import numpy as np, cv2

SAT, V_MIN, V_MAX = 40, 40, 235
V_KOPF, GRUPPE = 120, 15                  # 1.2: dunkelgrauer Kopf; Teile naeher als 15 px gehoeren zu einem Tier
STATISCH = None                           # 1.2: Maske ortsfester dunkler Flaechen (Medianbild), von main() gesetzt
FLAECHE_MIN, FLAECHE_MAX = 150, 6000
AUS = (slice(40, 440), slice(60, 580))     # derselbe Ausschnitt wie im Beobachter
KERN_AUF, KERN_ZU = np.ones((3, 3), np.uint8), np.ones((7, 7), np.uint8)
FARBEN = [(0x5e,0xc5,0x22),(0xf6,0x82,0x3b),(0x0b,0x9e,0xf5),(0x9e,0x27,0xec),
          (0xd0,0xb8,0x14),(0x4b,0x4b,0xef),(0x16,0xb8,0x84),(0x2b,0xcc,0x84)]


def statische_maske(bilder, anteil=0.8):
    """1.5: zwei Masken -- (braun_fest, dunkel_fest): Bildpunkt in >= anteil der (jedes dritten) Bilder braun bzw. dunkel; +4 px Rand."""
    sb = sd = None; n = 0
    for im in bilder[::3]:
        hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
        b = ((hsv[:, :, 1] > SAT) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint16)
        d = ((hsv[:, :, 2] < V_KOPF) & (hsv[:, :, 1] < 40)).astype(np.uint16)
        sb = b if sb is None else sb + b; sd = d if sd is None else sd + d; n += 1
    k = np.ones((9, 9), np.uint8)
    med = np.median(np.stack([im[AUS] for im in bilder[::3]]), axis=0).astype(np.uint8)          # 1.6: dunkel wie 1.2
    dunkel_fest = cv2.dilate((cv2.cvtColor(med, cv2.COLOR_BGR2HSV)[:, :, 2] < V_KOPF + 20).astype(np.uint8), k)
    return (cv2.dilate((sb >= anteil * n).astype(np.uint8), k), dunkel_fest)


def tiere_im_bild(im):
    """Tiere = brauner Rumpf + dunkelgrauer Kopf, gruppiert; Koordinaten im vollen Bild. lab: Gruppenkennung je Punkt."""
    hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
    rumpf = ((hsv[:, :, 1] > SAT) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint8)
    kopf = ((hsv[:, :, 2] < V_KOPF) & (hsv[:, :, 1] < 40)).astype(np.uint8)
    if STATISCH is not None: rumpf[STATISCH[0] > 0] = 0; kopf[STATISCH[1] > 0] = 0   # 1.5: je Teil die eigene Maske
    m = cv2.morphologyEx(np.maximum(rumpf, kopf), cv2.MORPH_OPEN, KERN_AUF)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, KERN_ZU)
    grob = cv2.dilate(m, np.ones((GRUPPE + 1, GRUPPE + 1), np.uint8))          # Gruppen naher Teile
    nn, labg, st, _ = cv2.connectedComponentsWithStats(grob, 8)
    lab = np.where(m > 0, labg, 0).astype(np.int32)                             # echte Punkte je Gruppe
    aus = []
    for i in range(1, nn):
        ys, xs = np.nonzero(lab == i); a = int(len(xs))
        if not (FLAECHE_MIN <= a <= FLAECHE_MAX): continue
        aus.append({"a": a, "x": round(float(xs.mean()) + AUS[1].start, 1), "y": round(float(ys.mean()) + AUS[0].start, 1),
                    "rx": int(xs.min()) + AUS[1].start, "ry": int(ys.min()) + AUS[0].start,
                    "rb": int(xs.max() - xs.min()) + 1, "rh": int(ys.max() - ys.min()) + 1, "lab": i,
                    "braun": int(rumpf[ys, xs].sum()), "dunkel": int(kopf[ys, xs].sum())})
    return aus, lab


def anteil_im_rahmen(lab, tier, r):
    """Anteil der Punkte des Farbgebiets, die im Rahmen r des Beobachters liegen."""
    ys, xs = np.nonzero(lab == tier["lab"]); xs = xs + AUS[1].start; ys = ys + AUS[0].start
    return float(((xs >= r["rx"]) & (xs < r["rx"] + r["rb"]) & (ys >= r["ry"]) & (ys < r["ry"] + r["rh"])).mean())


def main(stamm):
    name = os.path.basename(stamm)
    z = [json.loads(l) for l in open(stamm + ".jsonl", encoding="utf-8") if l.strip()]
    kopf, rahmen = z[0], {b["b"]: b["objekte"] for b in z[1:]}
    cap = cv2.VideoCapture(stamm + ".avi"); alle = []
    while True:
        ok, im = cap.read()
        if not ok: break
        alle.append(im)
    global STATISCH; STATISCH = statische_maske(alle)
    n = 0; aus = []; schnitte = []
    s_tier = s_erk = s_rahmen = s_um = s_rand = s_neben = s_leer = 0; versaetze = []
    for im in alle:
        tiere, lab = tiere_im_bild(im)
        rr = [r for r in rahmen.get(n, []) if not r.get("ruht")]
        zeile = {"b": n, "tiere_farbe": len(tiere), "rahmen": len(rr), "paare": [],
                 "tiere": [{k_: t[k_] for k_ in ("a", "x", "y", "rx", "ry", "rb", "rh", "braun", "dunkel")} for t in tiere]}   # 1.1: Tierlagen je Bild
        getroffen = set()
        for r in rr:
            best = None
            for k, t in enumerate(tiere):
                p = anteil_im_rahmen(lab, t, r)
                if best is None or p > best[0]: best = (p, k, t)
            if best is None or best[0] == 0.0:
                zeile["paare"].append({"nr": r["nr"], "tier": None, "urteil": "Rahmen ohne Tier"}); s_leer += 1
                schnitte.append((n, im, r, None, "leer")); continue
            p, k, t = best; getroffen.add(k)
            v = float(np.hypot(t["x"] - (r["rx"] + r["rb"] / 2), t["y"] - (r["ry"] + r["rh"] / 2)))
            u = "um" if p >= 0.6 else ("rand" if p >= 0.25 else "neben")
            {"um": None}  # noqa
            if u == "um": s_um += 1
            elif u == "rand": s_rand += 1
            else: s_neben += 1
            versaetze.append(v)
            zeile["paare"].append({"nr": r["nr"], "tier": k, "im_rahmen": round(p, 3), "versatz_px": round(v, 1), "urteil": u})
            schnitte.append((n, im, r, t, u))
        for k, t in enumerate(tiere):
            if k not in getroffen:
                schnitte.append((n, im, None, t, "verpasst"))
        zeile["verpasst"] = len(tiere) - len(getroffen)
        s_tier += len(tiere); s_erk += len(getroffen); s_rahmen += len(rr)
        aus.append(zeile); n += 1
    cap.release()
    with open(stamm + "_farbe.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "bilder": n, "sat": SAT, "v_kopf": V_KOPF, "gruppe": GRUPPE, "flaeche_min": FLAECHE_MIN, "fassung": "1.6"}) + "\n")
        for zl in aus: f.write(json.dumps(zl, separators=(",", ":")) + "\n")
    # Ausschnitte: Rohbild, Tier nach Farbe weiss, Rahmen farbig; zuerst die verpassten und die danebenliegenden
    reihenfolge = {"verpasst": 0, "neben": 1, "leer": 2, "rand": 3, "um": 4}
    schnitte.sort(key=lambda s: (reihenfolge[s[4]], s[0]))
    kacheln = []
    for (i, im, r, t, u) in schnitte[:64]:
        q = t if t is not None else r
        cx, cy = int(q["x"]), int(q["y"]); R = 40
        im2 = im.copy()
        if t is not None: cv2.rectangle(im2, (t["rx"], t["ry"]), (t["rx"] + t["rb"], t["ry"] + t["rh"]), (255, 255, 255), 1)
        if r is not None: cv2.rectangle(im2, (r["rx"] - 2, r["ry"] - 2), (r["rx"] + r["rb"] + 2, r["ry"] + r["rh"] + 2), FARBEN[r["nr"] % len(FARBEN)], 1)
        s = im2[max(0, cy - R):cy + R, max(0, cx - R):cx + R]
        s = cv2.copyMakeBorder(s, 0, 2 * R - s.shape[0], 0, 2 * R - s.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30))
        cv2.putText(s, f"{i}:{r['nr'] if r else '-'} {u}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, .36, (255, 255, 255), 1, cv2.LINE_AA)
        kacheln.append(s)
    if kacheln:
        sp = 8; ab = np.full((((len(kacheln) + sp - 1) // sp) * 80, sp * 80, 3), 30, np.uint8)
        for k, s in enumerate(kacheln):
            r_, c_ = divmod(k, sp); ab[r_*80:(r_+1)*80, c_*80:(c_+1)*80] = s
        cv2.imwrite(stamm + "_farbe.jpg", ab, [cv2.IMWRITE_JPEG_QUALITY, 80])
    bilder_mit_tier = sum(1 for zl in aus if zl["tiere_farbe"]); bilder_mit_rahmen = sum(1 for zl in aus if zl["rahmen"])
    v = np.array(versaetze) if versaetze else np.array([0.0])
    print(f"{name}: {n} Bilder. Bilder mit Tier nach Farbe: {bilder_mit_tier}, mit Rahmen des Beobachters: {bilder_mit_rahmen}")
    print(f"  Tiere nach Farbe gesamt {s_tier}, davon von einem Rahmen getroffen {s_erk} = {100*s_erk/max(s_tier,1):.0f} % (verpasst {s_tier-s_erk})")
    print(f"  Rahmen gesamt {s_rahmen}: um das Tier {s_um}, am Rand {s_rand}, neben dem Tier {s_neben}, ohne Tier {s_leer}")
    print(f"  Versatz Rahmenmitte -> Tier (Farbe): Median {np.median(v):.1f} px, 90 % unter {np.percentile(v,90):.1f} px, groesster {v.max():.1f} px")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].replace(".jsonl", "").replace(".avi", "")) if len(sys.argv) > 1 else (print(__doc__) or 1))
