#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pi_warten_messen_1.0.py -- laeuft AUF dem Pi. 07.11.2026, Nachtrag zu Problem 1.

pi_last_messen_1.0.py hat gemessen: nur 2,12 von 4 Kernen sind mit Rechnen belegt, das Lastmittel steht aber
bei 4,3 bis 5,1. Die Differenz sind Aufgaben, die NICHT rechnen, sondern warten (Zustand D, ununterbrechbar --
fast immer Platte oder Geraet). Dieses Programm sagt, wer das ist und worauf gewartet wird:

  - Zustandszaehlung alle 0,5 s ueber das Fenster: wie viele Aufgaben laufen (R), wie viele warten (D)
  - welche Programme im Wartezustand stehen und an welcher Kernfunktion (wchan)
  - Drucklage des Kerns (/proc/pressure): Anteil der Zeit, in der ueberhaupt jemand auf CPU, Platte oder
    Speicher wartet -- das ist die Zahl, die sagt, ob es eng ist, nicht das Lastmittel
  - Plattenverkehr je Geraet ueber dasselbe Fenster

NUR LESEN. Aufruf: python3 pi_warten_messen_1.0.py [sekunden]   (Vorgabe 20)"""
import os, sys, time, collections

FENSTER = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
TAKT = 0.5


def lies(p, vorgabe=""):
    try: return open(p).read()
    except Exception: return vorgabe


def zustaende():
    r = d = 0; wer = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        s = lies(f"/proc/{pid}/stat")
        if not s: continue
        try:
            z = s[s.rindex(")") + 2:].split(); zu = z[0]
            name = s[s.index("(") + 1:s.rindex(")")]
        except Exception: continue
        if zu == "R": r += 1
        elif zu == "D":
            d += 1; wer.append((name, lies(f"/proc/{pid}/wchan", "?").strip() or "?"))
    return r, d, wer


def druck():
    aus = {}
    for art in ("cpu", "io", "memory"):
        t = lies(f"/proc/pressure/{art}")
        for zeile in t.splitlines():
            if zeile.startswith(("some", "full")):
                teil = dict(x.split("=") for x in zeile.split()[1:])
                aus[f"{art}.{zeile.split()[0]}"] = float(teil.get("total", 0)) / 1e6      # Sekunden
    return aus


def diskstats():
    aus = {}
    for z in lies("/proc/diskstats").splitlines():
        f = z.split()
        if len(f) < 14: continue
        name = f[2]
        if not (name.startswith("mmcblk") or name.startswith("sd") or name.startswith("nvme")): continue
        if name[-1].isdigit() and "p" not in name and not name.startswith("sd"): continue
        aus[name] = {"lese_sektoren": int(f[5]), "schreib_sektoren": int(f[9]), "warte_ms": int(f[12])}
    return aus


print(f"=== Wartemessung {time.strftime('%d.%m.%Y %H:%M:%S')} auf {os.uname().nodename}, {os.cpu_count()} Kerne, Fenster {FENSTER:.0f} s")
d0 = druck(); k0 = diskstats(); t0 = time.time()
rr = []; dd = []; warter = collections.Counter(); funktionen = collections.Counter()
while time.time() - t0 < FENSTER:
    r, d, wer = zustaende(); rr.append(r); dd.append(d)
    for name, fkt in wer:
        warter[name] += 1; funktionen[f"{name} @ {fkt}"] += 1
    time.sleep(TAKT)
dt = time.time() - t0; d1 = druck(); k1 = diskstats()
n = len(rr)

print(f"\n== Zustaende ({n} Stichproben im Abstand {TAKT} s)")
print(f"  rechnend (R): Mittel {sum(rr)/n:.2f}, hoechstens {max(rr)}")
print(f"  wartend  (D): Mittel {sum(dd)/n:.2f}, hoechstens {max(dd)}")
print(f"  Summe R+D (das ist, was ins Lastmittel geht): {sum(rr)/n + sum(dd)/n:.2f}")
print(f"  Lastmittel jetzt: {lies('/proc/loadavg').split()[0:3]}")

print(f"\n== Wer wartet (Anteil der Stichproben, in denen das Programm im Zustand D stand)")
for name, c in warter.most_common(10):
    print(f"  {name:<22} {100.0*c/n:6.1f} %")
print(f"\n== Worauf gewartet wird (Programm @ Kernfunktion)")
for f, c in funktionen.most_common(10):
    print(f"  {f:<50} {100.0*c/n:6.1f} %")

print(f"\n== Drucklage (/proc/pressure), Anteil des Fensters von {dt:.0f} s")
for k in sorted(set(d0) | set(d1)):
    anteil = 100.0 * (d1.get(k, 0) - d0.get(k, 0)) / dt
    art = "irgendeine Aufgabe wartet" if k.endswith("some") else "ALLE Aufgaben warten"
    print(f"  {k:<14} {anteil:6.1f} %   ({art})")

print(f"\n== Plattenverkehr im Fenster")
for name in sorted(set(k0) | set(k1)):
    a, b = k0.get(name, {}), k1.get(name, {})
    if not a or not b: continue
    lese = (b["lese_sektoren"] - a["lese_sektoren"]) * 512 / 1e6
    schr = (b["schreib_sektoren"] - a["schreib_sektoren"]) * 512 / 1e6
    warte = (b["warte_ms"] - a["warte_ms"]) / 1000.0
    print(f"  {name:<10} gelesen {lese:7.1f} MB   geschrieben {schr:7.1f} MB   Wartezeit aller Auftraege {warte:6.1f} s "
          f"({100.0*warte/dt:.0f} % des Fensters)")
print(f"\n== Platz und Temperatur")
print(os.popen("df -h / | tail -1; vcgencmd measure_temp; vcgencmd get_throttled").read().strip())
