#!/usr/bin/env python3
"""jetson_zaehler_verlauf_1.0.py -- Stundenzaehler ueber die Tage: YOLO-Livedienst (:8096/stand, zaehler.stunden) und Pi-Auswertung
(http://mikroskop:8092/zaehler bzw. /stand), je Tag Mittel der Stundenmittel (Tiere je Bild), Hoechstwert; dazu jede Stunde knapp.
1.0 (14.11.2026). Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import json, urllib.request, collections, statistics as st
def hole(url):
    try: return json.loads(urllib.request.urlopen(url, timeout=8).read())
    except Exception as ex: return {"fehler": str(ex)}
def tafel(name, stunden):
    print(f"=== {name}: {len(stunden)} Stunden")
    tage = collections.defaultdict(list)
    for s in stunden:
        u = s.get("uhr", ""); tage[u[:10]].append(s)
    for t in sorted(tage):
        L = tage[t]; m = [x.get("mittel") for x in L if x.get("mittel") is not None]; h = [x.get("hoechstens") for x in L if x.get("hoechstens") is not None]
        print(f"  {t}: {len(L):2d} h  Mittel {st.mean(m):5.2f}  (min {min(m):4.2f} max {max(m):4.2f})  Hoechst {max(h) if h else '-'}  Bilder {sum(x.get('bilder', 0) for x in L)}")
    print("  Stunden:", " ".join(f"{s.get('uhr','')[5:13]}={s.get('mittel')}" for s in stunden))
y = hole("http://127.0.0.1:8096/stand"); tafel("YOLO (Jetson :8096)", (y.get("zaehler") or {}).get("stunden", []) + ([y["zaehler"]["laufend"]] if isinstance(y.get("zaehler"), dict) and y["zaehler"].get("laufend") else []))
for url in ("http://mikroskop:8092/zaehler", "http://mikroskop:8092/stand"):
    p = hole(url)
    if "fehler" in p: print(url, "FEHLER", p["fehler"]); continue
    z = p.get("zaehler", p); stunden = z.get("stunden") if isinstance(z, dict) else None
    if stunden: tafel("Pi-Auswertung OpenCV (" + url + ")", stunden + ([z["laufend"]] if z.get("laufend") else [])); break
    print(url, "Schluessel:", list(p)[:20])
