"""FastAPI endpoints for the intelligent traffic management system."""

from fastapi import FastAPI, HTTPException
from src.simulation import IntersectionSimulator
from src.optimizer import AdaptiveOptimizer

app = FastAPI(title="Intelligent Traffic Management System", version="1.0.0")

# Singleton instances
simulator = IntersectionSimulator(green_time=30.0, red_time=30.0)
optimizer = AdaptiveOptimizer(min_green=15.0, max_green=60.0)


@app.get("/")
def root():
    return {"message": "Intelligent Traffic Management API", "status": "running"}


@app.post("/simulate/run")
def run_simulation(duration: float = 60.0):
    """Run traffic simulation for specified duration (seconds)."""
    if duration <= 0:
        raise HTTPException(status_code=400, detail="duration must be positive")
    state = simulator.run(duration=duration)
    # Optimize green time based on observed queues
    adjusted_green = optimizer.evaluate(state["queues"])
    return {
        "duration": duration,
        "final_state": state,
        "optimized_green_time": round(adjusted_green, 2),
        "phase_switches": 1 if state["phase"] == "E-W" else 0,
    }


@app.get("/simulate/status")
def current_status():
    """Return current simulation state without advancing time."""
    return simulator.state()


@app.post("/optimizer/adjust")
def adjust_green(queues: dict):
    """Manually adjust green time based on queue measurements."""
    try:
        green = optimizer.evaluate(queues)
        switch = optimizer.should_switch(queues)
        return {"green_time": round(green, 2), "should_switch": switch}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))