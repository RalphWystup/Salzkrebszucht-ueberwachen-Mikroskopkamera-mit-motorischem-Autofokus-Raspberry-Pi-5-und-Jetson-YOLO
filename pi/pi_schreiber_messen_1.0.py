#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pi_schreiber_messen_1.0.py -- laeuft AUF dem Pi. 07.11.2026, Problem 1, dritter Schritt.

pi_warten_messen_1.0.py hat gezeigt: das hohe Lastmittel kommt nicht vom Rechnen (2,35 Aufgaben), sondern vom
Warten auf die Speicherkarte (2,20 Aufgaben, alle im Rueckschreiben: flush-179:0, jbd2, systemd-journal);
34,6 MB in 20 s, und 44 % des Fensters standen Auftraege in der Warteschlange der Karte.

Dieses Programm sagt, WER diese Daten schreibt -- aus /proc/<pid>/io (write_bytes = was wirklich zur Karte geht,
cancelled_write_bytes abgezogen). Dazu, wohin: Groesse der grossen Ordner und die Einstellung des Systemtagebuchs.

NUR LESEN. Aufruf: python3 pi_schreiber_messen_1.0.py [sekunden]   (Vorgabe 30)"""
import os, sys, time, subprocess

FENSTER = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0


def sh(c, t=60):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t); return (r.stdout + r.stderr).strip()
    except Exception as e: return f"(Fehler: {e})"


def io_lesen():
    """write_bytes je Prozess; was nicht lesbar ist (fremder Benutzer), wird ueber sudo versucht."""
    d = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try:
            t = open(f"/proc/{pid}/io").read()
        except Exception:
            continue
        w = c = 0
        for z in t.splitlines():
            if z.startswith("write_bytes:"): w = int(z.split()[1])
            elif z.startswith("cancelled_write_bytes:"): c = int(z.split()[1])
        try:
            name = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
            if not name: name = "[" + open(f"/proc/{pid}/comm").read().strip() + "]"
        except Exception: name = "?"
        d[pid] = (w - c, name[:100])
    return d


def io_sudo():
    """Dasselbe ueber sudo, falls der eigene Benutzer fremde Prozesse nicht lesen darf."""
    t = sh("sudo -n sh -c 'for p in /proc/[0-9]*; do pid=${p#/proc/}; w=$(grep -h ^write_bytes: $p/io 2>/dev/null | awk \"{print \\$2}\"); "
           "c=$(grep -h ^cancelled_write_bytes: $p/io 2>/dev/null | awk \"{print \\$2}\"); "
           "[ -n \"$w\" ] && echo \"$pid $w $c $(tr \\\\0 \\  < $p/cmdline | cut -c1-90)\"; done' 2>/dev/null", 60)
    d = {}
    for z in t.splitlines():
        f = z.split(None, 3)
        if len(f) >= 3 and f[0].isdigit():
            try: d[f[0]] = (int(f[1]) - int(f[2] or 0), (f[3] if len(f) > 3 else "?")[:100])
            except Exception: pass
    return d


print(f"=== Schreiber-Messung {time.strftime('%d.%m.%Y %H:%M:%S')} auf {os.uname().nodename}, Fenster {FENSTER:.0f} s")
mit_sudo = bool(io_sudo())
print(f"Leserecht fuer fremde Prozesse ueber sudo: {'ja' if mit_sudo else 'nein (dann fehlen fremde Prozesse)'}")
lies = io_sudo if mit_sudo else io_lesen
a = lies(); t0 = time.time(); time.sleep(FENSTER); b = lies(); dt = time.time() - t0

zeilen = []
for pid, (w, name) in b.items():
    if pid in a:
        d = (w - a[pid][0]) / 1e6
        if d > 0.05: zeilen.append((d, pid, name))
zeilen.sort(reverse=True)
summe = sum(z[0] for z in zeilen)
print(f"\n== Wer schreibt (MB im Fenster von {dt:.0f} s)   Summe {summe:.1f} MB = {summe/dt:.2f} MB/s = {summe/dt*86.4:.0f} GB je Tag")
print(f"{'MB':>8} {'MB/s':>7} {'PID':>8}  Programm")
for d, pid, name in zeilen[:15]:
    print(f"{d:8.2f} {d/dt:7.3f} {pid:>8}  {name}")

print("\n== Systemtagebuch (journald)")
print(sh("journalctl --disk-usage; grep -E '^#?(Storage|SystemMaxUse|RuntimeMaxUse)' /etc/systemd/journald.conf | head -5"))
print("\n== Grosse Ordner unter /home/pi (nur eine Ebene)")
print(sh("du -sh /home/pi/* 2>/dev/null | sort -h | tail -8"))
print("\n== Aufnahmen auf dem Pi")
print(sh("ls /home/pi/wache/aufnahmen 2>/dev/null | wc -l; du -sh /home/pi/wache/aufnahmen 2>/dev/null; "
         "ls -la --time-style=+%H:%M /home/pi/wache/aufnahmen 2>/dev/null | tail -4"))
print("\n== Was raeumt die Aufnahmen weg (Frist)")
print(sh("grep -rniE 'loesch|unlink|remove|frist|aufraeum' /home/pi/auswertung_1.4.py 2>/dev/null | head -6"))
print("\n== Platte")
print(sh("df -h /; mount | grep -E ' / | /home ' | head -3"))
print("\n== Abnutzung der Karte (falls lesbar)")
print(sh("cat /sys/block/mmcblk0/device/life_time 2>/dev/null || echo '(kein life_time-Eintrag)'"))
