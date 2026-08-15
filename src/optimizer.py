"""Adaptive traffic light optimizer - adjusts green times based on queue lengths."""


class AdaptiveOptimizer:
    """Simple rule-based optimizer: extend green if queue is long, switch if short."""

    def __init__(self, min_green: float = 15.0, max_green: float = 60.0,
                 queue_threshold: float = 3.0, extension_step: float = 5.0):
        self.min_green = min_green
        self.max_green = max_green
        self.queue_threshold = queue_threshold
        self.extension_step = extension_step
        self.current_green = min_green

    def evaluate(self, queues: dict) -> float:
        """Return adjusted green time based on current queues (seconds)."""
        avg_queue = sum(queues.values()) / len(queues) if queues else 0
        if avg_queue > self.queue_threshold:
            # Extend green, but cap at max
            self.current_green = min(self.max_green, self.current_green + self.extension_step)
        elif avg_queue < self.queue_threshold * 0.5 and self.current_green > self.min_green:
            # Reduce green if queues are very light
            self.current_green = max(self.min_green, self.current_green - self.extension_step)
        return self.current_green

    def should_switch(self, queues: dict) -> bool:
        """Return True if phase should switch now based on queue lengths."""
        avg_queue = sum(queues.values()) / len(queues) if queues else 0
        # Switch if queues are very light (cleared) or extremely heavy (stuck)
        return avg_queue < 1.0 or (avg_queue > 10 and self.current_green >= self.max_green)