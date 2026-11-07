#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_ruecksetzprobe_1.0.py -- laeuft als Jetson-Auftrag im Ordner ~/mikroskop. 07.11.2026.

Prueft den neuen Knopf "alles Gelernte zuruecksetzen" (Dienst 1.11, POST /lernen/zuruecksetzen) AM ECHTEN
GERAET und an seinen echten Bewertungen -- und stellt sie sofort wieder her. Sein Grundsatz: Knopfprobe statt
HTTP 200; und: ein Knopf, der Daten loescht, ist erst dann geprueft, wenn auch das Wiederherstellen geprueft ist.

Ablauf, mit ZWEI unabhaengigen Sicherungen:
  1. eigene Vollkopie des Ordners lernen/bilder nach lernen/bilder_probe_<stamp>   (Sicherung A)
  2. Stand vorher festhalten (Zahl je Zustand)
  3. POST /lernen/zuruecksetzen -- der Dienst schreibt dabei selbst lernen/sicherung_<stamp>.json (Sicherung B)
  4. Nachsehen: steht jetzt wirklich alles auf "offen"?
  5. Wiederherstellen AUS SICHERUNG B (nicht aus A) -- damit ist belegt, dass die Sicherung des Dienstes taugt
  6. Nachsehen: ist der Stand vorher wieder da, Bild fuer Bild, Rahmen fuer Rahmen?
  7. Sicherung A bleibt liegen; sie wird nicht geloescht (Regel: nichts loeschen ohne sein Wort)

Dazu Punkt 8: laesst sich ueber den Dienst der Stand "zurueckgestellt" speichern (neu in 1.11)? Geprueft an
einem Bild, das ohnehin schon zurueckgestellt ist -- der Inhalt aendert sich dadurch nicht.

  python3 jetson_ruecksetzprobe_1.0.py
"""
import os, json, glob, time, shutil, collections, urllib.request

H = os.path.expanduser("~/mikroskop"); LERNEN = os.path.join(H, "lernen", "bilder")
DIENST = "http://127.0.0.1:8095"


def stand():
    z = collections.Counter(); inhalt = {}
    for p in sorted(glob.glob(LERNEN + "/*.json")):
        try: d = json.load(open(p, encoding="utf-8"))
        except Exception: continue
        n = os.path.basename(p)[:-5]; inhalt[n] = d; z[d.get("status", "offen")] += 1
    return z, inhalt


def post(pfad, d):
    r = urllib.request.urlopen(urllib.request.Request(DIENST + pfad, data=json.dumps(d).encode(),
                               headers={"Content-Type": "application/json"}, method="POST"), timeout=60)
    return json.loads(r.read().decode())


P = []
def pruef(name, ok, txt): P.append((name, ok, txt)); print(f"  {'JA  ' if ok else 'NEIN'} {name:<48} {txt}")


stamp = time.strftime("%Y%m%d_%H%M%S")
print(f"Ruecksetzprobe {time.strftime('%d.%m.%Y %H:%M:%S')} auf {os.uname().nodename}\n")

# 1. eigene Vollkopie
kopie = os.path.join(H, "lernen", f"bilder_probe_{stamp}")
shutil.copytree(LERNEN, kopie)
pruef("P1 eigene Vollkopie angelegt", os.path.isdir(kopie) and len(glob.glob(kopie + "/*.json")) > 0,
      f"{len(glob.glob(kopie + '/*.json'))} Dateien in {os.path.basename(kopie)}")

# 2. Stand vorher
vorher, inhalt_vorher = stand()
print(f"       Stand vorher: {dict(vorher)}")

# 3. Zuruecksetzen ueber den Dienst
try:
    a = post("/lernen/zuruecksetzen", {})
except Exception as e:
    a = {"ok": False, "fehler": str(e)}
pruef("P2 Dienst nimmt /lernen/zuruecksetzen an", bool(a.get("ok")), str(a)[:120])
sicherung = os.path.join(H, "lernen", a.get("sicherung", "")) if a.get("ok") else ""
pruef("P3 Dienst hat selbst gesichert", bool(sicherung) and os.path.isfile(sicherung),
      os.path.basename(sicherung) if sicherung else "keine Sicherung gemeldet")

# 4. steht alles auf offen?
nachher, _ = stand()
pruef("P4 danach ist alles offen", nachher.get("offen", 0) == sum(vorher.values()) and len(nachher) == 1,
      f"{dict(nachher)}")

# 5. Wiederherstellen AUS DER SICHERUNG DES DIENSTES
n_zurueck = 0
try:
    sich = json.load(open(sicherung, encoding="utf-8"))["bilder"]
    for n, d in sich.items():
        p = os.path.join(LERNEN, n + ".json"); tmp = p + ".tmp"
        json.dump(d, open(tmp, "w", encoding="utf-8")); os.replace(tmp, p); n_zurueck += 1
    ok5 = True; txt5 = f"{n_zurueck} Bilder aus {os.path.basename(sicherung)} zurueckgeschrieben"
except Exception as e:
    ok5 = False; txt5 = f"FEHLER: {e}"
pruef("P5 Wiederherstellen aus der Dienstsicherung", ok5, txt5)

# 6. ist alles wieder wie vorher?
wieder, inhalt_wieder = stand()
gleich_zahl = dict(wieder) == dict(vorher)
unterschiede = [n for n in inhalt_vorher if json.dumps(inhalt_vorher[n], sort_keys=True) != json.dumps(inhalt_wieder.get(n), sort_keys=True)]
pruef("P6 Zahlen wieder wie vorher", gleich_zahl, f"{dict(wieder)}")
pruef("P7 jede Datei wieder Zeichen fuer Zeichen gleich", not unterschiede,
      "kein Unterschied" if not unterschiede else f"{len(unterschiede)} Dateien anders: {unterschiede[:3]}")

# 8. Stand "zurueckgestellt" ueber den Dienst speicherbar?
kand = next((n for n, d in inhalt_wieder.items() if d.get("status") == "zurueckgestellt"), None)
if kand:
    d = inhalt_wieder[kand]
    try:
        b = post("/lernen/boxen/" + kand, {"boxen": d.get("boxen", []), "status": "zurueckgestellt"})
        ok8 = b.get("ok") and b.get("status") == "zurueckgestellt"; txt8 = str(b)[:100]
    except Exception as e:
        ok8 = False; txt8 = str(e)[:100]
    pruef("P8 Stand 'zurueckgestellt' speicherbar (neu in 1.11)", ok8, txt8)
else:
    pruef("P8 Stand 'zurueckgestellt' speicherbar", False, "kein zurueckgestelltes Bild gefunden")

n_ok = sum(1 for _, o, _ in P if o)
print(f"\n===== RUECKSETZPROBE {n_ok} von {len(P)} bestanden")
print(f"Eigene Vollkopie bleibt liegen: {kopie}  (nicht geloescht -- Regel 42)")
print(f"Sicherung des Dienstes bleibt liegen: {sicherung}")
