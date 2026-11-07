#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_fahren_1.3.py -- schiebt ein Programm auf den Jetson und laesst es dort laufen (laeuft auf dem PC in <Brückenordner-auf-dem-PC>).

Aufruf:  python jetson_fahren_1.3.py <ip> <benutzer | -> <kennwort | -> <datei.py> [--pip=paket]

1.3 (06.11.2026, sein Wort: "das haben wir doch schon gemacht mit dem CFD Projekt"): Steht als Kennwort (oder Benutzer) ein
Bindestrich, kommt der Wert aus dem Zugangsblatt des Rechenverbunds <Zugangsblatt-auf-dem-PC> (26.10.2026,
Abschnitt JETSON, Zeilen "  Kennwort<22 breit>Wert" aus zugangsblatt.py) -- oder, falls vorhanden, aus <Schlüsseldatei-auf-dem-PC>.
Nichts davon steht je in einer Befehlszeile oder im Gespraech.

1.2 (06.11.2026): nimmt neben jetson.key auch jetson.key.txt (der Windows-Editor haengt gern .txt an) und liest die Datei
als UTF-8 mit oder ohne Byte-Reihenfolge-Marke -- damit die einmalige Anlage von Hand nicht an Kleinigkeiten scheitert.

1.1 (06.11.2026, sein Wort: "das Kennwort darf nie wieder durch meine Befehle laufen ... dann kodiere es!"):
Steht als Kennwort ein Bindestrich, liest das Programm das Kennwort aus der Datei <Schlüsseldatei-auf-dem-PC> (eine Zeile),
die er EINMAL selbst anlegt (Editor, Inhalt: das Kennwort, speichern). Dann traegt kein Aufruf aus dem Arbeitsbereich und
keine Befehlszeile das Kennwort mehr; auf dem Jetson geht es wie bisher nur ueber die Umgebung JK an sudo.
Sonst wie 1.0: Datei muss neben diesem Programm liegen, landet unter ~/messung/ und wird dort mit python3 gestartet.
"""
import sys, os, re, subprocess, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    import paramiko
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "paramiko"], timeout=300)
    import paramiko

if len(sys.argv) < 5:
    print(__doc__); sys.exit(1)
ip, ben, kw, datei = sys.argv[1:5]
pakete = [a.split("=", 1)[1] for a in sys.argv[5:] if a.startswith("--pip=")]
hier = os.path.dirname(os.path.abspath(__file__))
BLATT = r"<Zugangsblatt-auf-dem-PC>"


def blatt_wert(feld):
    """Wert eines Feldes aus dem JETSON-Abschnitt des Zugangsblatts (Titel in Grossbuchstaben, Felder eingerueckt)."""
    if not os.path.isfile(BLATT): return None
    im_jetson = False
    for z in open(BLATT, encoding="utf-8-sig"):
        s = z.rstrip("\n")
        if s and not s.startswith(" ") and s.isupper(): im_jetson = s.startswith("JETSON"); continue
        if not im_jetson: continue
        m = re.match(r"\s*" + re.escape(feld) + r"\s{2,}(\S.*)$", s)
        if m and "von Hand" not in m.group(1): return m.group(1).strip()
    return None


def kennwort_finden():
    for n in ("jetson.key", "jetson.key.txt"):
        p = os.path.join(hier, n)
        if os.path.isfile(p):
            k = open(p, encoding="utf-8-sig").read().strip()
            if k: return k
            print(f"FEHLER: {p} ist leer"); sys.exit(1)
    k = blatt_wert("Kennwort")
    if k: return k
    print(f"FEHLER: kein Jetson-Kennwort gefunden -- weder {hier}\\jetson.key noch im Zugangsblatt {BLATT}"); sys.exit(1)


if ben == "-":
    ben = blatt_wert("Benutzer") or "<jetson-benutzer>"
if kw == "-":
    kw = kennwort_finden()
quelle = datei if os.path.isabs(datei) else os.path.join(hier, datei)
if not os.path.isfile(quelle):
    print(f"FEHLER: {quelle} gibt es nicht"); sys.exit(1)

c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect(ip, username=ben, password=kw, timeout=15, banner_timeout=25,
              allow_agent=False, look_for_keys=False)
except Exception as e:
    print(f"FEHLER: Anmeldung an {ip}: {type(e).__name__}: {e}"); sys.exit(1)

def lauf(b, t=3000, still=False):
    i, o, e = c.exec_command(b, timeout=t)
    a = o.read().decode("utf-8", "replace"); f = e.read().decode("utf-8", "replace")
    if not still:
        if a.strip(): print(a.rstrip())
        if f.strip(): print("  [stderr] " + f.strip()[:1500])
    return a, f

lauf("mkdir -p ~/messung", still=True)
sftp = c.open_sftp()
ziel = "messung/" + os.path.basename(quelle)
sftp.put(quelle, ziel)
sftp.close()
print(f"{os.path.basename(quelle)} liegt auf dem Jetson unter ~/{ziel}\n")

for p in pakete:
    print(f"--- hole {p} ---")
    lauf(f"python3 -m pip install --quiet {p} 2>&1 | tail -5", t=1800)
    print()

t0 = time.time()
# JK traegt das Kennwort fuer sudo-Schritte -- ueber die Umgebung, nicht ueber die
# Befehlszeile: dort stuende es in der Prozessliste des Jetson fuer jeden lesbar.
lauf(f"cd ~/messung && JK={kw!r} python3 -u {os.path.basename(quelle)}", t=3000)
print(f"\n(Laufzeit auf dem Jetson: {time.time()-t0:.1f} s)")
c.close()
