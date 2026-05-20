"""Temporal confirmation to reduce single-frame false alarms."""

from collections import deque
from dataclasses import dataclass


@dataclass
class TemporalRule:
    required: int
    window: int


class TemporalFilter:
    """Track recent detection hits and confirm only after enough hits in a window."""

    def __init__(
        self,
        fire_rule: TemporalRule | None = None,
        smoke_rule: TemporalRule | None = None,
        both_rule: TemporalRule | None = None,
    ):
        self.fire_rule = fire_rule or TemporalRule(3, 5)
        self.smoke_rule = smoke_rule or TemporalRule(4, 6)
        self.both_rule = both_rule or TemporalRule(2, 4)

        self._fire_hits: deque[bool] = deque(maxlen=self.fire_rule.window)
        self._smoke_hits: deque[bool] = deque(maxlen=self.smoke_rule.window)
        self._both_hits: deque[bool] = deque(maxlen=self.both_rule.window)

    @staticmethod
    def _confirmed(hits: deque[bool], rule: TemporalRule) -> bool:
        if len(hits) < rule.window:
            return False
        return sum(hits) >= rule.required

    def update(self, fire_detected: bool, smoke_detected: bool) -> dict:
        self._fire_hits.append(fire_detected)
        self._smoke_hits.append(smoke_detected)
        self._both_hits.append(fire_detected and smoke_detected)

        fire_confirmed = fire_detected and self._confirmed(self._fire_hits, self.fire_rule)
        smoke_confirmed = smoke_detected and self._confirmed(self._smoke_hits, self.smoke_rule)
        both_confirmed = (
            fire_detected
            and smoke_detected
            and self._confirmed(self._both_hits, self.both_rule)
        )

        return {
            "fire_confirmed": fire_confirmed,
            "smoke_confirmed": smoke_confirmed,
            "both_confirmed": both_confirmed,
        }

    def reset(self) -> None:
        self._fire_hits.clear()
        self._smoke_hits.clear()
        self._both_hits.clear()
