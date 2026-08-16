"""
Citizen Grievance & Traffic Issue Reporting Engine.
Manages ticket lifecycle: Submit → Triage → Dispatch → Resolution → Closed.
Supports complaint categories, evidence metadata, severity classification, and authority triage.
"""

import time
import random

COMPLAINT_TYPES = {
    "traffic_jam": {"label": "Traffic Jam / Gridlock", "icon": "🚗", "default_severity": "medium"},
    "road_accident": {"label": "Road Accident", "icon": "💥", "default_severity": "critical"},
    "rash_driving": {"label": "Rash / Dangerous Driving", "icon": "⚠️", "default_severity": "high"},
    "illegal_parking": {"label": "Illegal Parking", "icon": "🅿️", "default_severity": "low"},
    "road_hazard": {"label": "Road Hazard / Pothole", "icon": "🕳️", "default_severity": "medium"},
    "signal_malfunction": {"label": "Signal Malfunction", "icon": "🚦", "default_severity": "high"},
    "waterlogging": {"label": "Waterlogging / Flooding", "icon": "🌊", "default_severity": "high"},
    "noise_pollution": {"label": "Noise / Horn Violation", "icon": "📢", "default_severity": "low"},
}

STATUS_FLOW = ["received", "triage_review", "unit_dispatched", "on_scene", "resolved", "closed"]

SAMPLE_LOCATIONS = [
    "Sitabuldi Square, near Metro Station",
    "Medical Square, opposite Government Hospital",
    "Cotton Market Road, Lane 3",
    "Wardha Road Underpass, KM 1.2",
    "Sadar, near Variety Square",
    "Itwari Station Road, Gate 2",
    "Shankar Nagar Square",
    "Automotive Square Flyover",
    "Zero Mile Chowk",
    "Hingna T-Point, Industrial Area",
    "Pardi Naka Flyover, Eastbound",
    "Trimurti Nagar Main Road"
]


class GrievanceEngine:
    def __init__(self):
        self.tickets = {}
        self._counter = 0
        self._seed_demo_tickets()

    def _seed_demo_tickets(self):
        """Create a few demo tickets so the dashboard isn't empty on first load."""
        demos = [
            {"type": "road_accident", "location": "Medical Square, opposite Government Hospital",
             "description": "Two-wheeler collision with auto-rickshaw. Minor injuries. Traffic backed up 200m.",
             "severity": "critical"},
            {"type": "illegal_parking", "location": "Sadar, near Variety Square",
             "description": "Multiple cars double-parked blocking bus lane for 2+ hours.",
             "severity": "low"},
            {"type": "traffic_jam", "location": "Sitabuldi Square, near Metro Station",
             "description": "Severe gridlock during evening rush hour. Signal timing inadequate.",
             "severity": "medium"},
        ]
        for i, d in enumerate(demos):
            self._counter += 1
            tid = f"NAG-GRV-2026-{self._counter:04d}"
            status_idx = min(i + 1, len(STATUS_FLOW) - 1)
            self.tickets[tid] = {
                "ticket_id": tid,
                "complaint_type": d["type"],
                "complaint_label": COMPLAINT_TYPES[d["type"]]["label"],
                "complaint_icon": COMPLAINT_TYPES[d["type"]]["icon"],
                "location": d["location"],
                "description": d["description"],
                "severity": d["severity"],
                "status": STATUS_FLOW[status_idx],
                "status_index": status_idx,
                "submitted_at": time.time() - random.randint(600, 7200),
                "citizen_name": random.choice(["Rahul M.", "Priya S.", "Amit K."]),
                "evidence_count": random.randint(0, 3),
                "assigned_unit": f"PCR-{random.randint(101, 199)}" if status_idx >= 2 else None,
                "timeline": self._build_timeline(status_idx)
            }

    def _build_timeline(self, up_to_index: int) -> list:
        labels = [
            "Complaint Received",
            "Under Triage Review",
            "Police Unit Dispatched",
            "Officer On-Scene",
            "Issue Resolved",
            "Ticket Closed"
        ]
        timeline = []
        base = time.time() - 3600
        for i, label in enumerate(labels):
            if i < up_to_index:
                status = "completed"
                ts = base + i * 420
            elif i == up_to_index:
                status = "completed" if up_to_index == len(labels) - 1 else "in_progress"
                ts = base + i * 420
            else:
                status = "pending"
                ts = None
            timeline.append({
                "step": label,
                "status": status,
                "timestamp": ts
            })
        return timeline

    def submit_complaint(self, complaint_type: str, location: str,
                         description: str, citizen_name: str = "Anonymous",
                         severity: str = None) -> dict:
        """Submit a new citizen grievance."""
        if complaint_type not in COMPLAINT_TYPES:
            complaint_type = "traffic_jam"

        ct = COMPLAINT_TYPES[complaint_type]
        if severity not in ("low", "medium", "high", "critical"):
            severity = ct["default_severity"]

        self._counter += 1
        tid = f"NAG-GRV-2026-{self._counter:04d}"

        ticket = {
            "ticket_id": tid,
            "complaint_type": complaint_type,
            "complaint_label": ct["label"],
            "complaint_icon": ct["icon"],
            "location": location or random.choice(SAMPLE_LOCATIONS),
            "description": description or "No description provided.",
            "severity": severity,
            "status": "received",
            "status_index": 0,
            "submitted_at": time.time(),
            "citizen_name": citizen_name,
            "evidence_count": random.randint(0, 2),
            "assigned_unit": None,
            "timeline": self._build_timeline(0)
        }
        self.tickets[tid] = ticket
        return {"status": "SUBMITTED", "ticket": ticket}

    def get_ticket(self, ticket_id: str) -> dict:
        """Look up a single ticket."""
        if ticket_id in self.tickets:
            return {"ticket": self.tickets[ticket_id]}
        return {"error": f"Ticket {ticket_id} not found"}

    def advance_ticket(self, ticket_id: str) -> dict:
        """Advance a ticket to the next status stage (for authority dashboard)."""
        if ticket_id not in self.tickets:
            return {"error": f"Ticket {ticket_id} not found"}

        t = self.tickets[ticket_id]
        if t["status_index"] >= len(STATUS_FLOW) - 1:
            return {"status": "ALREADY_CLOSED", "ticket": t}

        t["status_index"] += 1
        t["status"] = STATUS_FLOW[t["status_index"]]
        t["timeline"] = self._build_timeline(t["status_index"])
        if t["status_index"] == 2 and not t["assigned_unit"]:
            t["assigned_unit"] = f"PCR-{random.randint(101, 199)}"

        return {"status": "ADVANCED", "ticket": t}

    def list_tickets(self, status_filter: str = None) -> dict:
        """List all tickets, optionally filtered by status."""
        tickets = list(self.tickets.values())
        if status_filter and status_filter in STATUS_FLOW:
            tickets = [t for t in tickets if t["status"] == status_filter]
        tickets.sort(key=lambda t: t["submitted_at"], reverse=True)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for t in self.tickets.values():
            severity_counts[t["severity"]] = severity_counts.get(t["severity"], 0) + 1

        return {
            "tickets": tickets,
            "total": len(self.tickets),
            "severity_counts": severity_counts,
            "complaint_types": {k: v["label"] for k, v in COMPLAINT_TYPES.items()}
        }
