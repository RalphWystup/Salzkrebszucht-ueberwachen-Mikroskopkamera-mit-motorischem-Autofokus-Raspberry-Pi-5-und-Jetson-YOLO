#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_lichtfarbe_1.1.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Problem 6 des Plans: "Lichtfarbe: Aussehenspruefung (S > 40) auf heutiges Licht geeicht; nur Helligkeits-
spruenge werden erkannt; Kontrolle ueber die Zeit fehlt."

1.1 berichtigt zwei Fehler von 1.0, beide am gemessenen Ergebnis erkannt:
  - 1.0 nahm auch die Dateien <satz>_rahmen.avi fuer Saetze (sie haben keine .jsonl) -- von 140 gewaehlten
    Saetzen blieben nur 67 uebrig.
  - 1.0 mass die Saettigung ALLER Bildpunkte. Die Farbregel sieht aber nur Punkte mit 40 < V < 235 an
    (dunkler Aufdruck und ausgebrannte Stellen sind fuer sie gar nicht da). Darum stand der Hintergrund im
    99. Hundertstel bei S = 255 und der "Abstand" war in jedem Satz negativ -- gemessen wurde etwas, worueber
    die Regel nie entscheidet. 1.1 legt dasselbe Helligkeitsfenster an wie die Regel.

Gemessen wird jetzt genau das, was die Regel tut, ueber die Zeit:
  Fehlflaeche   Anteil der HINTERGRUND-Punkte (ausserhalb seiner um 20 px verbreiterten Rahmen), die
                S > 40 erfuellen und damit faelschlich als Tier durchgehen koennten.
  Trefferflaeche Anteil der TIER-Punkte (mittleres Drittel seiner bewegten Rahmen), die S > 40 erfuellen.
  Beste Schwelle Der Wert, der beide am weitesten auseinanderhaelt (Trefferflaeche minus Fehlflaeche,
                S von 20 bis 100). Wandert er ueber die Tage von 40 weg, ist die Eichung verbraucht.
  Blau/Rot      Farbtemperatur des Hintergrunds -- ein Lampenwechsel zeigt sich hier, nicht in der Helligkeit.

Wo ein Tier ist, sagt nicht die Farbregel, sondern der Beobachter mit seinen Rahmen (kein Zirkelschluss).

Nur lesen. Schreibt befund_problem6_<datum>.json.

  python3 jetson_lichtfarbe_1.1.py [--saetze 160] [--bilder 4] [--grenze_s 900]
"""
import os, sys, json, time, glob
import numpy as np, cv2

AUS = (slice(40, 440), slice(60, 580))
SAT_SCHWELLE = 40
V_MIN, V_MAX = 40, 235          # Helligkeitsfenster der Farbregel (tiere_nach_farbe_1.6)
RAND_WEG = 0.33
BREITER = 20
SCHWELLEN = list(range(20, 101, 5))


def arg(n, v): return type(v)(sys.argv[sys.argv.index(n) + 1] if n in sys.argv else v)


def satz_messen(stamm, n_bilder):
    z = [json.loads(l) for l in open(stamm + ".jsonl", encoding="utf-8") if l.strip()]
    kopf = z[0]; rahmen = {b["b"]: [o for o in b.get("objekte", []) if not o.get("ruht")] for b in z[1:]}
    mit = [b for b, rr in rahmen.items() if rr]
    if not mit: return None
    cap = cv2.VideoCapture(stamm + ".avi")
    if not cap.isOpened(): return None
    wahl = [mit[i] for i in np.linspace(0, len(mit) - 1, min(n_bilder, len(mit))).astype(int)]
    s_t, s_h, v_h, br = [], [], [], []
    for b in wahl:
        cap.set(cv2.CAP_PROP_POS_FRAMES, b)
        ok, im = cap.read()
        if not ok: continue
        aus = im[AUS]; hsv = cv2.cvtColor(aus, cv2.COLOR_BGR2HSV)
        S, V = hsv[:, :, 1], hsv[:, :, 2]
        im_fenster = (V > V_MIN) & (V < V_MAX)                 # nur was die Regel ueberhaupt ansieht
        m_tier = np.zeros(S.shape, np.uint8); m_nah = np.zeros(S.shape, np.uint8)
        for o in rahmen[b]:
            x0 = o["rx"] - AUS[1].start; y0 = o["ry"] - AUS[0].start; w, h = o["rb"], o["rh"]
            dx, dy = int(w * RAND_WEG), int(h * RAND_WEG)
            cv2.rectangle(m_tier, (x0 + dx, y0 + dy), (x0 + w - dx, y0 + h - dy), 1, -1)
            cv2.rectangle(m_nah, (x0 - BREITER, y0 - BREITER), (x0 + w + BREITER, y0 + h + BREITER), 1, -1)
        t = (m_tier > 0) & im_fenster; g = (m_nah == 0) & im_fenster
        if t.sum() < 50 or g.sum() < 1000: continue
        s_t.append(S[t]); s_h.append(S[g]); v_h.append(V[g])
        br.append(float(aus[:, :, 0][g].mean()) / max(float(aus[:, :, 2][g].mean()), 1e-6))
    cap.release()
    if not s_t: return None
    ST = np.concatenate(s_t); SH = np.concatenate(s_h); VH = np.concatenate(v_h)
    treffer = {T: float((ST > T).mean()) for T in SCHWELLEN}
    fehl = {T: float((SH > T).mean()) for T in SCHWELLEN}
    beste = max(SCHWELLEN, key=lambda T: treffer[T] - fehl[T])
    return {"name": os.path.basename(stamm), "uhr": kopf.get("uhr"), "bilder": len(s_t),
            "tier_punkte": int(ST.size), "hint_punkte": int(SH.size),
            "trefferflaeche_40": treffer[SAT_SCHWELLE], "fehlflaeche_40": fehl[SAT_SCHWELLE],
            "trennkraft_40": treffer[SAT_SCHWELLE] - fehl[SAT_SCHWELLE],
            "beste_schwelle": beste, "trennkraft_beste": treffer[beste] - fehl[beste],
            "s_tier_p75": float(np.percentile(ST, 75)), "s_tier_p90": float(np.percentile(ST, 90)),
            "s_hint_p99": float(np.percentile(SH, 99)), "s_hint_p999": float(np.percentile(SH, 99.9)),
            "v_hint_p50": float(np.percentile(VH, 50)), "blau_durch_rot": float(np.median(br))}


def main():
    ordner = os.path.join(os.path.expanduser("~/mikroskop"), "aufnahmen")
    n_saetze = arg("--saetze", 160); n_bilder = arg("--bilder", 4); grenze = arg("--grenze_s", 900.0)
    stamm_mit_video = sorted(p[:-4] for p in glob.glob(os.path.join(ordner, "*.avi"))
                             if not p.endswith("_rahmen.avi") and os.path.exists(p[:-4] + ".jsonl"))
    if not stamm_mit_video: print("keine Saetze mit Video und Rahmen"); return 1
    wahl = [stamm_mit_video[i] for i in np.linspace(0, len(stamm_mit_video) - 1, min(n_saetze, len(stamm_mit_video))).astype(int)]
    print(f"Problem 6 -- Lichtfarbe ueber die Zeit (1.1). {len(stamm_mit_video)} Saetze mit Video UND Rahmen, "
          f"davon {len(wahl)} gemessen, je bis zu {n_bilder} Bilder.")
    print(f"Regel: Tier, wenn S > {SAT_SCHWELLE} bei {V_MIN} < V < {V_MAX}. Gemessen nur in diesem Fenster.\n")
    t0 = time.time(); aus = []
    for i, s in enumerate(wahl):
        if time.time() - t0 > grenze: print(f"Zeitgrenze nach {i} Saetzen"); break
        try:
            r = satz_messen(s, n_bilder)
            if r: aus.append(r)
        except Exception as e:
            if len(aus) < 3: print(f"  {os.path.basename(s)}: {e}")
    if not aus: print("keine Saetze messbar"); return 1
    print(f"gemessen: {len(aus)} Saetze in {time.time()-t0:.0f} s\n")
    print("Satz             Datum Uhr        Treffer  Fehl   Trennkraft  beste  Trennkraft  S Tier  S Hint   V Hint  Blau")
    print("                                 flaeche  flaeche  bei 40    Schw.  bei bester   p75    p99,9     p50   /Rot")
    for r in aus[:: max(1, len(aus) // 35)]:
        print(f"{r['name']:<16} {str(r['uhr'])[:16]:<16} {100*r['trefferflaeche_40']:6.1f}% {100*r['fehlflaeche_40']:6.2f}% "
              f"{100*r['trennkraft_40']:9.1f}% {r['beste_schwelle']:6d} {100*r['trennkraft_beste']:10.1f}% "
              f"{r['s_tier_p75']:7.0f} {r['s_hint_p999']:7.0f} {r['v_hint_p50']:8.0f} {r['blau_durch_rot']:6.3f}")
    T40 = np.array([r["trefferflaeche_40"] for r in aus]); F40 = np.array([r["fehlflaeche_40"] for r in aus])
    B = np.array([r["beste_schwelle"] for r in aus], float); K40 = np.array([r["trennkraft_40"] for r in aus])
    KB = np.array([r["trennkraft_beste"] for r in aus]); BR = np.array([r["blau_durch_rot"] for r in aus])
    VH = np.array([r["v_hint_p50"] for r in aus]); H999 = np.array([r["s_hint_p999"] for r in aus])
    print(f"\n== Zusammenfassung ueber {len(aus)} Saetze")
    print(f"  Trefferflaeche bei S > 40 (Anteil der Tierpunkte): Median {100*np.median(T40):.1f} %, "
          f"Spanne {100*T40.min():.1f} .. {100*T40.max():.1f} %")
    print(f"  Fehlflaeche bei S > 40 (Anteil der Hintergrundpunkte): Median {100*np.median(F40):.2f} %, "
          f"Spanne {100*F40.min():.2f} .. {100*F40.max():.2f} %")
    print(f"  Hintergrund S im 99,9. Hundertstel: Median {np.median(H999):.0f}, Spanne {H999.min():.0f} .. {H999.max():.0f}")
    print(f"  Beste Schwelle je Satz: Median {np.median(B):.0f}, Spanne {B.min():.0f} .. {B.max():.0f}; "
          f"Saetze, in denen 40 die beste ist: {int((B == SAT_SCHWELLE).sum())} von {len(B)}")
    print(f"  Trennkraft bei 40: Median {100*np.median(K40):.1f} %, bei der besten Schwelle {100*np.median(KB):.1f} % "
          f"-- Verlust durch die feste 40: {100*(np.median(KB)-np.median(K40)):.1f} Punkte")
    print(f"  Helligkeit Hintergrund: Median {np.median(VH):.0f}, Spanne {VH.min():.0f} .. {VH.max():.0f} "
          f"({100*(VH.max()-VH.min())/np.median(VH):.0f} % Schwankung)")
    print(f"  Blau/Rot Hintergrund: Median {np.median(BR):.3f}, Spanne {BR.min():.3f} .. {BR.max():.3f} "
          f"({100*(BR.max()-BR.min())/np.median(BR):.1f} % Schwankung)")
    schlecht = [r for r in aus if r["trennkraft_40"] < 0.5 * np.median(K40)]
    print(f"  Saetze, in denen die Trennkraft auf unter die Haelfte des ueblichen faellt: {len(schlecht)}")
    for r in schlecht[:8]:
        print(f"    {r['name']} ({str(r['uhr'])[:16]}): Treffer {100*r['trefferflaeche_40']:.1f} %, "
              f"Fehl {100*r['fehlflaeche_40']:.2f} %, beste Schwelle {r['beste_schwelle']}")
    heute = time.strftime("%Y-%m-%d")
    json.dump({"saetze": aus, "schwelle": SAT_SCHWELLE, "fenster_v": [V_MIN, V_MAX]},
              open(f"befund_problem6_{heute}.json", "w", encoding="utf-8"))
    print(f"\ngeschrieben: befund_problem6_{heute}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
