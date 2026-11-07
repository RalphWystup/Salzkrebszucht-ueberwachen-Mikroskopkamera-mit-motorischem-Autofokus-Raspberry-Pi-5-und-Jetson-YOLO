#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pi_last_messen_1.0.py -- laeuft AUF dem Pi. 07.11.2026, Problem 1 des Plans (Rechenlast knapp).
Misst den CPU-Anteil JE PROZESS ueber ein echtes Zeitfenster aus /proc/<pid>/stat (utime+stime), Kernfaeden
eingeschlossen -- nicht geschaetzt, nicht aus top abgelesen. Dazu: woher der Faden w1_bus_master kommt
(Overlays in config.txt, geladene Bausteine, Geraete am 1-Wire-Bus), Drosselung, Temperatur, Arbeitsspeicher.
NUR LESEN. Aufruf: python3 pi_last_messen_1.0.py [sekunden]   (Vorgabe 20 s)"""
import os, sys, time, subprocess

FENSTER = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
TAKT = os.sysconf("SC_CLK_TCK"); KERNE = os.cpu_count()


def sh(c, t=20):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"(Fehler: {e})"


def schnappschuss():
    d = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                s = f.read()
            z = s[s.rindex(")") + 2:].split()
            name = s[s.index("(") + 1:s.rindex(")")]
            d[pid] = (int(z[11]) + int(z[12]), name)      # utime + stime in Takten
        except Exception:
            pass
    return d


def befehlszeile(pid, name):
    try:
        c = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except Exception:
        c = ""
    return c[:110] if c else f"[{name}]"                  # leer = Kernfaden


print(f"=== Lastmessung {time.strftime('%d.%m.%Y %H:%M:%S')} auf {os.uname().nodename}, {KERNE} Kerne, Fenster {FENSTER:.0f} s")
a = schnappschuss(); la0 = open("/proc/loadavg").read().split()[:3]; t0 = time.time()
time.sleep(FENSTER)
b = schnappschuss(); t1 = time.time(); dt = t1 - t0
la1 = open("/proc/loadavg").read().split()[:3]

zeilen = []
for pid, (takte, name) in b.items():
    if pid in a:
        d = (takte - a[pid][0]) / TAKT / dt               # Kerne
        if d >= 0.005:
            zeilen.append((d, pid, name))
zeilen.sort(reverse=True)
summe = sum(z[0] for z in zeilen)
print(f"Lastmittel vorher {la0} nachher {la1}; gemessene Summe {summe:.2f} von {KERNE} Kernen ({100*summe/KERNE:.0f} %)")
print(f"{'Kerne':>6}  {'%1Kern':>7}  {'PID':>8}  Programm")
for d, pid, name in zeilen[:22]:
    print(f"{d:6.2f}  {100*d:6.0f}%  {pid:>8}  {befehlszeile(pid, name)}")

print("\n=== 1-Wire: woher kommt w1_bus_master?")
print("--- Zeilen mit w1/therm/gpio in /boot/firmware/config.txt:")
print(sh("grep -nE 'w1|therm|gpio' /boot/firmware/config.txt 2>/dev/null || grep -nE 'w1|therm|gpio' /boot/config.txt 2>/dev/null"))
print("--- geladene Bausteine:"); print(sh("lsmod | grep -E '^w1|^wire|therm' || echo '(keine)'"))
print("--- Geraete am Bus:"); print(sh("ls -la /sys/bus/w1/devices/ 2>&1 | head -10"))
print("--- Suchtakt des Busses (such_intervall, Sekunden):")
print(sh("cat /sys/bus/w1/devices/w1_bus_master*/w1_master_search /sys/bus/w1/devices/w1_bus_master*/w1_master_timeout 2>&1 | head -4"))
print("--- Wer zieht die Overlays (cmdline):"); print(sh("cat /proc/device-tree/soc/*w1*/status 2>/dev/null | tr -d '\\0'; echo; vcgencmd get_config str 2>/dev/null | grep -i w1 || echo '(vcgencmd ohne w1-Eintrag)'"))

print("\n=== Drosselung, Temperatur, Takt:")
print(sh("vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd measure_clock arm"))
print("=== Arbeitsspeicher:"); print(sh("free -m"))
print("=== Laufende Mikroskop-Einheiten:")
print(sh("systemctl list-units --type=service --state=running --no-pager --no-legend | grep -iE 'mikroskop|wache|fokus|kiosk' | cut -c1-110 || echo '(keine)'"))
print("=== Alle laufenden Einheiten:")
print(sh("systemctl list-units --type=service --state=running --no-pager --no-legend | cut -c1-80"))
print("=== Bildschirmsitzung / Kiosk:")
print(sh("ps -eo pid,etimes,comm,args --sort=-etimes | grep -iE 'firefox|chromium|xinit|labwc|wayfire|lightdm' | grep -v grep | cut -c1-140 | head -8"))
