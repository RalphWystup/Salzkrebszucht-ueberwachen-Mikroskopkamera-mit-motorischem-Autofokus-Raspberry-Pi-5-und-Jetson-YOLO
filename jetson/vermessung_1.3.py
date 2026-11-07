#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vermessung_1.3.py -- statistische Auswertung der Vermessungsdaten des Beobachters.

Sein Wort, 05.11.2026: "ich will die tiere richtig getrackt wissen und die vermessungsdaten (groesse,
geschwindigkeit, anzahl tiere im bild) sollen statistisch ausgewertet werden".

Liest alle geholten Saetze aufnahmen/<name>/<name>.jsonl (Beobachter 2.x) und rechnet je Satz und gesamt:
  Tiere je Bild      Verteilung 0,1,2,... ueber alle Bilder. Ein Tier ist ein Objekt, das sich in dieser Aufnahme
                     bewegt hat (Nummer mit >= MIN_PUNKTE bewegten Rahmen); seine ruhenden Bilder zaehlen mit. Objekte,
                     die sich nie bewegen (Kruemel, Blasen), zaehlen nicht -- sein Wort: "es werden auch unbewegliche
                     objekte getrackt" (1.1)
  Groesse            je Bahn der MEDIAN der Koerperlaenge mL (Beobachter 2.7+: am Rohbild gemessen, Punkte dunkler als der
                     Hintergrund; bei aelteren Saetzen ersatzweise L der Bewegungsmaske, die den Lichthof enthaelt und
                     gemessen 690..1040 um statt 514 um ergab -- im Bericht gekennzeichnet). px -> um ueber den Massstab.
                     Median statt 90. Hundertstel, weil Bewegungsunschaerfe und Teilansichten nach oben UND unten streuen (1.2)
  Geschwindigkeit    je Bahn der Median von |Weg|/Zeit zwischen Folgebildern (px/s -> mm/s); Verteilung ueber Bahnen
  Bahnen             Anzahl, Dauer, Abdeckung (Anteil der Bilder einer Bahn mit Rahmen)
Eine Bahn ist eine Nummer des Verfolgers mit mindestens MIN_PUNKTE Rahmen. Bahnen sind NICHT Tiere: dasselbe
Tier kann unter mehreren Nummern laufen (Nummernwechsel), ein Tier das das Bild verlaesst und wiederkommt ist
zwei Bahnen. Die Zahl verschiedener Tiere ist aus diesen Daten nicht bestimmbar.
Massstab: aus dem Kopf des Satzes (massstab_um_px, von der Wache aus der Folie); fehlt er, 10,625 um/px
(Folie, 02.11.2026, Fokus 154,6 Grad) -- mit Vermerk.
Schreibt VERMESSUNG_<datum>.md (Tabellen) und vermessung_<datum>.json (Zahlen).

  python3 vermessung_1.3.py [aufnahmen-ordner] [--ab 20261105_0030]   nur Saetze ab diesem Namen
"""
import sys, json, pathlib, collections, datetime
import numpy as np

MIN_PUNKTE = 5
MASSSTAB_FOLIE = 10.625     # um/px, Folie 02.11.2026, Fokus 154,6 Grad


def quant(v, q): return float(np.percentile(v, q)) if len(v) else float("nan")


def dz(x, nk=0):
    """Zahl mit Dezimalkomma; nan -> '-'."""
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)): return "-"
        return f"{x:.{nk}f}".replace(".", ",")
    except Exception:
        return str(x)


def satz_auswerten(pfad):
    z = [json.loads(l) for l in open(pfad, encoding="utf-8") if l.strip()]
    kopf, bilder = z[0], z[1:]
    fps = kopf.get("fps") or 28.8
    mst = kopf.get("massstab_um_px"); mst_quelle = "Satzkopf (Wache)" if mst else "Folie 02.11.2026 (Vorgabe)"
    mst = mst or MASSSTAB_FOLIE
    bahnen = collections.defaultdict(list)
    for b in bilder:
        for o in b["objekte"]:
            if not o.get("ruht"): bahnen[o["nr"]].append((b["b"], b["t"], o))
    tiere = {nr for nr, pts in bahnen.items() if len(pts) >= MIN_PUNKTE}      # 1.1: Nummern, die sich bewegt haben
    je_bild = [sum(1 for o in b["objekte"] if o["nr"] in tiere) for b in bilder]
    aus_bahnen = []
    for nr, pts in bahnen.items():
        if len(pts) < MIN_PUNKTE: continue
        am_koerper = all("mL" in o for _, _, o in pts)
        L = np.array([o["mL"] if "mL" in o else o["L"] for _, _, o in pts]); laenge_px = quant(L, 50)
        v = []
        for (b0, t0, o0), (b1, t1, o1) in zip(pts, pts[1:]):
            if 1 <= b1 - b0 <= 3 and t1 > t0:
                v.append(float(np.hypot(o1["x"] - o0["x"], o1["y"] - o0["y"])) / (t1 - t0))
        dauer = pts[-1][1] - pts[0][1]; spanne = pts[-1][0] - pts[0][0] + 1
        aus_bahnen.append({"nr": nr, "punkte": len(pts), "abdeckung": len(pts) / spanne, "dauer_s": round(dauer, 2),
                           "laenge_px": round(laenge_px, 1), "laenge_um": round(laenge_px * mst, 0),
                           "tempo_px_s": (round(float(np.median(v)), 1) if v else None),
                           "tempo_mm_s": (round(float(np.median(v)) * mst / 1000, 2) if v else None),
                           "breite_um": round(quant(np.array([o["mB"] if "mB" in o else o["B"] for _, _, o in pts]), 50) * mst, 0),
                           "am_koerper": am_koerper})
    hell = [b.get("hell") for b in bilder if b.get("hell") is not None]
    return {"name": kopf["name"], "fassung": kopf.get("fassung"), "uhr": kopf.get("uhr"), "bilder": len(bilder), "fps": fps,
            "sekunden": kopf.get("sekunden"), "massstab_um_px": mst, "massstab_quelle": mst_quelle,
            "bilder_mit_tier": sum(1 for n in je_bild if n), "je_bild": je_bild, "bahnen": aus_bahnen,
            "helligkeit": (round(float(np.mean(hell)), 1) if hell else None),
            "hell_spanne": (round(float(np.max(hell) - np.min(hell)), 1) if hell else None)}


def verteilung(werte, einheit, nk=0):
    w = np.array([x for x in werte if x is not None], float)
    if not len(w): return f"keine Werte"
    return f"n = {len(w)}, Median {dz(np.median(w), nk)} {einheit}, Viertel {dz(quant(w,25), nk)} .. {dz(quant(w,75), nk)}, Spanne {dz(w.min(), nk)} .. {dz(w.max(), nk)}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ordner = pathlib.Path(args[0]) if args else pathlib.Path(__file__).resolve().parent / "aufnahmen"
    ab = sys.argv[sys.argv.index("--ab") + 1] if "--ab" in sys.argv else ""
    saetze = []
    kandidaten = sorted(ordner.glob("*/*.jsonl")) + sorted(ordner.glob("*.jsonl"))      # 1.3: Unterordner je Satz ODER flach (Jetson, rsync)
    for p in kandidaten:
        if p.name.endswith("_farbe.jsonl") or p.stem < ab: continue
        if p.parent != ordner and p.stem != p.parent.name: continue
        try: saetze.append(satz_auswerten(p))
        except Exception as e: print(f"{p}: nicht lesbar ({e})")
    if not saetze: print("keine Saetze"); return 1
    heute = datetime.date.today().strftime("%Y-%m-%d"); jetzt = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    alle_bild = [n for s in saetze for n in s["je_bild"]]; alle_bahn = [b for s in saetze for b in s["bahnen"]]
    hist = collections.Counter(alle_bild); hoechst = max(hist) if hist else 0
    sek = sum(s["sekunden"] or 0 for s in saetze)
    quellen = sorted({s["massstab_quelle"] for s in saetze}); mst = sorted({s["massstab_um_px"] for s in saetze})
    L = [b["laenge_um"] for b in alle_bahn]; V = [b["tempo_mm_s"] for b in alle_bahn if b["tempo_mm_s"] is not None]
    md = [f"# Vermessung Salzkrebse -- Beobachter, Stand {jetzt}", "",
          f"Grundlage: {len(saetze)} Aufnahmesaetze, {len(alle_bild)} Bilder, {sek:.0f} s Aufnahmezeit, "
          f"Fassungen {sorted({s['fassung'] for s in saetze})}. Massstab {', '.join(dz(m, 3) for m in mst)} um/px ({'; '.join(quellen)}).", "",
          "Eine *Bahn* ist eine Nummer des Verfolgers mit mindestens 5 Rahmen. Bahnen sind nicht Tiere: dasselbe Tier",
          "kann unter mehreren Nummern laufen, und ein Tier, das das Bild verlaesst und wiederkommt, ist zwei Bahnen.", "",
          "## Tiere je Bild (Objekte, die sich in der Aufnahme bewegt haben; ruhende Bilder zaehlen mit)", "", "| Tiere im Bild | Bilder | Anteil |", "|---|---|---|"]
    for k in range(hoechst + 1): md.append(f"| {k} | {hist.get(k,0)} | {dz(100*hist.get(k,0)/len(alle_bild), 1)} % |")
    md += ["", f"Mittel {dz(np.mean(alle_bild), 2)} Tiere je Bild, hoechstens {hoechst}; Bilder mit mindestens einem Tier: "
           f"{sum(1 for n in alle_bild if n)} von {len(alle_bild)} ({dz(100*sum(1 for n in alle_bild if n)/len(alle_bild))} %).", "",
           "## Groesse (Koerperlaenge je Bahn, Median)", "",
           (f"Am Rohbild gemessen (mL) bei {sum(1 for b in alle_bahn if b['am_koerper'])} von {len(alle_bahn)} Bahnen; die uebrigen aus der Bewegungsmaske (zu gross, enthaelt den Lichthof)." if alle_bahn else ""), "",
           "Nur am Koerper gemessene Bahnen: " + verteilung([b["laenge_um"] for b in alle_bahn if b["am_koerper"]], "um"), "",
           "Alle Bahnen: " + verteilung(L, "um"), "",
           "## Geschwindigkeit (Median je Bahn)", "", verteilung(V, "mm/s", 2), "",
           "## Bahnen", "", f"{len(alle_bahn)} Bahnen; Dauer {verteilung([b['dauer_s'] for b in alle_bahn], 's', 2)}; "
           f"Abdeckung {verteilung([100*b['abdeckung'] for b in alle_bahn], '%')}; Rahmen je Bahn {verteilung([b['punkte'] for b in alle_bahn], '')}.", "",
           "## Je Aufnahmesatz", "", "| Satz | Fassung | Bilder | s | Bilder mit Tier | Bahnen | Laenge um (Median) | Tempo mm/s (Median) | Helligkeit |", "|---|---|---|---|---|---|---|---|---|"]
    for s in saetze:
        Ls = [b["laenge_um"] for b in s["bahnen"]]; Vs = [b["tempo_mm_s"] for b in s["bahnen"] if b["tempo_mm_s"] is not None]
        md.append(f"| {s['name']} | {s['fassung']} | {s['bilder']} | {dz(s['sekunden'], 2)} | {s['bilder_mit_tier']} | {len(s['bahnen'])} | "
                  f"{dz(np.median(Ls) if Ls else None)} | {dz(np.median(Vs) if Vs else None, 2)} | {dz(s['helligkeit'], 1)} |")
    md += ["", "## Alle Bahnen", "", "| Satz | Nr | Rahmen | Abdeckung | Dauer s | Laenge um | Breite um | Tempo mm/s | Mass |", "|---|---|---|---|---|---|---|---|---|"]
    for s in saetze:
        for b in s["bahnen"]:
            md.append(f"| {s['name']} | {b['nr']} | {b['punkte']} | {dz(100*b['abdeckung'])} % | {dz(b['dauer_s'], 2)} | {dz(b['laenge_um'])} | {dz(b['breite_um'])} | {dz(b['tempo_mm_s'], 2)} | {'Koerper' if b['am_koerper'] else 'Bewegungsmaske'} |")
    ziel = ordner.parent / f"VERMESSUNG_{heute}.md"; ziel.write_text("\n".join(md) + "\n", encoding="utf-8")
    json.dump({"stand": jetzt, "saetze": [{k: v for k, v in s.items() if k != "je_bild"} for s in saetze], "tiere_je_bild": dict(hist)},
              open(ordner.parent / f"vermessung_{heute}.json", "w"), indent=1)
    print("\n".join(md[:40])); print(f"\n-> {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
