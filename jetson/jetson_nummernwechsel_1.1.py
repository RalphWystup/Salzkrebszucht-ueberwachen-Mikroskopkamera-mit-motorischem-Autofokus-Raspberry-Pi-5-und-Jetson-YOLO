#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_nummernwechsel_1.1.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Problem 7 des Plans: "Zwei Tiere naeher als 50 px verschmelzen, Nummern koennen tauschen -- nicht gemessen."

1.0 hat die eine Haelfte gemessen (Ergebnis: zwei GETRENNT VERFOLGTE Tiere kommen einander fast nie nahe --
12 von 190 067 Bildern unter 50 px, 7 Begegnungen, alle zu kurz zum Entscheiden). Damit ist aber nur die Frage
beantwortet, ob zwei Nummern tauschen. Die eigentliche Sorge ist die andere Haelfte, und die kann der
Verfolger selbst nicht beantworten: wenn zwei Tiere zu EINEM Rahmen verschmelzen, sieht er nur EIN Objekt,
und ein Abstand zwischen zwei Nummern entsteht gar nicht erst.

1.1 misst darum beides, die zweite Haelfte mit dem unabhaengigen Weg (Farbwahrheit <satz>_farbe.jsonl, die
Tiere an der Farbe findet und Teile naeher als 15 px zusammenlegt):
  A  Abstaende zwischen getrennt verfolgten Tieren (wie 1.0)
  B  VERSCHMELZUNG: Rahmen des Beobachters, in denen ZWEI ODER MEHR Farbgebiete liegen. Ihr Abstand wird
     mitgeschrieben -- unter etwa 20 px koennen es Rumpf und Kopf eines Tieres sein, darueber sind es zwei
     Tiere unter einer Nummer. Gegenprobe: wie oft liegt umgekehrt kein einziges Farbgebiet im Rahmen.

Nur lesen. Schreibt befund_problem7_<datum>.json.

  python3 jetson_nummernwechsel_1.1.py [--jeder 6] [--grenze_s 900]
"""
import os, sys, json, time, glob, statistics as st

SCHWELLEN = (30.0, 50.0, 80.0)
NAH = 50.0; LUECKE = 3; RAND = 30; MIN_PUNKTE = 5; MIN_VERGLEICH = 5; UNTERSCHIED_FAKTOR = 2.0


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1] if n in sys.argv else v)
def laenge(o): return float(o["mL"]) if "mL" in o else float(o.get("L", 0.0))
def mad(w):
    if len(w) < 2: return 0.0
    m = st.median(w); return sum(abs(x - m) for x in w) / len(w)


def satz_auswerten(pfad):
    z = [json.loads(l) for l in open(pfad, encoding="utf-8") if l.strip()]
    kopf, bilder = z[0], z[1:]
    bahnen = {}
    for b in bilder:
        for o in b.get("objekte", []):
            if o.get("ruht"): continue
            bahnen.setdefault(o["nr"], []).append((b["b"], o))
    tiere = {nr for nr, p in bahnen.items() if len(p) >= MIN_PUNKTE}
    bilder_nah = {s: 0 for s in SCHWELLEN}; paar_bilder = {}
    for b in bilder:
        oo = [o for o in b.get("objekte", []) if o["nr"] in tiere and not o.get("ruht")]
        nah = {s: False for s in SCHWELLEN}
        for i in range(len(oo)):
            for j in range(i + 1, len(oo)):
                d = ((oo[i]["x"] - oo[j]["x"]) ** 2 + (oo[i]["y"] - oo[j]["y"]) ** 2) ** 0.5
                for s in SCHWELLEN:
                    if d < s: nah[s] = True
                if d < NAH: paar_bilder.setdefault(tuple(sorted((oo[i]["nr"], oo[j]["nr"]))), []).append(b["b"])
        for s in SCHWELLEN:
            if nah[s]: bilder_nah[s] += 1
    ereignisse = []
    for paar, bb in paar_bilder.items():
        bb = sorted(set(bb)); block = [bb[0]]
        for x in bb[1:]:
            if x - block[-1] <= LUECKE: block.append(x)
            else: ereignisse.append((paar, block[0], block[-1])); block = [x]
        ereignisse.append((paar, block[0], block[-1]))
    aus = []
    for (na, nb), f0, f1 in ereignisse:
        pa, pb = bahnen[na], bahnen[nb]
        verlust = (pa[-1][0] <= f1 + 3) or (pb[-1][0] <= f1 + 3)
        va = [laenge(o) for n, o in pa if f0 - RAND <= n < f0]; vb = [laenge(o) for n, o in pb if f0 - RAND <= n < f0]
        qa = [laenge(o) for n, o in pa if f1 < n <= f1 + RAND]; qb = [laenge(o) for n, o in pb if f1 < n <= f1 + RAND]
        urteil = "nicht entscheidbar"
        if verlust: urteil = "Verlust"
        elif min(len(va), len(vb), len(qa), len(qb)) >= MIN_VERGLEICH:
            ma, mb_, ka, kb = st.median(va), st.median(vb), st.median(qa), st.median(qb)
            streu = max(mad(va), mad(vb), mad(qa), mad(qb))
            if abs(ma - mb_) > UNTERSCHIED_FAKTOR * max(streu, 0.5):
                urteil = "Groessentausch" if abs(ka - mb_) + abs(kb - ma) < abs(ka - ma) + abs(kb - mb_) else "Nummern halten"
        aus.append({"von": f0, "bis": f1, "dauer_bilder": f1 - f0 + 1, "urteil": urteil})
    # --- B: Verschmelzung ueber die Farbwahrheit
    ver = {"rahmen": 0, "mit_0": 0, "mit_1": 0, "mit_2plus": 0, "abstaende": []}
    fp = pfad[:-6] + "_farbe.jsonl"
    if os.path.exists(fp):
        fz = [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
        farbe = {w["b"]: w.get("tiere", []) for w in fz[1:]}
        for b in bilder:
            tt = farbe.get(b["b"])
            if tt is None: continue
            for o in b.get("objekte", []):
                if o.get("ruht") or o["nr"] not in tiere: continue
                drin = [t for t in tt if o["rx"] <= t["x"] < o["rx"] + o["rb"] and o["ry"] <= t["y"] < o["ry"] + o["rh"]]
                ver["rahmen"] += 1
                if len(drin) == 0: ver["mit_0"] += 1
                elif len(drin) == 1: ver["mit_1"] += 1
                else:
                    ver["mit_2plus"] += 1
                    d = min(((drin[i]["x"] - drin[j]["x"]) ** 2 + (drin[i]["y"] - drin[j]["y"]) ** 2) ** 0.5
                            for i in range(len(drin)) for j in range(i + 1, len(drin)))
                    ver["abstaende"].append(round(d, 1))
    return {"name": kopf.get("name"), "bilder": len(bilder), "bilder_nah": bilder_nah,
            "begegnungen": aus, "tiere": len(tiere), "verschmelzung": ver, "farbe_da": os.path.exists(fp)}


def main():
    ordner = os.path.join(os.path.expanduser("~/mikroskop"), "aufnahmen")
    jeder = arg("--jeder", 6); grenze = arg("--grenze_s", 900.0)
    alle = sorted(p for p in glob.glob(os.path.join(ordner, "*.jsonl")) if not p.endswith("_farbe.jsonl"))
    pfade = alle[::jeder]
    print(f"Problem 7 (1.1) -- dichte Tiere: Nummerntausch UND Verschmelzung. {len(pfade)} Saetze (jeder {jeder}. von {len(alle)})")
    t0 = time.time(); S = []; fehler = 0
    for i, p in enumerate(pfade):
        if time.time() - t0 > grenze: print(f"Zeitgrenze nach {i} Saetzen"); break
        try: S.append(satz_auswerten(p))
        except Exception as e:
            fehler += 1
            if fehler <= 3: print(f"  {os.path.basename(p)}: {e}")
    nb = sum(s["bilder"] for s in S)
    if not nb: print("keine Bilder"); return 1
    print(f"Gelesen: {len(S)} Saetze, {nb} Bilder, {sum(1 for s in S if s['farbe_da'])} davon mit Farbwahrheit, "
          f"{fehler} nicht lesbar, {time.time()-t0:.0f} s\n")
    print("== A. Zwei GETRENNT VERFOLGTE Tiere dicht beieinander")
    for s in SCHWELLEN:
        n = sum(x["bilder_nah"][s] for x in S)
        print(f"   naeher als {s:.0f} px: {n} von {nb} Bildern = {100.0*n/nb:.3f} %")
    alleb = [b for s in S for b in s["begegnungen"]]
    z = {}
    for b in alleb: z[b["urteil"]] = z.get(b["urteil"], 0) + 1
    print(f"   Begegnungen unter {NAH:.0f} px: {len(alleb)}; Urteile: {z}")
    V = {"rahmen": 0, "mit_0": 0, "mit_1": 0, "mit_2plus": 0}; abst = []
    for s in S:
        for k in V: V[k] += s["verschmelzung"][k]
        abst += s["verschmelzung"]["abstaende"]
    print(f"\n== B. VERSCHMELZUNG -- wie oft steckt mehr als ein Farbgebiet in EINEM Rahmen")
    if not V["rahmen"]:
        print("   keine Farbwahrheit zu diesen Saetzen vorhanden")
    else:
        print(f"   gepruefte Rahmen (bewegte Tiere): {V['rahmen']}")
        print(f"   mit genau einem Farbgebiet: {V['mit_1']} = {100.0*V['mit_1']/V['rahmen']:.2f} %")
        print(f"   mit ZWEI oder mehr:         {V['mit_2plus']} = {100.0*V['mit_2plus']/V['rahmen']:.2f} %   <-- Verschmelzungsverdacht")
        print(f"   mit keinem (Rahmen ohne Farbe): {V['mit_0']} = {100.0*V['mit_0']/V['rahmen']:.2f} %")
        if abst:
            abst.sort(); n = len(abst)
            print(f"   Abstand der beiden Gebiete: Median {abst[n//2]:.0f} px, Viertel {abst[n//4]:.0f} .. {abst[3*n//4]:.0f}, "
                  f"Spanne {abst[0]:.0f} .. {abst[-1]:.0f}")
            ueber20 = sum(1 for a in abst if a > 20); ueber30 = sum(1 for a in abst if a > 30)
            print(f"   davon weiter als 20 px auseinander: {ueber20} ({100.0*ueber20/n:.0f} %) -- kaum noch Rumpf und Kopf eines Tieres")
            print(f"   davon weiter als 30 px auseinander: {ueber30} ({100.0*ueber30/n:.0f} %)")
            print(f"   => echte Verschmelzung zweier Tiere, streng gerechnet (> 30 px): "
                  f"{100.0*ueber30/max(V['rahmen'],1):.3f} % aller Rahmen")
    heute = time.strftime("%Y-%m-%d")
    json.dump({"saetze": len(S), "bilder": nb, "schwellen": {str(s): sum(x["bilder_nah"][s] for x in S) for s in SCHWELLEN},
               "urteile": z, "verschmelzung": V, "abstaende": abst},
              open(f"befund_problem7_{heute}.json", "w", encoding="utf-8"))
    print(f"\ngeschrieben: befund_problem7_{heute}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
