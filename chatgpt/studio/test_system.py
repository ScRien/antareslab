# -*- coding: utf-8 -*-
"""
test_system.py - Donanım olmadan pipeline testi
- Yerel bir mock ESP32 server ayağa kalkar:
  - / -> 200 OK
  - /360_list -> {"12345": N}
  - /360_12345_i.jpg -> sentetik JPG
- AntaresStudio içindeki Esp32Client ile indirir
- ReconstructionWorker'ın core fonksiyonları GUI olmadan çağrılabilir değil; burada sadece download+dosya varlığını test ediyoruz.
İstersen bunu pytest'e çevirebilirsin.
"""
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import numpy as np
import cv2

PORT = 8089
SESSION = "12345"
N = 12

def make_img(i: int):
    img = np.full((480, 640, 3), 255, np.uint8)
    cv2.putText(img, f"IMG {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 4)
    # basit pattern
    cv2.circle(img, (320,240), 60+i, (50,100,200), 6)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return buf.tobytes()

IMGS = [make_img(i) for i in range(N)]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if self.path == "/360_list":
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({SESSION: N}).encode("utf-8"))
            return
        if self.path.startswith(f"/360_{SESSION}_") and self.path.endswith(".jpg"):
            try:
                idx = int(self.path.split("_")[-1].split(".")[0])
            except Exception:
                self.send_response(404); self.end_headers(); return
            if 0 <= idx < N:
                data = IMGS[idx]
                self.send_response(200)
                self.send_header("Content-Type","image/jpeg")
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_response(404); self.end_headers(); return
        self.send_response(404); self.end_headers()

def run_server():
    httpd = HTTPServer(("127.0.0.1", PORT), Handler)
    httpd.serve_forever()

def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.2)

    # import client from main file
    from antares_studio_final import Esp32Client  # dosya adını aynı klasörde tut

    ip = f"127.0.0.1:{PORT}"
    c = Esp32Client(ip)
    c.ping()
    scans = c.get_scan_list()
    assert SESSION in scans and scans[SESSION] == N

    out = os.path.join(os.getcwd(), "tmp_test_download")
    files = c.download_scan(SESSION, N, out, progress=lambda p: None, log=lambda s: None, concurrency=3)
    assert len(files) == N
    assert all(os.path.exists(f) for f in files)

    print("✅ TEST OK - download pipeline çalışıyor.")
    print("Klasör:", out)

if __name__ == "__main__":
    main()
