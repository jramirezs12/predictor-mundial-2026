"""Servidor web del predictor del Mundial 2026.

Usa solo la librería estándar (http.server). Sirve el dashboard estático de
web/ y expone una API JSON con todas las predicciones y estadísticas.

Ejecutar:  python server.py    ->  abre http://localhost:8000
"""

from __future__ import annotations

import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import api

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
# En local usa 8000; en un host (Render, Railway, etc.) toma el puerto asignado.
PORT = int(os.environ.get("PORT", "8000"))
# Detecta si está desplegado (para no intentar abrir el navegador del servidor).
IS_HOSTED = bool(os.environ.get("PORT") or os.environ.get("RENDER"))

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silencioso salvo errores
        pass

    def end_headers(self):
        # Evita conexiones persistentes que confunden a algunos clientes.
        self.send_header("Connection", "close")
        self.close_connection = True
        super().end_headers()

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path):
        ext = os.path.splitext(path)[1]
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path.startswith("/api/"):
            return self._handle_api(path, qs)

        # Archivos estáticos.
        if path == "/":
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("\\/")
        full = os.path.join(WEB_DIR, safe)
        if os.path.isfile(full):
            return self._file(full)
        self.send_error(404)

    def _handle_api(self, path, qs):
        try:
            if path == "/api/teams":
                return self._json(api.list_teams())
            if path == "/api/groups":
                return self._json(api.list_groups())
            if path == "/api/stadiums":
                return self._json(api.list_stadiums())
            if path == "/api/schedule":
                return self._json(api.list_schedule())
            if path == "/api/group-stage":
                return self._json(api.group_stage_predictions())
            if path == "/api/match":
                home = qs.get("home", [""])[0]
                away = qs.get("away", [""])[0]
                stage = qs.get("stage", ["group"])[0]
                res = api.predict(home, away, stage)
                if res is None:
                    return self._json({"error": "equipo no encontrado"}, 404)
                return self._json(res)
            if path == "/api/markets":
                home = qs.get("home", [""])[0]
                away = qs.get("away", [""])[0]
                stage = qs.get("stage", ["group"])[0]
                res = api.match_markets(home, away, stage)
                if res is None:
                    return self._json({"error": "equipo no encontrado"}, 404)
                return self._json(res)
            if path == "/api/simulate":
                n = int(qs.get("n", ["10000"])[0])
                n = max(100, min(n, 100000))
                return self._json(api.simulate(n))
            if path == "/api/live/status":
                return self._json(api.live_status())
            if path == "/api/live/refresh":
                return self._json(api.refresh_live())
            if path == "/api/live/standings":
                return self._json(api.live_standings())
            if path == "/api/live/results":
                return self._json(api.live_results())
            if path == "/api/value/scan":
                km = float(qs.get("kelly", ["0.25"])[0])
                return self._json(api.value_scan(km))
            if path == "/api/recommendations":
                top = int(qs.get("top", ["12"])[0])
                return self._json(api.recommendations(top))
            return self._json({"error": "endpoint desconocido"}, 404)
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            payload = json.loads(body.decode("utf-8") or "{}")
        except Exception:  # noqa: BLE001
            return self._json({"error": "JSON inválido"}, 400)
        try:
            if path == "/api/value":
                bets = payload.get("bets", [])
                km = float(payload.get("kelly_multiplier", 0.25))
                return self._json({"analysis": api.analyze_value(bets, km)})
            if path == "/api/portfolio-sim":
                bets = payload.get("bets", [])
                start = float(payload.get("start", 50000))
                target = float(payload.get("target", 4000000))
                km = float(payload.get("kelly_multiplier", 0.25))
                n = max(500, min(int(payload.get("n", 10000)), 100000))
                if not bets:
                    return self._json({"error": "sin apuestas"}, 400)
                return self._json(api.simulate_portfolio(bets, start, target, km, n))
            return self._json({"error": "endpoint desconocido"}, 404)
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 500)


def _background_refresher(stop_event):
    """Actualiza resultados/cuotas en segundo plano cada AUTO_REFRESH_SECONDS."""
    import config
    while not stop_event.is_set():
        try:
            s = api.refresh_live()
            print(f"  [live] actualizado: {s.get('played', 0)} jugados, "
                  f"{s.get('with_odds', 0)} con cuotas "
                  f"({s.get('source_results')} / {s.get('source_odds')})")
        except Exception as e:  # noqa: BLE001
            print(f"  [live] error al actualizar: {e}")
        stop_event.wait(config.AUTO_REFRESH_SECONDS)


def main():
    import threading
    print(f"\n  Predictor Mundial 2026  ->  http://localhost:{PORT}\n")
    print("  Endpoints: /api/teams /api/match /api/simulate /api/recommendations")
    print("             /api/value/scan /api/live/status /api/live/standings\n")
    print("  Obteniendo datos en vivo del torneo (primera vez puede tardar)...")
    print("  Ctrl+C para detener.\n")

    stop_event = threading.Event()
    t = threading.Thread(target=_background_refresher, args=(stop_event,), daemon=True)
    t.start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    if not IS_HOSTED:
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
        stop_event.set()
        server.shutdown()


if __name__ == "__main__":
    main()
