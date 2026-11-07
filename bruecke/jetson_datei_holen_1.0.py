#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_datei_holen_1.0.py -- holt eine Datei vom Jetson ueber die Bruecke (hole -> :8095/datei/<name>/<stueck>), stueckweise
unter der Antwortgrenze von 60 000 Zeichen, prueft sha256 und schreibt sie hierher. Laeuft im Arbeitsbereich (braucht Dienst 1.3).
  python3 jetson_datei_holen_1.0.py montage_fehltreffer.jpg [zielordner]      python3 jetson_datei_holen_1.0.py --liste"""
import sys, json, subprocess, base64, hashlib, pathlib, time
BEF = "<Arbeitsbereich>/befehl.py"; JETSON = "<IP-des-Jetson>:8095"


def hole(pfad):
    r = subprocess.run(["python3", BEF, "-p", "Mikroskop_Laborstation", "hole", f"{JETSON} {pfad}"], capture_output=True, text=True, timeout=120)
    i = r.stdout.find("[") if pfad == "/dateien" else r.stdout.find("{")
    if i < 0: raise RuntimeError("keine JSON-Antwort: " + r.stdout[-200:])
    return json.loads(r.stdout[i:])


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--liste":
        for d in hole("/dateien"): print(f"{d['bytes']:>10}  {d['zeit']}  {d['name']}")
        return 0
    name = sys.argv[1]; ziel = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".") / pathlib.Path(name).name
    t0 = time.time(); d = hole(f"/datei/{name}/0")
    if "fehler" in d: print("FEHLER:", d); return 1
    teile = [d["b64"]]
    for i in range(1, d["stuecke"]):
        e = hole(f"/datei/{name}/{i}")
        if e.get("sha256") != d["sha256"]: print("FEHLER: Datei hat sich waehrend des Holens geaendert"); return 1
        teile.append(e["b64"])
    roh = base64.b64decode("".join(teile))
    if hashlib.sha256(roh).hexdigest() != d["sha256"] or len(roh) != d["bytes"]: print("FEHLER: Pruefsumme falsch"); return 1
    ziel.write_bytes(roh); print(f"{ziel}: {len(roh)} Bytes in {d['stuecke']} Stuecken, {time.time()-t0:.0f} s, sha256 stimmt")
    return 0


if __name__ == "__main__": sys.exit(main())
