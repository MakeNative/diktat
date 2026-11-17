"""Diktat: im Browser aufnehmen, lokal mit Whisper transkribieren, Text kopieren.

`diktat` startet den Server im Vordergrund und öffnet http://127.0.0.1:8765.
`diktat --detach` startet ihn im Hintergrund (so ruft ihn die App auf).
Läuft schon einer, öffnen beide nur den Browser.
"""
import hashlib
import json
import os
import ssl
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import certifi
import numpy as np

HOST, PORT = "127.0.0.1", int(os.environ.get("DIKTAT_PORT", "8765"))
MODEL_NAME = os.environ.get("DIKTAT_MODEL", "large-v3-turbo")
IDLE_MINUTES = float(os.environ.get("DIKTAT_IDLE_MINUTES", "60"))
URL = f"http://{HOST}:{PORT}"
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
ALLOWED_ORIGINS = {f"http://{h}" for h in ALLOWED_HOSTS}
SAMPLE_RATE = 16000
MAX_AUDIO_BYTES = SAMPLE_RATE * 4 * 60 * 30  # 30 Minuten float32 mono
# Gleicher Ort wie Whisper selbst, damit ein schon geladenes Modell weiterverwendet wird.
MODEL_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "whisper"
LOG = Path.home() / "Library" / "Logs" / "Diktat.log"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

state = {"phase": "loading", "message": "Starte …", "progress": None}
model = None
lock = threading.Lock()
last_used = time.time()


def download_model(whisper):
    """Lädt das Modell selbst herunter, damit die Seite den Fortschritt zeigen kann."""
    url = whisper._MODELS.get(MODEL_NAME)
    if not url:
        return  # eigener Pfad oder unbekannter Name, das klärt load_model
    target = MODEL_DIR / os.path.basename(url)
    if target.exists():
        return  # load_model prüft die Prüfsumme
    expected = url.split("/")[-2]
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    sha = hashlib.sha256()
    with urllib.request.urlopen(url, context=SSL_CONTEXT) as resp, open(part, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        size = f"{total / 1e9:.1f}".replace(".", ",")
        done = 0
        while chunk := resp.read(1 << 20):
            out.write(chunk)
            sha.update(chunk)
            done += len(chunk)
            state.update(
                phase="download",
                message=f"Lade Sprachmodell herunter (einmalig, {size} GB) …",
                progress=done / total if total else None,
            )
    if sha.hexdigest() != expected:
        part.unlink()
        raise RuntimeError("Download unvollständig, bitte Diktat neu starten.")
    part.replace(target)


def load():
    global model
    try:
        state.update(message="Lade Sprachmodell …")
        import whisper  # dauert ein paar Sekunden, deshalb erst hier

        download_model(whisper)
        state.update(phase="loading", message="Lade Sprachmodell …", progress=None)
        model = whisper.load_model(MODEL_NAME, device="cpu", download_root=str(MODEL_DIR))
        state.update(phase="ready", message="Bereit.", progress=None)
        print(f"Modell {MODEL_NAME} geladen.", flush=True)
    except Exception as e:
        state.update(phase="error", message=f"Sprachmodell konnte nicht geladen werden: {e}", progress=None)
        print(state["message"], flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, data):
        self._send(status, json.dumps(data).encode(), "application/json")

    def _trusted(self):
        # Host gegen DNS-Rebinding, Origin gegen fremde Seiten im selben Browser.
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in ALLOWED_HOSTS and (origin is None or origin in ALLOWED_ORIGINS)

    def do_GET(self):
        global last_used
        if not self._trusted():
            return self._send(403, b"forbidden", "text/plain")
        last_used = time.time()
        if self.path in ("/", "/index.html"):
            self._send(200, files("diktat").joinpath("index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/status":
            self._json(200, state)
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        global last_used
        if not self._trusted():
            return self._send(403, b"forbidden", "text/plain")
        last_used = time.time()
        url = urlparse(self.path)
        if url.path == "/quit":
            self._json(200, {"ok": True})
            threading.Thread(target=self.server.shutdown).start()
            return
        if url.path != "/transcribe":
            return self._send(404, b"not found", "text/plain")
        if model is None:
            return self._json(503, {"error": state["message"]})
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_AUDIO_BYTES:
            return self._json(413, {"error": "Aufnahme zu lang (höchstens 30 Minuten)."})
        language = parse_qs(url.query).get("lang", ["de"])[0] or None
        # Der Browser schickt das Audio schon dekodiert: 16 kHz, mono, float32.
        audio = np.frombuffer(self.rfile.read(length), dtype=np.float32)
        try:
            start = time.time()
            with lock:
                result = model.transcribe(audio, language=language, fp16=False)
            text = result["text"].strip()
            print(f"Transkribiert in {time.time() - start:.1f}s: {text[:80]}", flush=True)
            self._json(200, {"text": text, "seconds": round(time.time() - start, 1)})
        except Exception as e:
            self._json(500, {"error": str(e)})


def watch_idle(server):
    while time.time() - last_used < IDLE_MINUTES * 60:
        time.sleep(30)
    print(f"{IDLE_MINUTES:g} Minuten ohne Nutzung, beende Diktat.", flush=True)
    server.shutdown()


def running():
    try:
        with urllib.request.urlopen(f"{URL}/status", timeout=1):
            return True
    except Exception:
        return False


def serve(open_browser):
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        sys.exit(f"Port {PORT} ist belegt. Anderen Port wählen mit DIKTAT_PORT=8766 diktat")
    threading.Thread(target=load, daemon=True).start()
    threading.Thread(target=watch_idle, args=(server,), daemon=True).start()
    print(f"Diktat läuft auf {URL}  (Beenden: Ctrl+C)", flush=True)
    if open_browser:
        webbrowser.open(URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def detach():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as log:
        subprocess.Popen(
            [sys.executable, "-m", "diktat", "--no-browser"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
        )
    for _ in range(100):
        if running():
            break
        time.sleep(0.2)
    webbrowser.open(URL)


def main():
    if running():
        print(f"Diktat läuft schon auf {URL}", flush=True)
        webbrowser.open(URL)
    elif "--detach" in sys.argv:
        detach()
    else:
        serve(open_browser="--no-browser" not in sys.argv)


if __name__ == "__main__":
    main()
