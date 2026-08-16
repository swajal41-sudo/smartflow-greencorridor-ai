#!/usr/bin/env python3
"""
Zero-dependency HTTP Server & Live REST API for SmartFlow GreenCorridor AI & Nagpur Traffic OS.
Serves frontend web client and handles multi-intersection simulation, emergency preemption,
CCTV edge vision analytics, risk heatmap, police deployment optimization, citizen grievance,
end-to-end connected workflow demo, and testing suite.
"""

import json
import os
import sys
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.city_grid import NagpurCityGrid
from src.preemption_engine import PreemptionEngine
from src.risk_heatmap import RiskHeatmapEngine
from src.police_optimizer import PoliceOptimizer
from src.grievance_engine import GrievanceEngine
from src.vision_sim import CCTVVisionSimulator

city_grid = NagpurCityGrid()
preemption_engine = PreemptionEngine(city_grid)
risk_engine = RiskHeatmapEngine()
police_optimizer = PoliceOptimizer(risk_engine)
grievance_engine = GrievanceEngine()
vision_simulator = CCTVVisionSimulator()

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
        query = parse_qs(parsed.query)

        if path in ["/api/status", "/api/grid/status", "/simulate/status"]:
            state = city_grid.state()
            self._send_json(state)

        elif path == "/api/risk/heatmap":
            self._send_json(risk_engine.get_full_heatmap())

        elif path == "/api/police/optimize":
            self._send_json(police_optimizer.optimize())

        elif path == "/api/grievance/list":
            self._send_json(grievance_engine.list_tickets())

        elif path == "/api/vision/status":
            cam_id = query.get("cam_id", ["CAM_02"])[0]
            self._send_json(vision_simulator.get_camera_feed_state(cam_id))

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

        # --- Risk Heatmap APIs ---
        elif path == "/api/risk/incident":
            scenario = payload.get("scenario", "")
            self._send_json(risk_engine.trigger_incident(scenario))

        elif path == "/api/risk/clear_incident":
            jid = payload.get("junction_id", "")
            self._send_json(risk_engine.clear_incident(jid))

        elif path == "/api/risk/weather":
            severity = float(payload.get("severity", 0.0))
            self._send_json(risk_engine.set_weather(severity))

        # --- Police Optimizer APIs ---
        elif path == "/api/police/set_officers":
            count = int(payload.get("count", 16))
            self._send_json(police_optimizer.set_officers(count))

        # --- Citizen Grievance APIs ---
        elif path == "/api/grievance/submit":
            result = grievance_engine.submit_complaint(
                complaint_type=payload.get("complaint_type", "traffic_jam"),
                location=payload.get("location", ""),
                description=payload.get("description", ""),
                citizen_name=payload.get("citizen_name", "Anonymous"),
                severity=payload.get("severity", None)
            )
            self._send_json(result)

        elif path == "/api/grievance/track":
            tid = payload.get("ticket_id", "")
            self._send_json(grievance_engine.get_ticket(tid))

        elif path == "/api/grievance/advance":
            tid = payload.get("ticket_id", "")
            self._send_json(grievance_engine.advance_ticket(tid))

        # --- The Magic Connection: End-to-End Coordinated Storyline Demo ---
        elif path == "/api/workflow/e2e_demo":
            # 1. Citizen reports major trauma collision at Medical Square
            grv_res = grievance_engine.submit_complaint(
                complaint_type="road_accident",
                location="Medical Square (Opposite Government Hospital)",
                description="Mass casualty collision: Private bus struck auto-rickshaw. Severe injuries. Immediate ambulance and police diversion needed.",
                citizen_name="Dr. Alok Verma (Witness)",
                severity="critical"
            )
            ticket_id = grv_res["ticket"]["ticket_id"]
            grievance_engine.advance_ticket(ticket_id) # Advance to Triage Review

            # 2. Risk Heatmap spikes Medical Square to Critical
            inc_res = risk_engine.trigger_incident("road_accident")

            # 3. Police Optimizer reallocates officers to Medical Sq
            pol_res = police_optimizer.optimize()

            # 4. Dispatch Code Red Ambulance with Green Wave Corridor to AIIMS Hospital
            ev = city_grid.dispatch_emergency(
                vehicle_type="ambulance",
                origin="Sitabuldi Junction",
                destination="AIIMS / GMC Hospital Gate",
                priority=1
            )

            # Advance ticket to unit dispatched
            grievance_engine.advance_ticket(ticket_id)

            self._send_json({
                "status": "E2E_WORKFLOW_ACTIVE",
                "storyline": {
                    "step_1_citizen": f"Citizen grievance {ticket_id} filed with photo evidence.",
                    "step_2_risk_surge": "Medical Square risk scored 95/100 (CRITICAL).",
                    "step_3_police_dispatch": "Police Optimizer redeployed 3 officers to Medical Square.",
                    "step_4_green_wave": f"Preemption interlock activated: Code Red Cardiac Ambulance ({ev.ev_id}) en route to AIIMS Trauma Bay.",
                },
                "ticket": grievance_engine.get_ticket(ticket_id)["ticket"],
                "heatmap": risk_engine.get_full_heatmap(),
                "police_deployment": pol_res,
                "emergency_vehicle": ev.to_dict(),
                "grid_state": city_grid.state()
            })

        else:
            self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        """Suppress noisy request logs."""
        pass

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def run(port=8080):
    server_address = ("", port)
    try:
        httpd = ReusableHTTPServer(server_address, TrafficRequestHandler)
    except OSError as e:
        if e.errno == 98:
            print(f"\n❌ Port {port} is already in use by another process.")
            print(f"👉 Run this command to free port {port}:")
            print(f"   fuser -k {port}/tcp\n")
            print(f"👉 Or start on an alternate port:")
            print(f"   python3 server.py {port + 1}\n")
            sys.exit(1)
        else:
            raise e

    print(f"\n  ╔══════════════════════════════════════════════════════════════╗")
    print(f"  ║  SmartFlow I²TMS — Nagpur Unified Command OS               ║")
    print(f"  ║  Live on http://localhost:{port:<32}║")
    print(f"  ║  MANTHAN 4 YUVA — Vikasit Nagpur 2026                     ║")
    print(f"  ╚══════════════════════════════════════════════════════════════╝\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(port)

