"""Traffic simulation module - generates vehicle flows through intersections."""


class Vehicle:
    def __init__(self, id: int, approach: str, arrival_time: float):
        self.id = id
        self.approach = approach
        self.arrival_time = arrival_time


class IntersectionSimulator:
    """Simple intersection with four approaches (N, S, E, W)."""

    def __init__(self, green_time: float = 30.0, red_time: float = 30.0, 
                 queue_threshold: float = 5.0):
        self.green_time = green_time
        self.red_time = red_time
        self.queue_threshold = queue_threshold
        self.reset()

    def reset(self):
        self.time = 0.0
        self.queues = {"N": 0, "S": 0, "E": 0, "W": 0}
        self.vehicles_generated = {"N": 0, "S": 0, "E": 0, "W": 0}
        self.total_wait_time = 0.0
        self.phase = "N-S"  # current green phase
        self.phase_time = 0.0

    def update(self, dt: float) -> dict:
        """Advance simulation by dt seconds. Returns state dict."""
        # Generate vehicles (Poisson-like, ~2 per sec per approach)
        for approach in self.queues:
            # Random vehicle generation
            import random
            if random.random() < 0.3 * dt:
                self.vehicles_generated[approach] += 1
                self.queues[approach] += 1

        # Advance phase timer
        self.phase_time += dt
        if self.phase == "N-S" and self.phase_time >= self.green_time:
            self.phase = "E-W"
            self.phase_time = 0.0
        elif self.phase == "E-W" and self.phase_time >= self.red_time:
            self.phase = "N-S"
            self.phase_time = 0.0

        # Vehicles move through if their approach has green
        moving = {"N": 0, "S": 0, "E": 0, "W": 0}
        if self.phase == "N-S":
            # N and S can move; E and W stuck
            move_rate = 2.0  # vehicles/sec per green approach
            moving["N"] = min(self.queues["N"], move_rate * dt)
            moving["S"] = min(self.queues["S"], move_rate * dt)
            wait_N = moving["N"]
            wait_S = moving["S"]
        else:
            # E and W can move
            move_rate = 2.0
            moving["E"] = min(self.queues["E"], move_rate * dt)
            moving["W"] = min(self.queues["W"], move_rate * dt)
            wait_E = moving["E"]
            wait_W = moving["W"]

        # Remove moved vehicles from queue, add wait time
        for approach in self.queues:
            self.queues[approach] -= moving[approach]
            self.total_wait_time += getattr(self, f'wait_{approach}', 0) * moving[approach] if False else 0

        # Simplified wait time accumulation
        for approach in self.queues:
            self.total_wait_time += self.queues[approach] * dt * 0.1

        self.time += dt
        return self.state()

    def state(self) -> dict:
        """Return current simulation state."""
        return {
            "time": round(self.time, 2),
            "phase": self.phase,
            "queues": dict(self.queues),
            "total_wait_time": round(self.total_wait_time, 2),
            "green_time": self.green_time,
            "red_time": self.red_time,
        }

    def run(self, duration: float = 60.0) -> dict:
        """Run simulation for duration seconds, return final state."""
        while self.time < duration:
            self.update(1.0)  # 1-sec steps
        return self.state()