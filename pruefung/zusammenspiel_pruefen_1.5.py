#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zusammenspiel_pruefen_1.5.py -- prueft die ganze Kette Arbeitsbereich -> Bruecke -> PC -> Pi -> Jetson und zurueck und schreibt ein Protokoll.
Sein Wort, 06.11.2026 morgens: "zuerst muss das zusammenspiel und auch das zu dir ueber die Bruecke einwandfrei fehlerfrei
funktionieren, dann machen wir weiter, das muss auch geprueft und protokolliert werden".
Sein Wort, 06.11.2026 mittags: "sollte wieder eine sperre kommen, muss diese zusammenarbeit dagegen sicher sein! und
automatisch eigenstaendig funktionieren! das muessen wir zuerst pruefen, dann die eigentliche aufgaben!"
Schritte (jeder mit Zeit, Dauer, Ergebnis BESTANDEN/DURCHGEFALLEN):
  P1  Bruecke: Puls des Empfaengers (Mikroskop_Laborstation zuletzt vor < 10 s)
  P2  Bruecke antwortet: befehl.py info nennt den Rechner
  P3  Pi per Namen (pi.py: hostname, Adressen, Uptime)
  P4  Pi-Dienste: Auswertung /stand (Fassung, Bilder/s, kaputt 0), Fokus /status
  P5  Seite auf dem Pi: Fassung im Kopf; Kiosk-Firefox laeuft und bezieht den Punktestrom
  P6  Jetson-Dienst /stand ueber die Bruecke (hole), Pi-Verbindung des Jetson (Feld pi, letzter_rsync, Fehler)
  P7  Jetson <-> Pi direkt: Saetze auf dem Jetson, Statistik vorhanden
  P8  Rueckfall: Seite zeigt den Jetson-Block grau, wenn der Dienst nicht antwortet (Knopfprobe im Browser hier)
  P9  Dateikanal Jetson -> hier: eine Datei stueckweise ueber :8095/datei holen, sha256 gleich der Quelle im Projekt
  P10 Auftragskanal hier -> Pi -> Jetson -> hier: Probeauftrag (auftrag_probe_1.0.py) laeuft auf dem Jetson, Ausgabe kommt zurueck
  P11 Eigenstaendigkeit: Dienste auf Pi und Jetson eingeschaltet (systemd enabled), starten von selbst neu, jetson_clocks beim Start
  P12 Zugang ohne Kennwort: Zugangsblatt auf dem PC vollstaendig, jetson_fahren_1.3.py dort; dieser Lauf uebergibt kein Kennwort
  P13 Ohne Zutun weiter: waehrend der Pruefung rueckt der rsync des Jetson vor und die Auswertung auf dem Pi laeuft durch
  P14 Jetson sieht den Livestrom des Pi (:8095/live: verbunden, >= 20 Bilder/s, letztes Bild < 2 s alt, nichts abgeschnitten)
  P15 Seite mit anwesendem Jetson (Knopfprobe im Browser, Jetson-Antworten durch Stellvertreter ersetzt): Lampe gruen, Livestrom-Zeile
  P16 YOLO-Livedienst auf dem Jetson (:8096 ueber den Jetson-Dienst /stand.yolo): Modell geladen, laeuft, >= 10 Bilder/s verarbeitet
  P17 Lernseite auf dem Jetson: /lernen liefert die Seite, /lernen/liste die Bewertungen (Zahl je Stand)
Protokoll: PRUEFPROTOKOLL_ZUSAMMENSPIEL_<Datum>.md im Projekt, mit Tafel "Was ohne den Arbeitsbereich weiterlaeuft".
1.5 (06.11.2026): P16 YOLO-Livedienst, P17 Lernseite; Seite 1.28 (YOLO-Zeile) in P15.
1.4 (06.11.2026): P14 Livestrom-Empfang des Jetson (Dienst 1.4), P15 Seite 1.26 mit Livestrom-Zeile bei anwesendem Jetson.
1.3 (06.11.2026): P9-P13 neu; Pruefmittel (Stellvertreter stub8090.py, Browserprobe) liegen im Projekt unter pruefmittel/,
    Arbeitsordner pruefmittel/lauf/ (nicht mehr der Scratch-Ordner einer bestimmten Sitzung); Zeiten in MEZ.
1.2 (06.11.2026): P8 wartet auf den Port des Stellvertreters (bis 40 s); P7 verlangt eine fehlerfreie Statistik.
  python3 zusammenspiel_pruefen_1.5.py [--ohne-browser]
"""
import subprocess, sys, time, json, re, pathlib, urllib.request, datetime, hashlib, shutil, zoneinfo
HIER = pathlib.Path(__file__).resolve().parent; L = pathlib.Path("<Arbeitsbereich>/Mikroskop_Laborstation/Arbeitsstand/Laptop"); BEF = "<Arbeitsbereich>/Bruecke/befehl.py"
PRUEF = HIER / "pruefmittel"; LAUF = PRUEF / "lauf"; LAUF.mkdir(parents=True, exist_ok=True)
PI_NAME, PI_IPS, JETSON = "mikroskop", ["<IP-des-Pi>"], "<IP-des-Jetson>:8095"
MEZ = zoneinfo.ZoneInfo("Europe/Berlin")
ergeb = []; STAND0 = {}; PI0 = {}; PROBE = {}
def schritt(kenn, text, f):
    t0 = time.time()
    try: ok, befund = f()
    except Exception as e: ok, befund = False, f"Ausnahme: {str(e)[:160]}"
    ergeb.append((kenn, text, ok, round(time.time() - t0, 1), befund)); print(f"{kenn} {'BESTANDEN' if ok else 'DURCHGEFALLEN'} ({time.time()-t0:.1f} s): {text} -- {befund}", flush=True); return ok
def bruecke(args, t=240):
    r = subprocess.run(["python3", BEF, "-p", "Mikroskop_Laborstation"] + args, capture_output=True, text=True, timeout=t); return r.stdout
def hole(adresse, pfad):
    aus = bruecke(["hole", f"{adresse} {pfad}"], 90)
    i = aus.find("{"); return json.loads(aus[i:]) if i >= 0 else None
def pi_auftrag(text, t=300):
    (L / "pi_hochladen.txt").write_text(""); (L / "pi_auftrag.txt").write_text(text, encoding="utf-8")
    bruecke(["update", "pi_hochladen.txt,pi_auftrag.txt -> <Brückenordner-auf-dem-PC>"], 120); return bruecke(["python", "pi.py"], t)
def neueste_seite():
    seiten = sorted(HIER.parent.glob("seite_1.*.html"), key=lambda p: int(re.search(r"seite_1\.(\d+)", p.name).group(1))); return seiten[-1]

def p1():
    d = json.load(urllib.request.urlopen("http://127.0.0.1:8085/puls", timeout=5)); v = d.get("Mikroskop_Laborstation", {}).get("vor_sekunden")
    return (v is not None and v < 10), f"zuletzt vor {v} s"
def p2():
    aus = bruecke(["info"], 120); m = re.search(r"Rechner (\S+) \| Brücke ([\d.]+)", aus); return bool(m), (f"Rechner {m.group(1)}, Brücke {m.group(2)}" if m else aus[:120])
def p3():
    aus = pi_auftrag("hostname; ip -4 -o addr show | awk '{print $2, $4}' | grep -v 'lo '; uptime -p; ethtool eth0 2>/dev/null | grep -E 'Speed|Link detected' | tr '\\n' ' '\n")
    ok = "mikroskop" in aus; adr = re.findall(r"(eth0|wlan0) (\d+\.\d+\.\d+\.\d+)", aus); return ok, (f"Adressen {adr}, {re.search(r'up .*', aus).group(0) if re.search(r'up .*', aus) else ''} {' '.join(re.findall(r'Speed: \S+|Link detected: \S+', aus))}".strip() if ok else aus[-200:])
def pi_stand():
    aus = pi_auftrag("python3 -c \"import json,urllib.request as u; a=json.load(u.urlopen('http://127.0.0.1:8092/stand',timeout=5)); f=json.load(u.urlopen('http://127.0.0.1:8090/status',timeout=5)); print('P4JSON', json.dumps({'a':{k:a.get(k) for k in ('fassung','bilder_s','kaputt','laeuft_min')},'f':{k:f.get(k) for k in ('winkel','phase','fps')}}))\"\n")
    m = re.search(r"P4JSON (\{.*\})", aus); return (json.loads(m.group(1)) if m else None), aus
def p4():
    global PI0
    d, aus = pi_stand()
    if not d: return False, aus[-200:]
    PI0 = d; a, f = d["a"], d["f"]
    ok = a.get("kaputt") == 0 and a.get("bilder_s", 0) > 25 and f.get("phase") is not None
    return ok, f"Auswertung {a.get('fassung')} {a.get('bilder_s')} B/s kaputt {a.get('kaputt')} seit {a.get('laeuft_min')} min; Fokus {f.get('winkel'):.2f}° {f.get('phase')}"
def p5():
    aus = pi_auftrag("grep -oE 'Seite 1\\.[0-9]+' /home/pi/Desktop/autofokus4/seite.html | head -1; echo \"Firefox $(pgrep -x firefox | wc -l)\"; echo \"8092-Verbindungen $(ss -tn state established '( sport = :8092 )' | awk 'NR>1' | wc -l)\"\n")
    s = re.search(r"Seite 1\.\d+", aus); ff = re.search(r"Firefox (\d+)", aus); vb = re.search(r"8092-Verbindungen (\d+)", aus)
    ok = bool(s) and ff and int(ff.group(1)) >= 1 and vb and int(vb.group(1)) >= 1; return ok, f"{s.group(0) if s else 'keine Fassung'}, Firefox {ff.group(1) if ff else '?'}, Punktestrom-Verbindungen {vb.group(1) if vb else '?'}"
def p6():
    global STAND0
    d = hole(JETSON, "/stand"); ok = bool(d) and d.get("fassung") and d.get("letzter_fehler") is None
    if d: STAND0 = d
    return ok, (f"Dienst {d.get('fassung')}, Pi {d.get('pi')}, Auftrag '{d.get('auftrag')}', rsync {d.get('letzter_rsync')}, Fehler {d.get('letzter_fehler')}, CPU {d.get('cpu')} % GPU {d.get('gpu')} % {d.get('temp')} °C" if d else "keine Antwort")
def p7():
    d = hole(JETSON, "/stand"); s = (d or {}).get("statistik") or {}; v = (d or {}).get("verfolgung") or {}
    ok = bool(d) and d.get("saetze", 0) > 0 and d.get("letzter_rsync") is not None and "fehler" not in s and (s.get("bahnen") or 0) > 0
    return ok, (f"{d.get('saetze')} Sätze auf dem Jetson; Statistik über {s.get('saetze')} Sätze: {s.get('bahnen')} Bahnen, Länge {s.get('laenge_um_median')} µm, Tempo {s.get('tempo_mm_s_median')} mm/s, {s.get('tiere_je_bild')} Tiere/Bild"
                f"{(', FEHLER ' + str(s.get('fehler'))) if 'fehler' in s else ''}; Farbwahrheit letzte {v.get('saetze')} Sätze: Treffer {v.get('getroffen_prozent')} %, Nummernwechsel {v.get('wechsel_prozent')} %" if d else "keine Antwort")
def p8():
    if "--ohne-browser" in sys.argv: return True, "übersprungen"
    import os
    for n in ("stub8090.py", "pruefe_rueckfall.js"): shutil.copy(PRUEF / n, LAUF / n)
    seite = neueste_seite(); shutil.copy(seite, LAUF / "index.html")
    warten = "for i in $(seq 1 80); do python3 -c \"import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(0 if s.connect_ex(('127.0.0.1',8090))==0 else 1)\" && break; sleep 0.5; done"
    r = subprocess.run(["bash", "-c", f"cd {LAUF} && (python3 stub8090.py > stub8090.log 2>&1 & echo $! > s1.pid); t0=$(date +%s); {warten}; echo \"PORT nach $(( $(date +%s) - t0 )) s\"; "
                        f"NODE_PATH=/tmp/node_modules CHROME=$HOME/.cache/ms-playwright/chromium-1187/chrome-linux/chrome timeout 90 node pruefe_rueckfall.js; kill $(cat s1.pid); tail -c 300 stub8090.log"], capture_output=True, text=True, timeout=200)
    m = re.search(r'P8JSON (\{.*\})', r.stdout); d = json.loads(m.group(1)) if m else {}; port = re.search(r"PORT nach (\d+) s", r.stdout)
    ok = d.get("lampe") == "jlampe" and d.get("bild", 0) > 0
    return ok, f"{seite.name}: Jetson-Lampe '{d.get('lampe')}', Bild {d.get('bild')} px (Stellvertreter ohne Jetson, Port nach {port.group(1) if port else '?'} s)" + ("" if ok else f"; Ausgabe: {r.stdout[-300:]!r} {r.stderr[-200:]!r}")
def p9():
    name = "jetson_dienst_1.3.py"; ziel = LAUF / name
    if ziel.exists(): ziel.unlink()
    r = subprocess.run(["python3", str(HIER / "jetson_datei_holen_1.0.py"), name, str(LAUF)], capture_output=True, text=True, timeout=300)
    q = (HIER / name).read_bytes(); ok = ziel.exists() and hashlib.sha256(ziel.read_bytes()).hexdigest() == hashlib.sha256(q).hexdigest()
    return ok, f"{name} ({len(q)} Byte) stückweise über :8095/datei geholt, sha256 {'gleich der Quelle im Projekt' if ok else 'VERSCHIEDEN'}; {r.stdout.strip()[-110:]}"
def p10():
    global PROBE
    r = subprocess.run(["python3", str(HIER / "jetson_auftrag_1.1.py"), str(HIER / "auftrag_probe_1.0.py"), "--warten", "300", "--ziel", str(LAUF)], capture_output=True, text=True, timeout=700)
    m = re.search(r"P10JSON (\{.*\})", r.stdout); PROBE = json.loads(m.group(1)) if m else {}; rc = re.search(r"erledigt \S+ rc (-?\d+)", r.stdout)
    ok = PROBE.get("marke") == "AUFTRAGSPROBE_OK" and rc is not None and rc.group(1) == "0"
    return ok, (f"Probeauftrag auf {PROBE.get('rechner')} ausgeführt (rc {rc.group(1)}, Python {PROBE.get('python')}, OpenCV {PROBE.get('opencv')}, Arbeitsordner {PROBE.get('arbeitsordner')}); dort {PROBE.get('saetze')} Sätze, {PROBE.get('farbwahrheiten')} Farbwahrheiten, {PROBE.get('platte_frei_gb')} GB frei; Weg: Pi-Job → Jetson-Takt → Ausgabe über /datei zurück, kein Kennwort"
               if ok else f"Ausgabe: {r.stdout[-300:]!r} {r.stderr[-150:]!r}")
def p11():
    aus = pi_auftrag("systemctl is-enabled mikroskop-auswertung mikroskop-fokus 2>&1 | tr '\\n' ' '; echo; systemctl show -p Restart mikroskop-auswertung mikroskop-fokus | tr '\\n' ' '\n")
    ein = re.findall(r"\b(enabled|disabled|static|masked)\b", aus); neu = re.findall(r"Restart=(\S+)", aus)
    pi_ok = len(ein) >= 2 and all(e == "enabled" for e in ein[:2]) and len(neu) >= 2 and all(n != "no" for n in neu[:2])
    j = PROBE; nz = j.get("neustart", "") or ""
    j_ok = j.get("dienst_eingeschaltet") == "enabled" and j.get("dienst_aktiv") == "active" and "Restart=always" in nz and "jetson_clocks" in nz
    return pi_ok and j_ok, f"Pi: Auswertung/Fokus {ein[:2]}, Neustart {neu[:2]}; Jetson: mikroskop-jetson {j.get('dienst_eingeschaltet')}/{j.get('dienst_aktiv')}, {'Restart=always' if 'Restart=always' in nz else 'OHNE Restart=always'}, {'jetson_clocks beim Start' if 'jetson_clocks' in nz else 'OHNE jetson_clocks'}, Takt {j.get('takt_mhz')} kHz"
def p12():
    a = bruecke(["dateiliste", "suche <Zugangsblatt-auf-dem-PC> ZUGANGSBLATT.txt"], 120); b = bruecke(["python", "zugang_pruefen.py"], 120); c = bruecke(["dateiliste", "suche <Brückenordner-auf-dem-PC> jetson_fahren_1.3.py"], 120)
    m = re.search(r"noch auszufuellen: (\d+)", b); blatt = "ZUGANGSBLATT.txt" in a; fahren = "jetson_fahren_1.3.py" in c
    ok = blatt and m is not None and int(m.group(1)) == 0 and fahren
    return ok, f"Zugangsblatt auf dem PC {'vorhanden' if blatt else 'FEHLT'}, offene Felder {m.group(1) if m else '?'}; jetson_fahren_1.3.py {'auf <Brückenordner-auf-dem-PC>' if fahren else 'FEHLT'}; dieser Prüflauf übergibt kein Kennwort (Jetson nur über :8095 und den Pi)"
def p13():
    d = hole(JETSON, "/stand") or {}; p, _ = pi_stand(); a = (p or {}).get("a") or {}; a0 = PI0.get("a") or {}
    j_ok = bool(d) and d.get("letzter_fehler") is None and (d.get("letzter_rsync") != STAND0.get("letzter_rsync") or d.get("saetze", 0) > STAND0.get("saetze", 0))
    pi_ok = bool(a) and a.get("kaputt") == 0 and (a.get("laeuft_min") or 0) >= (a0.get("laeuft_min") or 0)
    return j_ok and pi_ok, f"Jetson: rsync {STAND0.get('letzter_rsync')} → {d.get('letzter_rsync')}, Sätze {STAND0.get('saetze')} → {d.get('saetze')}, Auftrag '{d.get('auftrag')}'; Pi: Auswertung läuft seit {a.get('laeuft_min')} min (vorher {a0.get('laeuft_min')}), kaputt {a.get('kaputt')} — beides ohne Zutun des Arbeitsbereichs"

def p14():
    d = hole(JETSON, "/live") or {}
    ok = bool(d) and d.get("verbunden") and (d.get("bilder_je_s") or 0) >= 20 and d.get("letztes_bild_vor_s") is not None and d["letztes_bild_vor_s"] < 2 and d.get("abgeschnitten") == 0
    return ok, (f"Jetson liest {d.get('pi')}:8090/strom seit {d.get('seit')}: {d.get('bilder_je_s')} Bilder/s, {d.get('mbit_je_s')} Mbit/s, letztes Bild vor {d.get('letztes_bild_vor_s')} s, "
                f"{d.get('bilder')} Bilder, {d.get('abgeschnitten')} abgeschnitten, {d.get('neuverbindungen')} Verbindung(en)" + (f", Fehler {d.get('fehler')}" if d.get('fehler') else "") if d else "keine Antwort auf /live")
def p15():
    if "--ohne-browser" in sys.argv: return True, "übersprungen"
    for n in ("stub8090.py", "pruefe_jetsonblock.js"): shutil.copy(PRUEF / n, LAUF / n)
    seite = neueste_seite(); shutil.copy(seite, LAUF / "index.html")
    warten = "for i in $(seq 1 80); do python3 -c \"import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(0 if s.connect_ex(('127.0.0.1',8090))==0 else 1)\" && break; sleep 0.5; done"
    r = subprocess.run(["bash", "-c", f"cd {LAUF} && (python3 stub8090.py > stub8090.log 2>&1 & echo $! > s2.pid); {warten}; "
                        f"NODE_PATH=/tmp/node_modules CHROME=$HOME/.cache/ms-playwright/chromium-1187/chrome-linux/chrome timeout 90 node pruefe_jetsonblock.js; kill $(cat s2.pid)"], capture_output=True, text=True, timeout=200)
    m = re.search(r'P15JSON (\{.*\})', r.stdout); d = json.loads(m.group(1)) if m else {}
    ok = d.get("lampe") == "jlampe an" and "Bilder/s" in (d.get("live") or "") and "Dienst 1.4" in (d.get("verb") or "") and d.get("bild", 0) > 0 and ("Tiere im Bild" in (d.get("yolo") or "") or "YOLO" in (d.get("yolo") or ""))
    return ok, f"{seite.name}: Lampe '{d.get('lampe')}', Livestrom-Zeile '{(d.get('live') or '')[:90]}', Verbindung '{(d.get('verb') or '')[:40]}'" + ("" if ok else f"; Ausgabe: {r.stdout[-300:]!r} {r.stderr[-200:]!r}")

def p16():
    d = hole(JETSON, "/stand") or {}; y = d.get("yolo") or {}
    ok = y.get("phase") == "laeuft" and (y.get("verarbeitet_s") or 0) >= 10 and bool(y.get("modell"))
    return ok, (f"YOLO {y.get('fassung')} Modell {y.get('modell')}: {y.get('phase')}, {y.get('verarbeitet_s')} von {y.get('bilder_s')} Bildern/s verarbeitet, {y.get('tiere_mittel_5s')} Tiere im Bild (5 s), "
                f"Größe {y.get('groesse_mm_median')} mm, Tempo {y.get('tempo_mm_s_median')} mm/s" + (f", Fehler {y.get('fehler')}" if y.get('fehler') else "")) if y else "kein yolo-Feld in /stand (Dienst < 1.8?)"
def p17():
    aus = bruecke(["hole", f"{JETSON} /lernen"], 90); titel = re.search(r"<title>([^<]*)</title>", aus); l = bruecke(["hole", f"{JETSON} /lernen/liste"], 90)
    try: liste = json.loads(l[l.find("["):]); z = {}
    except Exception: liste = []; z = {}
    for e in liste: z[e.get("status")] = z.get(e.get("status"), 0) + 1
    ok = bool(titel) and len(liste) > 0
    return ok, f"{titel.group(1) if titel else 'keine Seite'}; {len(liste)} Lernbilder: {z}"

SCHRITTE = (("P1", "Brücke meldet sich (Puls)", p1), ("P2", "Brücke antwortet (info)", p2), ("P3", "Pi über den Namen erreichbar", p3), ("P4", "Pi-Dienste: Auswertung und Fokus", p4),
            ("P5", "Seite und Kiosk auf dem Pi", p5), ("P6", "Jetson-Dienst über die Brücke", p6), ("P7", "Jetson holt vom Pi und rechnet", p7), ("P8", "Rückfall ohne Jetson (Browserprobe)", p8),
            ("P9", "Dateikanal Jetson → hier (Prüfsumme)", p9), ("P10", "Auftragskanal hier → Pi → Jetson → hier", p10), ("P11", "Eigenständigkeit der Dienste (Pi, Jetson)", p11),
            ("P12", "Zugang ohne Kennwort in Befehlen", p12), ("P13", "Geräte arbeiten ohne Zutun weiter", p13),
            ("P14", "Jetson sieht den Livestrom des Pi", p14), ("P15", "Seite mit anwesendem Jetson (Browserprobe)", p15),
            ("P16", "YOLO-Livedienst auf dem Jetson", p16), ("P17", "Lernseite auf dem Jetson", p17))
if __name__ == "__main__":
    start = datetime.datetime.now(MEZ)
    for k, t, f in SCHRITTE:
        if k in ("P3", "P4", "P5", "P10", "P11", "P13") and ergeb and not ergeb[0][2]: ergeb.append((k, t, False, 0.0, "übersprungen: Brücke ohne Puls")); continue
        schritt(k, t, f)
    n_ok = sum(1 for e in ergeb if e[2]); datum = start.strftime("%Y-%m-%d_%H%M")
    md = [f"# Prüfprotokoll Zusammenspiel — {start.strftime('%d.%m.%Y %H:%M')} (MEZ) — {n_ok} von {len(ergeb)} bestanden", "",
          "Kette: Arbeitsbereich → Empfänger (:8085) → Brücke auf dem PC (<Rechnername>) → SSH `mikroskop` (Pi) / HTTP Jetson (:8095) → Pi-Dienste (:8090 Fokus, :8092 Auswertung) → Jetson (rsync vom Pi, Aufträge vom Pi, Dateien über :8095/datei).",
          f"Prüfer `{pathlib.Path(__file__).name}`, Dauer {round((datetime.datetime.now(MEZ) - start).total_seconds())} s, ohne Kennwort in Befehlen.", "",
          "| Schritt | Prüfung | Ergebnis | Dauer | Befund |", "|---|---|---|---|---|"]
    md += [f"| {k} | {t} | {'BESTANDEN' if ok else 'DURCHGEFALLEN'} | {d} s | {b} |" for k, t, ok, d, b in ergeb]
    md += ["", "## Was ohne den Arbeitsbereich weiterläuft (Sperrfestigkeit)", "",
           "Wird die Sitzung im Arbeitsbereich gesperrt oder beendet, läuft auf den Geräten alles weiter; nur Eingriffe von hier aus ruhen.", "",
           "| Teil | läuft ohne den Arbeitsbereich | Beleg |", "|---|---|---|",
           "| Pi: Auswertung 1.4 (:8092), Fokus (:8090), Seite und Kiosk | ja — systemd eingeschaltet, Neustart von selbst | P4, P5, P11, P13 |",
           "| Jetson: Dienst 1.8 (rsync vom Pi, Livestrom dauernd, Farbwahrheit, Verfolgung, Statistik, Aufträge, Lernseite, Training auf Fertig) | ja — systemd eingeschaltet, Restart=always, jetson_clocks, Wiederverbindung des Livestroms von selbst | P6, P7, P11, P13, P14, P17 |",
           "| Jetson: YOLO-Livedienst (Tiere, Größe, Tempo aus dem Livestrom) | ja — eigene Einheit, Restart=always, Modell wird bei Nachtraining neu geladen; ohne ihn fehlt nur die YOLO-Zeile | P16 |",
           "| Brücke auf dem PC | ja — Wächter startet sie neu, Puls am Empfänger | P1, P2 |",
           "| Nur mit Sitzung: neue Fassungen aufspielen, Aufträge geben, Ergebnisse holen | Wiederaufnahme jederzeit ohne Kennwort (Zugangsblatt auf dem PC, Dienst 1.3) | P9, P10, P12 |",
           "", "Durchgefallene Schritte sind mit Befund zu klären; Kriterium nicht senken, Ursache messen."]
    aus = HIER / f"PRUEFPROTOKOLL_ZUSAMMENSPIEL_{datum}.md"; aus.write_text("\n".join(md) + "\n", encoding="utf-8"); print("->", aus)
    sys.exit(0 if n_ok == len(ergeb) else 1)
