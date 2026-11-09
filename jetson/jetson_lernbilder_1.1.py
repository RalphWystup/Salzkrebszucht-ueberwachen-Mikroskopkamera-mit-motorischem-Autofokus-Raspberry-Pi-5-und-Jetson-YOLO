#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_lernbilder_1.1.py -- laeuft auf dem Jetson: NACHZIEHEN von Lernbildern aus aktuellem Bildmaterial (09.11.2026).

Sein Wort: "die einzulernenden bilder fuer yolo veralten da die tiere wachsen. Also muss es einen button geben wo neue Bilder
ca. 100 Stueck aus aktuellem Bildmaterial, natuerlich nur wenn tiere detektiert wurden, erzeugt werden koennen ... Dann existieren
mehrere Datensaetze zu unterschiedlichen Wachstumszeiten, das muss aber yolo automatisch verarbeiten, auch mithilfe eines Zeitstempels."

  python3 jetson_lernbilder_1.1.py [anzahl=100] [stunden=6]

Quelle: Aufnahmesaetze mit Video (Videos liegen ~3 h, Lernarchiv laenger), neueste zuerst, bevorzugt juenger als <stunden> h; reicht das
nicht, werden aeltere Saetze mit Video genommen. Nur Bilder, auf denen Tiere ERKANNT wurden (Farbwahrheit _farbe.jsonl, wenn vorhanden,
vereinigt mit den Objekten der Auswertung .jsonl); die tierreichsten Bilder zuerst, mindestens 25 Bilder auseinander, hoechstens 2 je Satz,
erst ein Bild je Satz ueber alle Saetze (zeitliche Streuung), dann das zweite. Vorschlagsrahmen wie 1.0 (Rand 6 px, Dubletten > 0,5 vereinigt).

Jedes Bild bekommt die Marke  "datensatz": "<JJJJ-MM-TT_HHMM>"  (Zeitpunkt des Nachziehens = Wachstumsstand) sowie "aufnahme" (Satzname =
Aufnahmezeit) und "quelle": "nachziehen". Der Datensatzbau (jetson_yolo_datensatz_1.2) nimmt ALLE geprueften/offenen Bilder aller Marken
zusammen -- YOLO lernt damit alle Wachstumsstaende in einem Modell; die Zusammensetzung je Marke steht im Verlauf.
Bestehende Bilder (.jpg/.json) werden nie ueberschrieben. Ausgabe: eine Zeile LERNBILDER {json}."""
import os, glob, json, sys, time, cv2

A = os.path.expanduser("~/mikroskop/aufnahmen"); Z = os.path.expanduser("~/mikroskop/lernen/bilder"); os.makedirs(Z, exist_ok=True)
ANZAHL = int(sys.argv[1]) if len(sys.argv) > 1 else 100
STUNDEN = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
RAND, ABSTAND, JE_SATZ, AB_BILD = 6, 25, 2, 10
MARKE = time.strftime("%Y-%m-%d_%H%M"); JETZT = time.time()


def lade(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def box(t, rand=RAND): return [max(0, t["rx"] - rand), max(0, t["ry"] - rand), min(640, t["rx"] + t["rb"] + rand), min(480, t["ry"] + t["rh"] + rand)]
def ueberdeckung(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / max(1e-9, (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i)
def alter_h(stamm):
    try: return (JETZT - time.mktime(time.strptime(os.path.basename(stamm)[:15], "%Y%m%d_%H%M%S"))) / 3600
    except ValueError: return 1e9


def kandidaten(stamm):
    """Bilder eines Satzes mit Tieren: [(zahl, bildnr, boxen)] -- tierreichste zuerst, mindestens ABSTAND auseinander."""
    try:
        obj = {b["b"]: b.get("objekte", []) for b in lade(stamm + ".jsonl")[1:]}
        wahr = {w["b"]: w.get("tiere", []) for w in lade(stamm + "_farbe.jsonl")[1:]} if os.path.exists(stamm + "_farbe.jsonl") else {}
    except Exception: return []
    nummern = sorted(n for n in set(obj) | set(wahr) if n >= AB_BILD and (obj.get(n) or wahr.get(n)))
    bewertet = sorted(((len(wahr.get(n, [])) + len(obj.get(n, [])), n) for n in nummern), reverse=True)
    aus = []
    for z, n in bewertet:
        if all(abs(n - m) >= ABSTAND for _, m, _ in aus):
            boxen = [{"box": box(t), "quelle": "farbe"} for t in wahr.get(n, [])]
            for o in obj.get(n, []):
                b = box(o)
                if not any(ueberdeckung(b, x["box"]) > 0.5 for x in boxen): boxen.append({"box": b, "quelle": "auswertung"})
            aus.append((z, n, boxen))
        if len(aus) == JE_SATZ: break
    return aus


saetze = sorted((p[:-6] for p in glob.glob(A + "/*.jsonl") if not p.endswith("_farbe.jsonl") and os.path.exists(p[:-6] + ".avi")), key=alter_h)
junge = [s for s in saetze if alter_h(s) <= STUNDEN]; aeltere = [s for s in saetze if alter_h(s) > STUNDEN]
plan = {}                                                  # stamm -> Kandidatenliste
for s in junge + aeltere:
    k = kandidaten(s)
    if k: plan[s] = k
    if sum(min(len(v), 1) for v in plan.values()) >= ANZAHL and s in junge: break   # genug junge Saetze fuer je ein Bild
reihenfolge = []                                           # erst je Satz ein Bild (neueste zuerst), dann das zweite
for runde in range(JE_SATZ):
    for s in junge + aeltere:
        if s in plan and len(plan[s]) > runde: reihenfolge.append((s,) + plan[s][runde])
neu, uebersprungen, benutzt, aelt = 0, 0, set(), 0.0
for s, zahl, n, boxen in reihenfolge:
    if neu >= ANZAHL: break
    name = os.path.basename(s); stamm = f"{Z}/{name}_b{n}"
    if os.path.exists(stamm + ".jpg") or os.path.exists(stamm + ".json"): uebersprungen += 1; continue
    cap = cv2.VideoCapture(s + ".avi"); cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, im = cap.read(); cap.release()
    if not ok or im is None: continue
    cv2.imwrite(stamm + ".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    json.dump({"satz": name, "bild": n, "aufnahme": name, "datensatz": MARKE, "quelle": "nachziehen", "tiere_erkannt": zahl,
               "boxen": [{"x0": b["box"][0], "y0": b["box"][1], "x1": b["box"][2], "y1": b["box"][3], "quelle": b["quelle"]} for b in boxen],
               "status": "offen"}, open(stamm + ".json", "w", encoding="utf-8"))
    neu += 1; benutzt.add(s); aelt = max(aelt, alter_h(s))
alle = glob.glob(Z + "/*.json"); status, marken = {}, {}
for p in alle:
    try: d = json.load(open(p, encoding="utf-8")); st = d.get("status", "offen"); mk = d.get("datensatz", "alt")
    except Exception: st, mk = "kaputt", "?"
    status[st] = status.get(st, 0) + 1; marken[mk] = marken.get(mk, 0) + 1
print("LERNBILDER", json.dumps({"neu": neu, "datensatz": MARKE, "gewuenscht": ANZAHL, "saetze_benutzt": len(benutzt), "saetze_mit_video": len(saetze),
                                "saetze_juenger_h": len(junge), "aeltestes_benutzt_h": round(aelt, 1), "schon_vorhanden": uebersprungen,
                                "gesamt": len(alle), "status": status, "marken": marken}))
