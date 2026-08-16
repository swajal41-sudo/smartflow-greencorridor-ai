"""
Police Deployment Decision Support & Constrained Personnel Allocation Engine.
Optimizes placement of limited police officers across high-risk Nagpur junctions.
Includes explainable AI reasoning and dynamic incident redeployment.
"""

import random


class PoliceOptimizer:
    def __init__(self, risk_engine):
        self.risk_engine = risk_engine
        self.total_officers = 16
        self.deployment = {}  # junction_id -> officer_count
        self.baseline_deployment = {}  # static/manual baseline for comparison
        self._generate_baseline()

    def _generate_baseline(self):
        """Generate a naive even-spread baseline deployment for comparison."""
        junctions = self.risk_engine.junctions
        per_junction = self.total_officers // len(junctions)
        remainder = self.total_officers % len(junctions)
        for i, j in enumerate(junctions):
            self.baseline_deployment[j["id"]] = per_junction + (1 if i < remainder else 0)

    def optimize(self) -> dict:
        """Run constrained allocation algorithm based on current risk scores."""
        heatmap = self.risk_engine.get_full_heatmap()
        junctions = heatmap["junctions"]

        # Sort by risk score descending
        sorted_junctions = sorted(junctions, key=lambda x: x["risk_score"], reverse=True)

        # Weighted proportional allocation
        total_risk = sum(j["risk_score"] for j in sorted_junctions) or 1
        allocation = {}
        remaining = self.total_officers

        # First pass: proportional allocation
        for j in sorted_junctions:
            raw = (j["risk_score"] / total_risk) * self.total_officers
            alloc = int(raw)
            allocation[j["junction_id"]] = alloc
            remaining -= alloc

        # Second pass: distribute remainder to highest-risk junctions
        while remaining > 0 and sorted_junctions:
            for j in sorted_junctions:
                if remaining <= 0:
                    break
                allocation[j["junction_id"]] += 1
                remaining -= 1

        self.deployment = allocation

        # Build detailed report
        deployment_report = []
        unmanned_high_risk = []
        for j in sorted_junctions:
            jid = j["junction_id"]
            officers = allocation.get(jid, 0)
            baseline = self.baseline_deployment.get(jid, 0)
            entry = {
                "junction_id": jid,
                "name": j["name"],
                "risk_score": j["risk_score"],
                "tier": j["tier"],
                "officers_allocated": officers,
                "baseline_officers": baseline,
                "change": officers - baseline,
                "has_incident": j["active_incident"] is not None,
                "reasoning": self._generate_reasoning(j, officers)
            }
            deployment_report.append(entry)
            if officers == 0 and j["risk_score"] >= 50:
                unmanned_high_risk.append({"junction_id": jid, "name": j["name"], "risk_score": j["risk_score"]})

        # Efficiency metrics
        ai_coverage = sum(1 for d in deployment_report if d["officers_allocated"] > 0 and d["risk_score"] >= 50)
        baseline_coverage = sum(1 for d in deployment_report if d["baseline_officers"] > 0 and d["risk_score"] >= 50)
        high_risk_count = sum(1 for d in deployment_report if d["risk_score"] >= 50)

        return {
            "deployment": deployment_report,
            "unmanned_high_risk": unmanned_high_risk,
            "total_officers": self.total_officers,
            "efficiency": {
                "ai_high_risk_coverage": f"{ai_coverage}/{high_risk_count}",
                "baseline_high_risk_coverage": f"{baseline_coverage}/{high_risk_count}",
                "ai_coverage_pct": round((ai_coverage / max(1, high_risk_count)) * 100, 1),
                "baseline_coverage_pct": round((baseline_coverage / max(1, high_risk_count)) * 100, 1)
            }
        }

    def _generate_reasoning(self, junction: dict, officers: int) -> str:
        """Generate explainable AI reasoning for allocation decision."""
        reasons = []
        f = junction["factors"]

        if junction["risk_score"] >= 75:
            reasons.append(f"CRITICAL risk zone (score {junction['risk_score']}/100)")
        elif junction["risk_score"] >= 50:
            reasons.append(f"HIGH risk zone (score {junction['risk_score']}/100)")

        if f["blackspot"] >= 80:
            reasons.append("Historical accident blackspot")
        if f["congestion"] >= 70:
            reasons.append(f"Severe congestion (density {f['congestion']:.0f}%)")
        if f["road_width"] >= 60:
            reasons.append(f"Narrow road bottleneck ({junction['live_metrics']['road_width_m']}m width)")
        if f["weather"] >= 50:
            reasons.append("Monsoon/weather hazard active")
        if junction["active_incident"]:
            reasons.append(f"ACTIVE INCIDENT: {junction['active_incident']['name']}")
        if f["crowd"] >= 60:
            reasons.append(f"High pedestrian density ({junction['live_metrics']['pedestrian_count']} peds)")

        if officers == 0:
            reasons.append("⚠️ UNMANNED — insufficient officers for coverage")
        elif officers >= 3:
            reasons.append(f"Priority reinforcement: {officers} officers deployed")

        return " | ".join(reasons) if reasons else "Low risk — minimal allocation"

    def set_officers(self, count: int) -> dict:
        self.total_officers = max(4, min(50, count))
        return {"total_officers": self.total_officers}
