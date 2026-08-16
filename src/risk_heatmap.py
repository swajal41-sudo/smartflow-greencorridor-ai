"""
AI Traffic Risk Heatmap & Scoring Engine for Nagpur City.
Multi-factor risk model (0-100) covering 12 real Nagpur junctions.
Factors: congestion density, historical accident blackspot weight,
weather/monsoon waterlogging, road-width bottleneck, crowd surge.
"""

import random
import math

NAGPUR_JUNCTIONS = [
    {"id": "J01", "name": "Sitabuldi Square", "lat": 21.1458, "lng": 79.0882, "base_risk": 72, "blackspot": True, "road_width_m": 12},
    {"id": "J02", "name": "Cotton Market", "lat": 21.1525, "lng": 79.0812, "base_risk": 58, "blackspot": False, "road_width_m": 18},
    {"id": "J03", "name": "Medical Square", "lat": 21.1397, "lng": 79.0950, "base_risk": 81, "blackspot": True, "road_width_m": 10},
    {"id": "J04", "name": "Sadar (Variety Sq)", "lat": 21.1511, "lng": 79.0725, "base_risk": 55, "blackspot": False, "road_width_m": 22},
    {"id": "J05", "name": "Itwari Station Rd", "lat": 21.1571, "lng": 79.0831, "base_risk": 65, "blackspot": True, "road_width_m": 9},
    {"id": "J06", "name": "Shankar Nagar Sq", "lat": 21.1313, "lng": 79.0620, "base_risk": 48, "blackspot": False, "road_width_m": 20},
    {"id": "J07", "name": "Trimurti Nagar", "lat": 21.1263, "lng": 79.0487, "base_risk": 42, "blackspot": False, "road_width_m": 24},
    {"id": "J08", "name": "Hingna T-Point", "lat": 21.1100, "lng": 79.0350, "base_risk": 60, "blackspot": True, "road_width_m": 11},
    {"id": "J09", "name": "Automotive Square", "lat": 21.1350, "lng": 79.1050, "base_risk": 69, "blackspot": True, "road_width_m": 14},
    {"id": "J10", "name": "Pardi Flyover", "lat": 21.1600, "lng": 79.0950, "base_risk": 53, "blackspot": False, "road_width_m": 16},
    {"id": "J11", "name": "Zero Mile", "lat": 21.1497, "lng": 79.0806, "base_risk": 76, "blackspot": True, "road_width_m": 10},
    {"id": "J12", "name": "Wardha Rd Viaduct", "lat": 21.1320, "lng": 79.1100, "base_risk": 74, "blackspot": True, "road_width_m": 12},
]

INCIDENT_SCENARIOS = {
    "tanker_overturn": {
        "name": "Overturned Fuel Tanker at Medical Square",
        "junction_id": "J03",
        "risk_boost": 35,
        "description": "A fuel tanker overturned blocking 3 lanes. Fire hazard. Immediate lane closure and rerouting required."
    },
    "monsoon_waterlog": {
        "name": "Monsoon Waterlogging on Wardha Underpass",
        "junction_id": "J12",
        "risk_boost": 28,
        "description": "Heavy rainfall flooded the Wardha Rd underpass to 2ft depth. Vehicles stranded, diversions needed."
    },
    "vip_convoy": {
        "name": "VIP Convoy at Zero Mile",
        "junction_id": "J11",
        "risk_boost": 22,
        "description": "VIP convoy with 6-vehicle escort passing through Zero Mile. Temporary road closure for 15 minutes."
    },
    "road_accident": {
        "name": "Multi-Vehicle Pile-up at Automotive Square",
        "junction_id": "J09",
        "risk_boost": 30,
        "description": "3-vehicle collision at Automotive Square. 2 injuries reported. Ambulance dispatched. Traffic backed up 800m."
    },
    "festival_crowd": {
        "name": "Festival Crowd Surge at Sitabuldi",
        "junction_id": "J01",
        "risk_boost": 25,
        "description": "Dussehra procession crowd spilling onto main road. Pedestrian density exceeding safe limits."
    }
}


class RiskHeatmapEngine:
    def __init__(self):
        self.junctions = [dict(j) for j in NAGPUR_JUNCTIONS]
        self.active_incidents = {}  # junction_id -> incident info
        self.weather_severity = 0.0  # 0.0 (clear) to 1.0 (extreme monsoon)
        self.time_of_day = "day"  # 'day', 'night', 'rush_hour'
        self._randomize_live_data()

    def _randomize_live_data(self):
        """Simulate live congestion variance."""
        for j in self.junctions:
            j["live_congestion"] = max(0, min(100, j["base_risk"] + random.randint(-12, 18)))
            j["vehicle_count"] = random.randint(30, 250)
            j["pedestrian_count"] = random.randint(5, 80)
            j["avg_speed_kmh"] = max(5, 45 - int(j["live_congestion"] * 0.4) + random.randint(-5, 5))

    def compute_risk_score(self, junction: dict) -> dict:
        """Multi-factor weighted risk score (0-100) with explainable breakdown."""
        # Factor 1: Live congestion density (weight 0.30)
        congestion_score = junction.get("live_congestion", junction["base_risk"])

        # Factor 2: Historical accident blackspot (weight 0.20)
        blackspot_score = 85 if junction["blackspot"] else 20

        # Factor 3: Weather / Monsoon waterlogging (weight 0.15)
        weather_score = self.weather_severity * 90

        # Factor 4: Road width bottleneck (weight 0.20) — narrower = higher risk
        width = junction["road_width_m"]
        width_score = max(0, min(100, (25 - width) * 5))

        # Factor 5: Crowd / pedestrian surge (weight 0.15)
        ped = junction.get("pedestrian_count", 30)
        crowd_score = min(100, ped * 1.3)

        # Incident boost
        incident_boost = 0
        incident_info = None
        if junction["id"] in self.active_incidents:
            inc = self.active_incidents[junction["id"]]
            incident_boost = inc["risk_boost"]
            incident_info = inc

        weighted = (
            congestion_score * 0.30 +
            blackspot_score * 0.20 +
            weather_score * 0.15 +
            width_score * 0.20 +
            crowd_score * 0.15 +
            incident_boost
        )
        final_score = max(0, min(100, round(weighted)))

        # Risk tier
        if final_score >= 75:
            tier = "CRITICAL"
        elif final_score >= 50:
            tier = "HIGH"
        elif final_score >= 30:
            tier = "MODERATE"
        else:
            tier = "LOW"

        return {
            "junction_id": junction["id"],
            "name": junction["name"],
            "lat": junction["lat"],
            "lng": junction["lng"],
            "risk_score": final_score,
            "tier": tier,
            "factors": {
                "congestion": round(congestion_score, 1),
                "blackspot": round(blackspot_score, 1),
                "weather": round(weather_score, 1),
                "road_width": round(width_score, 1),
                "crowd": round(crowd_score, 1),
                "incident_boost": incident_boost
            },
            "live_metrics": {
                "vehicle_count": junction.get("vehicle_count", 0),
                "pedestrian_count": junction.get("pedestrian_count", 0),
                "avg_speed_kmh": junction.get("avg_speed_kmh", 0),
                "road_width_m": junction["road_width_m"]
            },
            "active_incident": {
                "name": incident_info["name"],
                "description": incident_info["description"]
            } if incident_info else None
        }

    def get_full_heatmap(self) -> dict:
        """Return scored heatmap for all junctions."""
        self._randomize_live_data()
        scored = [self.compute_risk_score(j) for j in self.junctions]
        scored.sort(key=lambda x: x["risk_score"], reverse=True)

        critical = sum(1 for s in scored if s["tier"] == "CRITICAL")
        high = sum(1 for s in scored if s["tier"] == "HIGH")

        return {
            "junctions": scored,
            "summary": {
                "total_junctions": len(scored),
                "critical_count": critical,
                "high_count": high,
                "avg_risk": round(sum(s["risk_score"] for s in scored) / len(scored), 1),
                "weather_severity": self.weather_severity,
                "active_incidents": len(self.active_incidents)
            }
        }

    def trigger_incident(self, scenario_key: str) -> dict:
        """Trigger a predefined incident scenario."""
        if scenario_key not in INCIDENT_SCENARIOS:
            return {"error": f"Unknown scenario: {scenario_key}"}
        scenario = INCIDENT_SCENARIOS[scenario_key]
        self.active_incidents[scenario["junction_id"]] = scenario
        return {
            "status": "INCIDENT_TRIGGERED",
            "incident": scenario,
            "heatmap": self.get_full_heatmap()
        }

    def clear_incident(self, junction_id: str) -> dict:
        """Clear an active incident."""
        if junction_id in self.active_incidents:
            del self.active_incidents[junction_id]
        return {"status": "INCIDENT_CLEARED", "junction_id": junction_id}

    def set_weather(self, severity: float) -> dict:
        """Set monsoon/weather severity 0.0 - 1.0."""
        self.weather_severity = max(0.0, min(1.0, severity))
        return {"weather_severity": self.weather_severity}
