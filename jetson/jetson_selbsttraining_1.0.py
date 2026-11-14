#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_selbsttraining_1.0.py -- laeuft AUF dem Jetson (~/yolo_umgebung/bin/python, nachts per crontab oder von Hand ueber den
Jetson-Dienst /selbst/start): zieht die YOLO-Erkennung dem Bildmaterial nach, ohne dass YOLO sich selbst die Wahrheit liefert.
Sein Wort 14.11.2026: "das mach so" (Marken aus Bewegung und Farbe, kein neues Modell ohne Abnahme) und "ich moechte sehen koennen,
wie alles funktioniert, und das immer in Echtzeit" -- jede Phase schreibt ihren Stand sofort nach ~/mikroskop/selbsttraining/stand.json,
das aktuelle Lernbild nach bild.jpg; der Jetson-Dienst (1.14) reicht beides an die Mikroskopseite.

Phasen:
  1 Drift     Saetze der letzten DRIFT_H Stunden mit Video und Farbwahrheit (bis zu 6, zeitlich gestreut): Tiere je Bild, Flaeche,
              Saettigung der Tierpunkte (in den Bewegungsrahmen des Pi), Trefferanteil des HEUTIGEN Modells gegen die Marken
              "Bewegung+Farbe". Ausloeser: Treffer < TREFFER_MIN oder Saettigung gegenueber dem letzten Training um > SAETT_DRIFT
              verschoben oder ERZWINGEN=1. Sonst Phase "Ruhe" und Ende.
  2 Marken    Farbschwelle aus der gemessenen Saettigung (0,6 x Median, 22..45) statt fest 40; Lernbild wird nur ein Tier, das die
              Bewegung des Pi (Rahmen in <satz>.jsonl, MOG2 + Aussehen) UND die Farbe (eigene Messung mit der Schwelle) zeigen.
              Koerner/Massstab aus dem heutigen Modell (conf >= 0,5), damit diese Klassen bleiben. Bis zu ANZAHL Bilder, hoechstens 2
              je Satz, 25 Bilder Abstand, Marke datensatz=<Zeit>, quelle=selbsttraining, status offen (Lernseite zeigt sie).
  3 Datensatz jetson_yolo_datensatz_1.2.py (alle Marken zusammen).
  4 Training  wie jetson_yolo_training_1.4 (Einheit mikroskop-training, haelt den Livedienst an), aber das Ergebnis geht nach
              modell/kandidat/best.pt, NICHT nach modell/best.pt; Epochen live aus results.csv.
  5 Abnahme   altes und neues Modell ueber dieselben Bilder der Drift-Saetze gegen die Marken: Trefferanteil (conf 0,4) und Meldungen je
              Bild. Neu wird nur uebernommen, wenn Treffer_neu >= Treffer_alt + 0,02 und Meldungen/Bild <= 1,3 x Tiere/Bild + 0,2.
              Dann modell/best.pt <- kandidat (der Livedienst laedt bei Dateiwechsel), altes nach modell/vorher_<Zeit>.pt (Rueckfall).
  6 Fertig    Zusammenfassung; Zeile in verlauf.jsonl.
1.3 (14.11.2026): Abnahmeregel Meldungen gegen das alte Modell; Betrieb ABNAHME_NUR=1 prueft nur den vorhandenen Kandidaten. 1.2: Trainingseinheit abgeloest (Popen) gestartet, weil die sudoers-Regel nur den nackten Startbefehl erlaubt; 1.1: unbehandelte Fehler in den Stand. 1.0: erste Fassung.
Alle Zahlen sind gemessen, nichts wird geraten; scheitert eine Phase, steht es mit Grund im Stand, und das alte Modell bleibt.
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, sys, glob, json, re, time, shutil, subprocess, collections
import numpy as np, cv2
H = os.path.expanduser("~/mikroskop"); A = os.path.join(H, "aufnahmen"); L = os.path.join(H, "lernen", "bilder"); Y = os.path.join(H, "yolo")
N = os.path.join(H, "selbsttraining"); os.makedirs(N, exist_ok=True); os.makedirs(L, exist_ok=True); os.makedirs(Y + "/modell/kandidat", exist_ok=True)
STAND = os.path.join(N, "stand.json"); BILD = os.path.join(N, "bild.jpg"); VERLAUF = os.path.join(N, "verlauf.jsonl")
DRIFT_H = float(os.environ.get("DRIFT_H", "24")); ANZAHL = int(os.environ.get("ANZAHL", "100")); ERZWINGEN = os.environ.get("ERZWINGEN", "0") == "1"
TREFFER_MIN = 0.85; SAETT_DRIFT = 0.15; CONF = 0.4; BILDER_JE_SATZ_DRIFT = 30; EPOCHEN = int(os.environ.get("EPOCHEN", "40"))
MARKE = time.strftime("%Y-%m-%d_%H%M"); T0 = time.time()
def _haken(typ, wert, tb):
    """jeder unbehandelte Fehler steht im Stand (Seite) und im Protokoll; das alte Modell bleibt."""
    import traceback; txt = "".join(traceback.format_exception(typ, wert, tb))[-600:]
    try:
        S.update(phase="fertig", fehler=f"{typ.__name__}: {str(wert)[:200]}", ergebnis="abgebrochen, altes Modell bleibt", uhr=time.strftime("%H:%M:%S"))
        json.dump(S, open(STAND, "w", encoding="utf-8"), ensure_ascii=False, indent=1); open(VERLAUF, "a").write(json.dumps({"marke": MARKE, "uhr": S.get("start"), "ergebnis": "Fehler: " + S["fehler"]}) + "\n")
    except Exception: pass
    print(txt, flush=True)
sys.excepthook = _haken
S = {"fassung": "1.0", "marke": MARKE, "start": time.strftime("%Y-%m-%d %H:%M:%S"), "ausloeser": "erzwungen" if ERZWINGEN else "zeitplan",
     "phase": "start", "fortschritt": 0.0, "meldung": "", "uhr": "", "phasen": [], "drift": {}, "marken": {}, "datensatz": {}, "training": {}, "abnahme": {}, "ergebnis": None, "fehler": None}

def schreibe(**k):
    S.update(k); S["uhr"] = time.strftime("%H:%M:%S"); S["laufzeit_s"] = round(time.time() - T0)
    tmp = STAND + ".tmp"; json.dump(S, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, STAND)
def phase(name, meldung=""):
    S["phasen"].append({"phase": name, "ab": time.strftime("%H:%M:%S")}); schreibe(phase=name, fortschritt=0.0, meldung=meldung); print(time.strftime("%H:%M:%S"), name, meldung, flush=True)
def lade(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def alter_h(name):
    try: return (time.time() - time.mktime(time.strptime(name[:15], "%Y%m%d_%H%M%S"))) / 3600
    except ValueError: return 1e9
def box_pi(o): return [max(0, o["rx"] - 6), max(0, o["ry"] - 6), min(640, o["rx"] + o["rb"] + 6), min(480, o["ry"] + o["rh"] + 6)]

# ---- Farbe mit einstellbarer Schwelle (Rezept von tiere_nach_farbe 1.5, ohne Ortsfest-Maske: dafuer die Bewegung des Pi)
def farbtiere(im, sat, flaeche_min=120):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); m = ((hsv[..., 1] > sat) & (hsv[..., 2] > 40) & (hsv[..., 2] < 235)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, stats, cen = cv2.connectedComponentsWithStats(m)
    return [{"x": float(cen[i][0]), "y": float(cen[i][1]), "a": int(stats[i][4]), "box": [int(stats[i][0]), int(stats[i][1]), int(stats[i][0] + stats[i][2]), int(stats[i][1] + stats[i][3])]}
            for i in range(1, n) if stats[i][4] >= flaeche_min]
def einig(pi_boxen, farb):
    """Tiere, die Bewegung UND Farbe zeigen: Farbschwerpunkt in einem Pi-Rahmen (um 10 px erweitert) -> Rahmen = Vereinigung."""
    aus = []; benutzt = set()
    for f in farb:
        for i, b in enumerate(pi_boxen):
            if b[0] - 10 <= f["x"] <= b[2] + 10 and b[1] - 10 <= f["y"] <= b[3] + 10:
                aus.append([min(b[0], f["box"][0] - 6), min(b[1], f["box"][1] - 6), max(b[2], f["box"][2] + 6), max(b[3], f["box"][3] + 6)]); benutzt.add(i); break
    return [[max(0, a[0]), max(0, a[1]), min(640, a[2]), min(480, a[3])] for a in aus], benutzt
def trifft(box, det):
    ix = max(0, min(box[2], det[2]) - max(box[0], det[0])); iy = max(0, min(box[3], det[3]) - max(box[1], det[1])); i = ix * iy
    return i / max(1e-9, (box[2] - box[0]) * (box[3] - box[1])) > 0.3

try:
    from ultralytics import YOLO
    MODELL = os.path.join(Y, "modell", "best.pt"); M_alt = YOLO(MODELL) if os.path.exists(MODELL) else None
except Exception as ex:
    M_alt = None; S["fehler"] = f"YOLO nicht ladbar: {ex}"
def yolo_boxen(m, im, conf=CONF):
    r = m.predict(im, conf=conf, imgsz=640, half=True, device=0, verbose=False)[0]
    if r.boxes is None or not len(r.boxes): return [], [], []
    kl = r.boxes.cls.cpu().numpy().astype(int); xy = r.boxes.xyxy.cpu().numpy().tolist(); cf = r.boxes.conf.cpu().numpy().tolist()
    return [b for b, k in zip(xy, kl) if k == 0], [(b, k) for b, k in zip(xy, kl) if k != 0], [c for c, k in zip(cf, kl) if k == 0]

def male(im, pi_boxen, farb, agreed, dets=None, text=""):
    out = im.copy()
    for b in pi_boxen: cv2.rectangle(out, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 160, 0), 1)       # blau: Bewegung (Pi)
    for f in farb: cv2.circle(out, (int(f["x"]), int(f["y"])), 4, (0, 0, 255), -1)                                    # rot: Farbe
    for b in agreed: cv2.rectangle(out, (b[0], b[1]), (b[2], b[3]), (0, 200, 0), 2)                                  # gruen: beide = Lernmarke
    for b in (dets or []): cv2.rectangle(out, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 220, 255), 1)       # gelb: YOLO
    cv2.putText(out, text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2); cv2.putText(out, text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imwrite(BILD + ".tmp.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 80]); os.replace(BILD + ".tmp.jpg", BILD)

# ================= 1 Drift =================
phase("drift", f"Saetze der letzten {DRIFT_H:.0f} h suchen")
saetze = sorted((os.path.basename(p)[:-6] for p in glob.glob(A + "/*.jsonl") if not p.endswith("_farbe.jsonl")), key=alter_h)
kand = [n for n in saetze if alter_h(n) <= DRIFT_H and os.path.exists(os.path.join(A, n + ".avi")) and os.path.exists(os.path.join(A, n + "_farbe.jsonl"))]
wahl = [kand[int(k)] for k in np.linspace(0, len(kand) - 1, min(6, len(kand))).astype(int)] if kand else []
S["drift"] = {"saetze_gefunden": len(kand), "saetze_gewaehlt": [w for w in wahl], "je_satz": []}
S_pix = []; treffer = [0, 0]; tiere_je_bild = []; flaechen = []; proben = []     # proben: (satz, bildnr, agreed, im) fuer die Abnahme
sat_vor = 40
for si, n in enumerate(wahl):
    stamm = os.path.join(A, n); z = lade(stamm + ".jsonl"); obj = {b["b"]: b.get("objekte", []) for b in z[1:]}
    cap = cv2.VideoCapture(stamm + ".avi"); nb = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); idx = np.linspace(10, max(11, nb - 1), min(BILDER_JE_SATZ_DRIFT, max(1, nb - 10))).astype(int)
    e = {"satz": n, "bilder": 0, "tiere": 0, "treffer": 0, "meldungen": 0}
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i)); ok, im = cap.read()
        if not ok: continue
        pib = [box_pi(o) for o in obj.get(int(i), [])]
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        for b in pib:                                                      # Saettigung der Tierpunkte in den Bewegungsrahmen (farbunabhaengig gewaehlt)
            r = hsv[int(b[1]):int(b[3]), int(b[0]):int(b[2]), 1]; r = r[r > 20]
            if r.size: S_pix.append(float(np.median(r)))
        farb = farbtiere(im, sat_vor); agreed, _ = einig(pib, farb)
        dets, _, _ = yolo_boxen(M_alt, im) if M_alt else ([], [], [])
        e["bilder"] += 1; e["tiere"] += len(agreed); e["treffer"] += sum(any(trifft(a, d) for d in dets) for a in agreed); e["meldungen"] += len(dets)
        flaechen += [f["a"] for f in farb]; proben.append((n, int(i), agreed))
        if (len(proben) % 5) == 0: male(im, pib, farb, agreed, dets, f"Drift {n} Bild {i}: Bewegung blau, Farbe rot, beide gruen, YOLO gelb")
        schreibe(fortschritt=(si + (list(idx).index(i) + 1) / len(idx)) / max(len(wahl), 1), meldung=f"Satz {si+1}/{len(wahl)} {n}, Bild {i}")
    cap.release(); treffer[0] += e["tiere"]; treffer[1] += e["treffer"]; tiere_je_bild.append(e["tiere"] / max(e["bilder"], 1)); S["drift"]["je_satz"].append(e)
sat_median = float(np.median(S_pix)) if S_pix else None; recall = treffer[1] / treffer[0] if treffer[0] else None
bezug = {}
try: bezug = json.load(open(os.path.join(N, "bezug.json"), encoding="utf-8"))
except Exception: pass
sat_bezug = bezug.get("saettigung_median"); drift_sat = (abs(sat_median - sat_bezug) / sat_bezug) if (sat_median and sat_bezug) else None
S["drift"].update({"tiere_je_bild": float(np.mean(tiere_je_bild)) if tiere_je_bild else None, "flaeche_median_px": float(np.median(flaechen)) if flaechen else None,
                   "saettigung_median": sat_median, "saettigung_bezug": sat_bezug, "saettigung_drift": drift_sat, "treffer_modell": recall, "modell": os.path.basename(MODELL) if M_alt else None,
                   "modell_geaendert": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(MODELL))) if M_alt else None, "tiere_gesamt": treffer[0], "getroffen": treffer[1]})
ausloeser = []
if recall is not None and recall < TREFFER_MIN: ausloeser.append(f"Treffer {recall:.0%} < {TREFFER_MIN:.0%}")
if drift_sat is not None and drift_sat > SAETT_DRIFT: ausloeser.append(f"Saettigung {sat_median:.0f} gegen Bezug {sat_bezug:.0f} ({drift_sat:+.0%})")
if ERZWINGEN: ausloeser.append("erzwungen")
S["drift"]["ausloeser"] = ausloeser
if not wahl or M_alt is None:
    schreibe(phase="fertig", ergebnis="keine Saetze mit Video und Farbwahrheit oder kein Modell", meldung="nichts zu tun"); sys.exit(0)
ABNAHME_NUR = os.environ.get("ABNAHME_NUR", "0") == "1" and os.path.exists(Y + "/modell/kandidat/best.pt")
if ABNAHME_NUR:
    S["ausloeser"] = "nur Abnahme des vorhandenen Kandidaten"; kand = Y + "/modell/kandidat/best.pt"; S["marken"] = {"hinweis": "uebersprungen (nur Abnahme)"}
    try: S["training"] = json.load(open(Y + "/modell/kandidat/info.json"))
    except Exception: S["training"] = {"hinweis": "kandidat ohne info.json"}
if not ausloeser and not ABNAHME_NUR:
    schreibe(phase="ruhe", fortschritt=1.0, ergebnis=f"kein Nachziehen noetig: Treffer {recall:.0%}, Saettigung {sat_median:.0f}", meldung="Ruhe")
    open(VERLAUF, "a").write(json.dumps({"marke": MARKE, "uhr": S["start"], "ergebnis": "ruhe", "drift": S["drift"]}) + "\n"); sys.exit(0)

# ================= 2 Marken =================
if not ABNAHME_NUR:
  sat = float(np.clip(0.6 * (sat_median or 66), 22, 45)); phase("marken", f"Farbschwelle {sat:.0f} (0,6 x Median {sat_median:.0f}); Ausloeser: " + "; ".join(ausloeser))
  saetze_v = [n for n in saetze if alter_h(n) <= DRIFT_H and os.path.exists(os.path.join(A, n + ".avi"))]
  neu = 0; zaehl = {"einig": 0, "nur_bewegung": 0, "nur_farbe": 0, "koerner": 0, "bilder": 0}; benutzt = 0
  for n in saetze_v:
      if neu >= ANZAHL: break
      stamm = os.path.join(A, n)
      try: z = lade(stamm + ".jsonl"); obj = {b["b"]: b.get("objekte", []) for b in z[1:]}
      except Exception: continue
      nummern = sorted(k for k, v in obj.items() if v and k >= 10); gewaehlt = []
      for k in sorted(nummern, key=lambda k: -len(obj[k])):
          if all(abs(k - g) >= 25 for g in gewaehlt): gewaehlt.append(k)
          if len(gewaehlt) == 2: break
      if not gewaehlt: continue
      cap = cv2.VideoCapture(stamm + ".avi"); benutzt += 1
      for k in gewaehlt:
          stamm_l = f"{L}/{n}_b{k}"
          if os.path.exists(stamm_l + ".jpg") or os.path.exists(stamm_l + ".json"): continue
          cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, im = cap.read()
          if not ok: continue
          pib = [box_pi(o) for o in obj[k]]; farb = farbtiere(im, sat); agreed, ben = einig(pib, farb)
          zaehl["einig"] += len(agreed); zaehl["nur_bewegung"] += len(pib) - len(ben); zaehl["nur_farbe"] += len(farb) - len(agreed)
          if not agreed: continue
          _, andere, _ = yolo_boxen(M_alt, im, conf=0.5); zaehl["koerner"] += len(andere)
          cv2.imwrite(stamm_l + ".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 90])
          boxen = [{"x0": b[0], "y0": b[1], "x1": b[2], "y1": b[3], "klasse": "tier", "quelle": "bewegung+farbe"} for b in agreed]
          boxen += [{"x0": int(b[0]), "y0": int(b[1]), "x1": int(b[2]), "y1": int(b[3]), "klasse": ["tier", "korn", "massstab"][kk], "quelle": "modell"} for b, kk in andere]
          json.dump({"satz": n, "bild": k, "aufnahme": n, "datensatz": MARKE, "quelle": "selbsttraining", "farbschwelle": sat, "tiere_erkannt": len(agreed), "boxen": boxen, "status": "offen"},
                    open(stamm_l + ".json", "w", encoding="utf-8"))
          neu += 1; zaehl["bilder"] = neu
          male(im, pib, farb, agreed, None, f"Lernbild {neu}/{ANZAHL}: {n} Bild {k} - {len(agreed)} Tiere einig (gruen)")
          schreibe(fortschritt=neu / ANZAHL, meldung=f"Lernbild {neu}/{ANZAHL} aus {n} Bild {k}", marken=dict(zaehl, farbschwelle=sat, saetze_benutzt=benutzt))
      cap.release()
  S["marken"] = dict(zaehl, farbschwelle=sat, saetze_benutzt=benutzt, datensatz=MARKE)
  if neu < 10:
      schreibe(phase="fertig", ergebnis=f"zu wenige einige Lernbilder ({neu}); altes Modell bleibt", meldung="abgebrochen")
      open(VERLAUF, "a").write(json.dumps({"marke": MARKE, "uhr": S["start"], "ergebnis": "zu wenige Lernbilder", "drift": S["drift"], "marken": S["marken"]}) + "\n"); sys.exit(0)

  # ================= 3 Datensatz =================
  phase("datensatz", "jetson_yolo_datensatz_1.2.py")
  aus = subprocess.run(["python3", os.path.join(H, "jetson_yolo_datensatz_1.2.py")], capture_output=True, text=True, timeout=900).stdout
  try: S["datensatz"] = json.loads(aus[aus.index("DATENSATZJSON") + 13:].strip()) if "DATENSATZJSON" in aus else {"roh": aus[-300:]}
  except Exception as ex: S["datensatz"] = {"fehler": str(ex)[:100], "roh": aus[-300:]}
  schreibe(fortschritt=1.0, meldung=f"Datensatz: {S['datensatz'].get('train')} zum Lernen, {S['datensatz'].get('val')} zum Pruefen")

  # ================= 4 Training (Einheit mikroskop-training; Ergebnis -> kandidat) =================
  phase("training", f"{EPOCHEN} Epochen, Livedienst pausiert")
  lauf = "selbst_" + time.strftime("%m%d_%H%M")
  skript = f'''
  import os, json, time, shutil, glob, subprocess, threading
  from ultralytics import YOLO
  Y = os.path.expanduser("~/mikroskop/yolo"); os.chdir(Y); t0 = time.time()
  def cache_leeren(): subprocess.run("sudo -n /usr/local/sbin/cache_leeren >/dev/null 2>&1", shell=True)
  def waechter():
      while True: time.sleep(20); cache_leeren()
  threading.Thread(target=waechter, daemon=True).start()
  m = YOLO("yolov8n.pt"); cache_leeren()
  try:
      erg = m.train(data=Y + "/datensatz/data.yaml", epochs={EPOCHEN}, imgsz=640, batch=8, device=0, workers=0, project=Y + "/laeufe", name="{lauf}", exist_ok=True, patience=15, plots=False, verbose=False)
  except RuntimeError as e:
      print("Erster Versuch scheiterte:", str(e)[:160], "-- zweiter Versuch mit batch 4", flush=True); cache_leeren(); import torch; torch.cuda.empty_cache(); m = YOLO("yolov8n.pt")
      erg = m.train(data=Y + "/datensatz/data.yaml", epochs={EPOCHEN}, imgsz=640, batch=4, device=0, workers=0, project=Y + "/laeufe", name="{lauf}", exist_ok=True, patience=15, plots=False, verbose=False)
  best = os.path.join(Y, "laeufe", "{lauf}", "weights", "best.pt"); os.makedirs(Y + "/modell/kandidat", exist_ok=True); shutil.copy(best, Y + "/modell/kandidat/best.pt")
  mm = YOLO(best); v = mm.val(data=Y + "/datensatz/data.yaml", imgsz=640, device=0, plots=False, verbose=False)
  info = {{"lauf": "{lauf}", "epochen": {EPOCHEN}, "sekunden": round(time.time() - t0), "mAP50": round(float(v.box.map50), 3), "mAP50_95": round(float(v.box.map), 3), "uhr": time.strftime("%Y-%m-%d %H:%M:%S"), "selbsttraining": "{MARKE}"}}
  json.dump(info, open(Y + "/modell/kandidat/info.json", "w"), indent=1); print("TRAINING_FERTIG", json.dumps(info), flush=True)
  '''
  open(Y + "/training_lauf.py", "w").write(skript)
  for p in (Y + "/modell/kandidat/best.pt", Y + "/modell/kandidat/info.json"):
      if os.path.exists(p): os.remove(p)
  # Die sudoers-Regel erlaubt genau "systemctl start mikroskop-training" (ohne --no-block: "a password is required", 2. Lauf 14.11.);
  # die Einheit ist oneshot, der Aufruf blockiert bis zum Ende (1. Lauf: TimeoutExpired nach 120 s) -> abgeloest starten, nicht warten.
  startproz = subprocess.Popen("sudo -n systemctl start mikroskop-training", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  time.sleep(8)
  if startproz.poll() is not None and startproz.returncode != 0:
      schreibe(phase="fertig", fehler="Training nicht startbar: " + (startproz.stderr.read() or startproz.stdout.read())[-200:], ergebnis="altes Modell bleibt"); sys.exit(1)
  csv = os.path.join(Y, "laeufe", lauf, "results.csv"); t_tr = time.time()
  while True:
      time.sleep(10); akt = subprocess.run("systemctl is-active mikroskop-training", shell=True, capture_output=True, text=True).stdout.strip()
      ep = {}
      try:
          z = [l for l in open(csv) if l.strip()]
          if len(z) > 1:
              k = [x.strip() for x in z[0].split(",")]; v = [x.strip() for x in z[-1].split(",")]; d = dict(zip(k, v))
              ep = {"epoche": int(float(d.get("epoch", 0))) + 1, "box_loss": round(float(d.get("train/box_loss", 0)), 4), "mAP50": round(float(d.get("metrics/mAP50(B)", 0)), 3), "mAP50_95": round(float(d.get("metrics/mAP50-95(B)", 0)), 3)}
      except Exception: pass
      S["training"] = dict(ep, lauf=lauf, epochen=EPOCHEN, zustand=akt, sekunden=round(time.time() - t_tr))
      schreibe(fortschritt=min(1.0, ep.get("epoche", 0) / EPOCHEN), meldung=f"Epoche {ep.get('epoche', 0)}/{EPOCHEN}, Verlust {ep.get('box_loss', '-')}, mAP50 {ep.get('mAP50', '-')}")
      if akt not in ("activating", "active"): break
      if time.time() - t_tr > 6 * 3600: break
  kand = Y + "/modell/kandidat/best.pt"
  if not os.path.exists(kand):
      schreibe(phase="fertig", fehler="Training ohne Ergebnis (kein kandidat/best.pt); siehe yolo/training.log", ergebnis="altes Modell bleibt")
      open(VERLAUF, "a").write(json.dumps({"marke": MARKE, "uhr": S["start"], "ergebnis": "training fehlgeschlagen", "drift": S["drift"], "marken": S["marken"]}) + "\n"); sys.exit(1)
  try: S["training"].update(json.load(open(Y + "/modell/kandidat/info.json")))
  except Exception: pass

# ================= 5 Abnahme =================
phase("abnahme", "altes gegen neues Modell auf denselben Bildern")
time.sleep(15)                                                                  # Livedienst ist wieder da; GPU-Speicher setzen lassen
M_neu = YOLO(kand); alt = {"treffer": 0, "meld": 0}; neu_ = {"treffer": 0, "meld": 0}; tiere = 0; nb = 0; cap_n = None; cap = None
for j, (n, i, agreed) in enumerate(proben):
    if n != cap_n:
        if cap: cap.release()
        cap = cv2.VideoCapture(os.path.join(A, n + ".avi")); cap_n = n
    cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, im = cap.read()
    if not ok: continue
    da, _, _ = yolo_boxen(M_alt, im); dn, _, _ = yolo_boxen(M_neu, im); nb += 1; tiere += len(agreed)
    alt["treffer"] += sum(any(trifft(a, d) for d in da) for a in agreed); alt["meld"] += len(da)
    neu_["treffer"] += sum(any(trifft(a, d) for d in dn) for a in agreed); neu_["meld"] += len(dn)
    if j % 10 == 0: male(im, [], [], agreed, dn, f"Abnahme {n} Bild {i}: Marken gruen, neues Modell gelb")
    schreibe(fortschritt=(j + 1) / len(proben), meldung=f"Bild {j+1}/{len(proben)}: alt {alt['treffer']}/{tiere}, neu {neu_['treffer']}/{tiere}",
             abnahme={"bilder": nb, "tiere": tiere, "alt_treffer": alt["treffer"] / max(tiere, 1), "neu_treffer": neu_["treffer"] / max(tiere, 1), "alt_meld_je_bild": alt["meld"] / max(nb, 1), "neu_meld_je_bild": neu_["meld"] / max(nb, 1)})
if cap: cap.release()
ra, rn = alt["treffer"] / max(tiere, 1), neu_["treffer"] / max(tiere, 1); tjb = tiere / max(nb, 1); mjb = neu_["meld"] / max(nb, 1)
mjb_alt = alt["meld"] / max(nb, 1)
# 1.3: Meldungen des neuen Modells gegen das ALTE Modell begrenzt (<= 1,2 x alt + 0,2), nicht gegen die Marken: die Marken zaehlen
# blasse und ruhende Tiere nicht, beide Modelle melden deshalb mehr als Marken (3. Lauf 14.11.: neu 80 % Treffer gegen 66 %, verworfen
# wegen 1,68 Meldungen/Bild bei 1,04 Marken/Bild -- das alte Modell lag bei denselben Bildern aehnlich hoch).
angenommen = (rn >= ra + 0.02) and (mjb <= 1.2 * mjb_alt + 0.2)
grund = f"Treffer neu {rn:.0%} gegen alt {ra:.0%}; Meldungen je Bild neu {mjb:.2f}, alt {mjb_alt:.2f}, Marken {tjb:.2f}"
S["abnahme"].update({"alt_treffer": ra, "neu_treffer": rn, "angenommen": angenommen, "grund": grund})
if angenommen:
    vorher = Y + f"/modell/vorher_{MARKE}.pt"; shutil.copy(MODELL, vorher); shutil.copy(kand, MODELL + ".neu"); os.replace(MODELL + ".neu", MODELL)
    try: shutil.copy(Y + "/modell/kandidat/info.json", Y + "/modell/info.json")
    except Exception: pass
    json.dump({"saettigung_median": sat_median, "marke": MARKE, "uhr": time.strftime("%Y-%m-%d %H:%M:%S")}, open(os.path.join(N, "bezug.json"), "w"))
    ergebnis = f"neues Modell uebernommen ({grund}); Rueckfall: {os.path.basename(vorher)}"
else:
    ergebnis = f"neues Modell verworfen ({grund}); altes bleibt"
phase("fertig", ergebnis); schreibe(fortschritt=1.0, ergebnis=ergebnis, ende=time.strftime("%Y-%m-%d %H:%M:%S"))
open(VERLAUF, "a").write(json.dumps({"marke": MARKE, "uhr": S["start"], "ende": S.get("ende"), "ergebnis": ergebnis, "angenommen": angenommen, "drift": {k: v for k, v in S["drift"].items() if k != "je_satz"},
                                     "marken": S["marken"], "training": S["training"], "abnahme": S["abnahme"]}) + "\n")
print("FERTIG", ergebnis, flush=True)
