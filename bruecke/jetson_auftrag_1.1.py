#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_auftrag_1.1.py -- gibt dem Jetson ein Skript zur Ausfuehrung, OHNE Jetson-Kennwort: das Skript geht als pi.py-Job
auf den Pi nach /home/pi/wache/halten/jetson_auftraege/<stamm>_<HHMMSS>.py; der Jetson-Dienst (ab 1.3) holt es im naechsten
Takt (60 s), fuehrt es einmal aus (Arbeitsordner ~/mikroskop) und legt die Ausgabe als auftraege/<name>.aus.txt ab, die hier
ueber jetson_datei_holen_1.0.py geholt und gezeigt wird. Ein pi.py-Job zugleich (Bruecke) -- vorher pgrep -af hole_aufnahme.
  python3 jetson_auftrag_1.1.py skript.py [--warten 900] [--ziel ordner]
1.1 (06.11.2026): Ausgaben nach jetson_ausgaben/ neben diesem Programm (1.0 schrieb in den Scratch-Ordner einer bestimmten
Sitzung, der nach deren Ende fehlt); --ziel waehlt einen anderen Ordner."""
import sys, subprocess, pathlib, time, json, shutil
L = pathlib.Path("<Ausgabeordner-im-Arbeitsbereich>"); BEF = "<Arbeitsbereich>/befehl.py"; JETSON = "<IP-des-Jetson>:8095"
SCRATCH = pathlib.Path(__file__).resolve().parent / "jetson_ausgaben"
HOLER = pathlib.Path(__file__).resolve().parent / "jetson_datei_holen_1.0.py"


def bruecke(args, t=300):
    return subprocess.run(["python3", BEF, "-p", "Mikroskop_Laborstation"] + args, capture_output=True, text=True, timeout=t).stdout


def main():
    if len(sys.argv) < 2: print(__doc__); return 1
    global SCRATCH
    q = pathlib.Path(sys.argv[1]); warten = int(sys.argv[sys.argv.index("--warten") + 1]) if "--warten" in sys.argv else 900
    if "--ziel" in sys.argv: SCRATCH = pathlib.Path(sys.argv[sys.argv.index("--ziel") + 1])
    name = f"{q.stem}_{time.strftime('%H%M%S')}.py"; shutil.copy(q, L / name)
    (L / "pi_hochladen.txt").write_text(f"{name} -> /home/pi/wache/halten/{name}\n")
    (L / "pi_auftrag.txt").write_text(f"mkdir -p /home/pi/wache/halten/jetson_auftraege && cp /home/pi/wache/halten/{name} /home/pi/wache/halten/jetson_auftraege/ && ls -la /home/pi/wache/halten/jetson_auftraege/{name}\n")
    bruecke(["update", f"{name},pi_hochladen.txt,pi_auftrag.txt -> <Brückenordner-auf-dem-PC>"]); aus = bruecke(["python", "pi.py"])
    if name not in aus: print("FEHLER beim Ablegen auf dem Pi:", aus[-300:]); return 1
    print(f"{name} liegt auf dem Pi; warte auf den Jetson (bis {warten} s) ...")
    t0 = time.time(); fertig = False
    while time.time() - t0 < warten:
        time.sleep(20)
        try:
            r = bruecke(["hole", f"{JETSON} /stand"], 90); d = json.loads(r[r.find("{"):]); a = d.get("auftraege") or {}
            if a.get("letzter") == name: print(f"erledigt {a.get('ende')} rc {a.get('rc')}"); fertig = True; break
            print(f"  {time.strftime('%H:%M:%S')} Jetson: {d.get('auftrag')}", flush=True)
        except Exception as e: print("  (Stand nicht lesbar:", str(e)[:80], ")")
    if not fertig: print("Zeit abgelaufen -- Ausgabe spaeter holen: jetson_datei_holen_1.0.py auftraege/" + name[:-3] + ".aus.txt"); return 2
    SCRATCH.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["python3", str(HOLER), f"auftraege/{name[:-3]}.aus.txt", str(SCRATCH)], capture_output=True, text=True, timeout=600)
    print(r.stdout.strip()); p = SCRATCH / f"{name[:-3]}.aus.txt"
    if p.exists(): print("--- Ausgabe:"); print(p.read_text(encoding="utf-8", errors="replace")[-6000:])
    return 0


if __name__ == "__main__": sys.exit(main())
