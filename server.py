#!/usr/bin/env python3
"""
Zero-dependency HTTP Server & Live REST API for SmartFlow GreenCorridor AI.
Serves frontend web client and handles multi-intersection simulation, emergency preemption, and testing suite.
"""

import json
import os
import sys
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.city_grid import NagpurCityGrid
from src.preemption_engine import PreemptionEngine

city_grid = NagpurCityGrid()
preemption_engine = PreemptionEngine(city_grid)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class TrafficRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _serve_file(self, filepath):
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            self.send_error(404, "File Not Found")
            return
        
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        with open(filepath, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ["/api/status", "/api/grid/status", "/simulate/status"]:
            state = city_grid.state()
            self._send_json(state)
        else:
            relative_path = path.lstrip("/")
            if not relative_path:
                relative_path = "index.html"
            target_path = os.path.join(STATIC_DIR, relative_path)
            self._serve_file(target_path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path in ["/api/simulate/step", "/api/grid/step"]:
            dt = float(payload.get("dt", 1.0))
            state = city_grid.step(dt)
            self._send_json(state)

        elif path in ["/api/corridor/dispatch", "/api/dispatch"]:
            vehicle_type = payload.get("vehicle_type", "ambulance")
            origin = payload.get("origin", "Sitabuldi Junction")
            destination = payload.get("destination", "AIIMS / GMC Hospital Gate")
            priority = int(payload.get("priority", 1))

            ev = city_grid.dispatch_emergency(vehicle_type, origin, destination, priority)
            self._send_json({
                "status": "DISPATCHED",
                "emergency_vehicle": ev.to_dict(),
                "grid_state": city_grid.state()
            })

        elif path in ["/api/corridor/test_suite", "/api/test_suite"]:
            test_results = preemption_engine.run_automated_test_suite()
            self._send_json(test_results)

        elif path in ["/api/simulate/reset", "/api/grid/reset"]:
            city_grid.reset()
            self._send_json({"status": "RESET", "grid_state": city_grid.state()})

        elif path in ["/api/simulate/set_surge", "/api/grid/set_surge"]:
            rate = float(payload.get("surge_rate", 0.3))
            city_grid.surge_rate = max(0.1, min(2.0, rate))
            self._send_json({"status": "UPDATED", "surge_rate": city_grid.surge_rate})

        else:
            self.send_error(404, "Endpoint Not Found")

def run(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, TrafficRequestHandler)
    print(f"SmartFlow GreenCorridor AI Server live on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(port)
