#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_zaehlgenauigkeit_1.1.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Zwei Zwecke in einem Durchgang:

  Problem 9 des Plans -- "Farbpruefung hat blinde Flecken (ortsfeste braune Koerner, dunkler Druck, Rand);
  Pruefwerkzeug, kein Beweis; sein Auge an den Ausschnitten." Hier wird der blinde Fleck SICHTBAR gemacht:
  seine von Hand nachgetragenen Rahmen sind genau die Objekte, die Farbregel und Auswertung nicht
  vorgeschlagen haben. Sie kommen als 3-fach vergroesserte Ausschnitte in eine Montage.

  Massstab aus abstract64.pdf (Wang & De Baets 2019, Gent): 99,6 % Erkennungsgenauigkeit auf Standbildern,
  gemessen gegen von Hand gezaehlte Bilder. Dieselbe Messung hier: YOLO und Farbregel gegen SEINE Rahmen.

Ehrlichkeitsvorbehalt, der mitgemessen wird:
  - YOLO wurde auf eben diesen geprueften Bildern angelernt. Die Aufteilung des Datensatzes (85/15 nach
    md5 des Namens, wie in jetson_yolo_datensatz_1.1.py) wird hier nachgebildet; Lern- und Pruefteil
    werden GETRENNT ausgewiesen. Nur der Pruefteil ist ein fairer Wert, und er ist klein.
  - Die Farbregel hat die meisten Vorschlagsrahmen selbst geliefert; ihre Trefferquote gegen diese Rahmen
    ist darum geschoent. Aussagekraeftig ist allein, wie sie auf den von HAND nachgetragenen Rahmen abschneidet.

1.1 (07.11.2026) berichtigt zwei Fehler von 1.0, beide am Ergebnis erkannt:
  - 1.0 rechnete die Farbregel auf dem Lernbild NEU. Zu keinem der 52 Bilder gab es noch ein Video, also fehlte
    die Ortsfest-Maske (die den dunklen Aufdruck und liegende Koerner ausblendet) -- gemessen wurde eine Regel,
    die so nie gelaufen ist (230 Funde, 26 Treffer). 1.1 nimmt die AUFGEZEICHNETE Farbwahrheit aus
    aufnahmen/<satz>_farbe.jsonl, Bild <n>: das ist genau das, was die Regel damals mit Maske gefunden hat.
  - 1.0 mass YOLO nur bei Schwelle 0,4. Ob ein Modell nichts findet oder nur unsicher ist, trennt erst eine
    Reihe von Schwellen. 1.1 rechnet einmal bei 0,10 und wertet 0,10 / 0,25 / 0,40 aus.

Nur lesen (ausser der geschriebenen Montage und den Befundblaettern). Der Livedienst bleibt unangetastet:
YOLO laeuft hier auf dem Prozessor (device cpu).

  python3 jetson_zaehlgenauigkeit_1.1.py [--iou 0.3] [--montage 8]
"""
import os, sys, json, glob, time, hashlib

YOLO_PY = os.path.expanduser("~/<yolo-umgebung>/bin/python")
# 1.1 (07.11.2026): NICHT am Programmpfad erkennen, ob wir in der richtigen Umgebung sind -- bin/python einer
# Umgebung ist ein Verweis auf /usr/bin/python3, der Pfadvergleich geht darum immer "gleich" aus und der Wechsel
# unterblieb. Entscheidend ist, ob torch da ist. (Gemessen 07.11.2026: das System-Python findet ein ultralytics
# in ~/.local OHNE torch -- der Auftrag brach mit ModuleNotFoundError ab.)
def _hat_torch():
    try:
        import importlib.util
        return importlib.util.find_spec("torch") is not None
    except Exception:
        return False
if "--im-yolo-python" not in sys.argv and not _hat_torch() and os.path.exists(YOLO_PY):
    os.execv(YOLO_PY, [YOLO_PY, "-u", os.path.abspath(__file__)] + sys.argv[1:] + ["--im-yolo-python"])

import numpy as np, cv2

H = os.path.expanduser("~/mikroskop")
LERN = os.path.join(H, "lernen", "bilder"); ABLAGE = os.path.join(H, "aufnahmen")
MODELL = os.path.join(H, "yolo", "modell", "best.pt")
KLASSEN = ["tier", "korn", "massstab"]
# Farbregel, Werte wie tiere_nach_farbe_1.6.py
SAT, V_MIN, V_MAX, V_KOPF, GRUPPE = 40, 40, 235, 120, 15
FLAECHE_MIN, FLAECHE_MAX = 150, 6000
AUS = (slice(40, 440), slice(60, 580))
KERN_AUF, KERN_ZU = np.ones((3, 3), np.uint8), np.ones((7, 7), np.uint8)


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else v


def ueberdeckung(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / max(1e-9, (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)


def statische_maske(bilder, anteil=0.8):
    sb = None; n = 0
    for im in bilder[::3]:
        hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
        b = ((hsv[:, :, 1] > SAT) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint16)
        sb = b if sb is None else sb + b; n += 1
    k = np.ones((9, 9), np.uint8)
    med = np.median(np.stack([im[AUS] for im in bilder[::3]]), axis=0).astype(np.uint8)
    dunkel_fest = cv2.dilate((cv2.cvtColor(med, cv2.COLOR_BGR2HSV)[:, :, 2] < V_KOPF + 20).astype(np.uint8), k)
    return (cv2.dilate((sb >= anteil * n).astype(np.uint8), k), dunkel_fest)


def farbregel(im, statisch):
    """Gebiete der Farbregel als Rahmen im vollen Bild -- dieselbe Regel wie tiere_nach_farbe_1.6."""
    hsv = cv2.cvtColor(im[AUS], cv2.COLOR_BGR2HSV)
    rumpf = ((hsv[:, :, 1] > SAT) & (hsv[:, :, 2] > V_MIN) & (hsv[:, :, 2] < V_MAX)).astype(np.uint8)
    kopf = ((hsv[:, :, 2] < V_KOPF) & (hsv[:, :, 1] < 40)).astype(np.uint8)
    if statisch is not None: rumpf[statisch[0] > 0] = 0; kopf[statisch[1] > 0] = 0
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


def paaren(wahr, gefunden, iou_min):
    """Gierige Zuordnung ueber die Ueberdeckung. Liefert (Paare, nicht gefundene Wahrheiten, ueberzaehlige Funde)."""
    paare = []; frei_w = list(range(len(wahr))); frei_g = list(range(len(gefunden)))
    kand = sorted(((ueberdeckung(wahr[i][:4], gefunden[j][:4]), i, j) for i in frei_w for j in frei_g), reverse=True)
    for u, i, j in kand:
        if u < iou_min: break
        if i in frei_w and j in frei_g:
            paare.append((i, j, u)); frei_w.remove(i); frei_g.remove(j)
    return paare, frei_w, frei_g


def kachel(im, box, gross=3, rand=10):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2; h = max(x1 - x0, y1 - y0) // 2 + rand
    a = im[max(0, cy-h):min(im.shape[0], cy+h), max(0, cx-h):min(im.shape[1], cx+h)]
    if a.size == 0: a = np.zeros((8, 8, 3), np.uint8)
    return cv2.resize(a, (0, 0), fx=gross, fy=gross, interpolation=cv2.INTER_NEAREST)


SCHWELLEN = (0.10, 0.25, 0.40)


def farbe_aufgezeichnet(satz, bild):
    """1.1: die Gebiete, die tiere_nach_farbe_1.6 damals MIT Ortsfest-Maske gefunden hat."""
    p = os.path.join(ABLAGE, satz + "_farbe.jsonl")
    if not os.path.exists(p): return None
    try:
        for l in open(p, encoding="utf-8"):
            if not l.strip(): continue
            d = json.loads(l)
            if d.get("b") == bild:
                return [[t["rx"], t["ry"], t["rx"] + t["rb"], t["ry"] + t["rh"]] for t in d.get("tiere", [])]
    except Exception: return None
    return None


def main():
    iou_min = arg("--iou", 0.3); conf = 0.10; n_montage = arg("--montage", 8)
    bilder = []
    for pj in sorted(glob.glob(LERN + "/*.json")):
        try: d = json.load(open(pj, encoding="utf-8"))
        except Exception: continue
        if d.get("status") != "geprueft": continue
        pb = pj[:-5] + ".jpg"
        if not os.path.exists(pb): continue
        name = os.path.basename(pj)[:-5]
        teil = "pruef" if int(hashlib.md5(name.encode()).hexdigest()[:4], 16) % 100 < 15 else "lern"
        bilder.append({"name": name, "jpg": pb, "teil": teil, "satz": d.get("satz"), "bild": d.get("bild"),
                       "boxen": [{"box": [b["x0"], b["y0"], b["x1"], b["y1"]],
                                  "klasse": b.get("klasse", "tier"), "quelle": b.get("quelle", "hand")} for b in d.get("boxen", [])]})
    if not bilder: print("keine geprueften Lernbilder gefunden"); return 1
    hand = sum(1 for b in bilder for x in b["boxen"] if x["quelle"] == "hand")
    alle_boxen = sum(len(b["boxen"]) for b in bilder)
    quellen = {}
    for b in bilder:
        for x in b["boxen"]: quellen[x["quelle"]] = quellen.get(x["quelle"], 0) + 1
    print(f"Grundlage: {len(bilder)} gepruefte Lernbilder (seine Rahmen = Wahrheit), {alle_boxen} Rahmen.")
    print(f"  Lernteil {sum(1 for b in bilder if b['teil']=='lern')}, Pruefteil {sum(1 for b in bilder if b['teil']=='pruef')} (Aufteilung wie im Datensatz)")
    print(f"  Rahmen nach Herkunft: {quellen}")
    print(f"  davon von HAND nachgetragen: {hand} -- das sind die blinden Flecken der Vorschlaege (Problem 9)")
    kl = {}
    for b in bilder:
        for x in b["boxen"]: kl[x["klasse"]] = kl.get(x["klasse"], 0) + 1
    print(f"  Rahmen nach Klasse: {kl}\n")

    from ultralytics import YOLO
    if not os.path.exists(MODELL): print(f"Modell fehlt: {MODELL}"); return 1
    netz = YOLO(MODELL)
    print(f"Modell {MODELL} ({time.strftime('%d.%m. %H:%M', time.localtime(os.path.getmtime(MODELL)))}), "
          f"Schwelle {conf}, Ueberdeckung {iou_min}, Rechenwerk: Prozessor\n")

    statisch_je_satz = {}; ohne_video = set()
    zahl = {s: {t: {k: {"wahr": 0, "treffer": 0, "funde": 0} for k in KLASSEN} for t in ("lern", "pruef")} for s in SCHWELLEN}
    farb = {"wahr_tier": 0, "treffer": 0, "funde": 0, "treffer_hand": 0, "wahr_hand": 0}
    streit = {"yolo_verpasst": [], "yolo_zuviel": [], "farbe_verpasst": [], "farbe_zuviel": []}
    t0 = time.time()
    for b in bilder:
        im = cv2.imread(b["jpg"])
        if im is None: continue
        # --- YOLO
        r = netz.predict(im, device="cpu", conf=conf, verbose=False)[0]
        gef = []
        for box, c, p in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            gef.append([int(box[0]), int(box[1]), int(box[2]), int(box[3]), KLASSEN[int(c)], float(p)])
        for s in SCHWELLEN:
            for k in KLASSEN:
                w = [x for x in b["boxen"] if x["klasse"] == k]; g = [x for x in gef if x[4] == k and x[5] >= s]
                paare, frei_w, frei_g = paaren([x["box"] for x in w], g, iou_min)
                z = zahl[s][b["teil"]][k]; z["wahr"] += len(w); z["funde"] += len(g); z["treffer"] += len(paare)
                if k == "tier" and abs(s - 0.40) < 1e-9:
                    for i in frei_w: streit["yolo_verpasst"].append((b, w[i]["box"], f"{b['name']} {w[i]['quelle']}"))
                    for j in frei_g: streit["yolo_zuviel"].append((b, g[j][:4], f"{b['name']} {g[j][5]:.2f}"))
        # --- Farbregel: 1.1 nimmt die aufgezeichnete Wahrheit (mit Ortsfest-Maske), sonst Neuberechnung ohne sie
        satz = b.get("satz"); fb = farbe_aufgezeichnet(satz, b.get("bild")) if satz else None
        if fb is None:
            ohne_video.add(satz); fb = farbregel(im, None)
        else: statisch_je_satz[satz] = True
        w_tier = [x for x in b["boxen"] if x["klasse"] == "tier"]
        paare, frei_w, frei_g = paaren([x["box"] for x in w_tier], fb, iou_min)
        farb["wahr_tier"] += len(w_tier); farb["funde"] += len(fb); farb["treffer"] += len(paare)
        getroffen_w = {i for i, _, _ in paare}
        for i, x in enumerate(w_tier):
            if x["quelle"] == "hand":
                farb["wahr_hand"] += 1
                if i in getroffen_w: farb["treffer_hand"] += 1
        for i in frei_w: streit["farbe_verpasst"].append((b, w_tier[i]["box"], f"{b['name']} {w_tier[i]['quelle']}"))
        for j in frei_g: streit["farbe_zuviel"].append((b, fb[j], b["name"]))
    print(f"gerechnet in {time.time()-t0:.0f} s; aufgezeichnete Farbwahrheit fuer {len(statisch_je_satz)} Saetze, "
          f"{len(ohne_video)} Saetze ohne Aufzeichnung (dort Farbregel ohne Ortsfest-Maske, Wert nicht belastbar)\n")

    print("== YOLO gegen seine Rahmen, ueber drei Sicherheitsschwellen")
    print(f"{'Schwelle':>9}{'Teil':>7}{'Klasse':>11}{'Wahrheit':>9}{'Funde':>7}{'Treffer':>8}{'Trefferquote':>14}{'Genauigkeit':>13}")
    for s in SCHWELLEN:
        for teil in ("lern", "pruef"):
            for k in KLASSEN:
                z = zahl[s][teil][k]
                if not z["wahr"] and not z["funde"]: continue
                tq = 100.0 * z["treffer"] / z["wahr"] if z["wahr"] else float("nan")
                gn = 100.0 * z["treffer"] / z["funde"] if z["funde"] else float("nan")
                print(f"{s:9.2f}{teil:>7}{k:>11}{z['wahr']:9d}{z['funde']:7d}{z['treffer']:8d}{tq:13.1f}%{gn:12.1f}%")
    for s in SCHWELLEN:
        zp = zahl[s]["pruef"]["tier"]; zl = zahl[s]["lern"]["tier"]
        print(f"  Schwelle {s:.2f}: Pruefteil Trefferquote {100.0*zp['treffer']/max(zp['wahr'],1):5.1f} % "
              f"(Genauigkeit {100.0*zp['treffer']/max(zp['funde'],1):5.1f} %) | Lernteil Trefferquote "
              f"{100.0*zl['treffer']/max(zl['wahr'],1):5.1f} %")
    print("  Gent (abstract64.pdf) erreicht 99,6 % auf 4671 Objekten -- dort mit 250 Lernbildern.")
    print("  Wichtig: bleibt die Trefferquote auch auf dem LERNTEIL niedrig, hat das Modell nicht zu wenig")
    print("  Sicherheit, sondern zu wenig gelernt. Das ist eine Frage der Menge an bewerteten Bildern.")

    print("\n== Farbregel gegen seine Rahmen (Klasse Tier)")
    print(f"  Wahrheit {farb['wahr_tier']}, Funde {farb['funde']}, Treffer {farb['treffer']}")
    print(f"  Trefferquote {100.0*farb['treffer']/max(farb['wahr_tier'],1):.1f} %, "
          f"Genauigkeit {100.0*farb['treffer']/max(farb['funde'],1):.1f} %  (geschoent: sie hat die Vorschlaege selbst geliefert)")
    print(f"  Auf den von HAND nachgetragenen Rahmen: {farb['treffer_hand']} von {farb['wahr_hand']} = "
          f"{100.0*farb['treffer_hand']/max(farb['wahr_hand'],1):.1f} %  <-- das ist der blinde Fleck (Problem 9)")

    # --- Montage der Streitfaelle, 3-fach vergroessert
    gruppen = [("YOLO verpasst (seine Rahmen ohne YOLO-Fund)", streit["yolo_verpasst"]),
               ("YOLO zuviel (Fund ohne seinen Rahmen)", streit["yolo_zuviel"]),
               ("Farbregel verpasst -- blinder Fleck", streit["farbe_verpasst"]),
               ("Farbregel zuviel -- Fehlalarm", streit["farbe_zuviel"])]
    KH = 180; sp = n_montage
    tafel = np.full(((KH + 26) * len(gruppen), KH * sp, 3), 30, np.uint8)
    for gi, (titel, liste) in enumerate(gruppen):
        y0 = gi * (KH + 26)
        cv2.putText(tafel, f"{titel}  (n = {len(liste)})", (6, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        for ki, (b, box, text) in enumerate(liste[:sp]):
            im = cv2.imread(b["jpg"])
            if im is None: continue
            k = kachel(im, box)
            k = cv2.resize(k, (KH - 4, KH - 4))
            tafel[y0 + 26:y0 + 26 + KH - 4, ki * KH:ki * KH + KH - 4] = k
            cv2.putText(tafel, text[:22], (ki * KH + 3, y0 + 26 + KH - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 255, 255), 1)
    heute = time.strftime("%Y-%m-%d")
    pfad = f"MONTAGE_STREITFAELLE_{heute}.jpg"   # Streitfaelle bei Schwelle 0,40
    cv2.imwrite(pfad, tafel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"\nMontage der Streitfaelle (3-fach vergroessert, vier Zeilen): {pfad}")
    json.dump({"bilder": len(bilder), "rahmen": alle_boxen, "quellen": quellen, "klassen": kl,
               "yolo": {str(s): zahl[s] for s in SCHWELLEN}, "farbe": farb,
               "streit": {k: len(v) for k, v in streit.items()}},
              open(f"befund_problem9_{heute}.json", "w", encoding="utf-8"))
    print(f"geschrieben: befund_problem9_{heute}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
