# Stellvertreter des Fokusdienstes (:8090) fuer die Seitenpruefung: Seite, /status, /strom (MJPEG aus Probebildern), /bild.jpg
import http.server, socketserver, json, time, sys, pathlib, threading
import numpy as np, cv2
HIER = pathlib.Path(__file__).parent
rng = np.random.default_rng(1)
def bild(k):
    im = np.full((480, 640, 3), 150, np.uint8); im = (im.astype(float) + rng.normal(0, 3, im.shape)).clip(0, 255).astype(np.uint8)
    cv2.putText(im, "DIV=0", (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (20, 20, 20), 5)
    x = 100 + (k * 9) % 440; cv2.ellipse(im, (x, 240), (19, 9), 0, 0, 360, (70, 60, 50), -1)
    return cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()
BILDER = [bild(k) for k in range(120)]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html", "/seite.html"):
            b = (HIER / "index.html").read_bytes(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif p == "/status":
            b = json.dumps({"winkel": 150.29, "schaerfe": 9300.0, "phase": "fertig", "max": 10253.5, "max_winkel": 155.29, "lauf": False, "fps": 28.8, "meldungen": [], "haltung": "an"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif p == "/bild.jpg":
            b = BILDER[int(time.time() * 28) % len(BILDER)]; self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif p == "/strom":
            self.send_response(200); self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=bild"); self.end_headers(); k = 0
            try:
                while True:
                    b = BILDER[k % len(BILDER)]; k += 1
                    self.wfile.write(b"--bild\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(b)).encode() + b"\r\n\r\n" + b + b"\r\n"); self.wfile.flush(); time.sleep(1 / 28.8)
            except (BrokenPipeError, ConnectionResetError, OSError): pass
        else:
            self.send_response(404); self.end_headers()
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
if __name__ == "__main__":
    S(("127.0.0.1", 8090), H).serve_forever()
