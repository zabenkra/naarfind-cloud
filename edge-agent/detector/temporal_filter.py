"""Temporal confirmation — fire 3/5, smoke 4/6, fire_smoke 2/4."""

import logging
import os
from collections import deque
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)

TEMPORAL_DEBUG = os.getenv("TEMPORAL_DEBUG", "false").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)


@dataclass
class TemporalRule:
    required: int
    window: int


@dataclass
class TemporalState:
    """Result of one temporal update (after appending current frame)."""

    fire_detected: bool
    smoke_detected: bool
    fire_confirmed: bool = False
    smoke_confirmed: bool = False
    both_confirmed: bool = False
    event_type: str | None = None
    fire_hits: int = 0
    fire_needed: int = 0
    fire_window_len: int = 0
    smoke_hits: int = 0
    smoke_needed: int = 0
    smoke_window_len: int = 0
    both_hits: int = 0
    both_needed: int = 0
    both_window_len: int = 0
    fire_history: list[bool] = field(default_factory=list)
    smoke_history: list[bool] = field(default_factory=list)
    both_history: list[bool] = field(default_factory=list)
    rejected_reason: str | None = None


class TemporalFilter:
    """
    Append one processed-frame sample per update.
    Confirmation uses hits in the sliding window (does NOT require current frame positive).
    """

    def __init__(
        self,
        fire_rule: TemporalRule | None = None,
        smoke_rule: TemporalRule | None = None,
        both_rule: TemporalRule | None = None,
        *,
        instant_dual_confirm: bool = True,
    ):
        self.fire_rule = fire_rule or TemporalRule(3, 5)
        self.smoke_rule = smoke_rule or TemporalRule(4, 6)
        self.both_rule = both_rule or TemporalRule(2, 4)
        self.instant_dual_confirm = instant_dual_confirm

        self._fire_hits: deque[bool] = deque(maxlen=self.fire_rule.window)
        self._smoke_hits: deque[bool] = deque(maxlen=self.smoke_rule.window)
        self._both_hits: deque[bool] = deque(maxlen=self.both_rule.window)

    @staticmethod
    def _count_hits(hits: deque[bool], rule: TemporalRule) -> int:
        recent = list(hits)[-rule.window :]
        return sum(1 for h in recent if h)

    @staticmethod
    def _is_confirmed(hits: deque[bool], rule: TemporalRule) -> bool:
        return TemporalFilter._count_hits(hits, rule) >= rule.required

    def update(self, fire_detected: bool, smoke_detected: bool) -> TemporalState:
        both_this_frame = fire_detected and smoke_detected

        self._fire_hits.append(fire_detected)
        self._smoke_hits.append(smoke_detected)
        self._both_hits.append(both_this_frame)

        fire_count = self._count_hits(self._fire_hits, self.fire_rule)
        smoke_count = self._count_hits(self._smoke_hits, self.smoke_rule)
        both_count = self._count_hits(self._both_hits, self.both_rule)

        fire_confirmed = self._is_confirmed(self._fire_hits, self.fire_rule)
        smoke_confirmed = self._is_confirmed(self._smoke_hits, self.smoke_rule)
        both_confirmed = self._is_confirmed(self._both_hits, self.both_rule)

        state = TemporalState(
            fire_detected=fire_detected,
            smoke_detected=smoke_detected,
            fire_confirmed=fire_confirmed,
            smoke_confirmed=smoke_confirmed,
            both_confirmed=both_confirmed,
            fire_hits=fire_count,
            fire_needed=self.fire_rule.required,
            fire_window_len=len(self._fire_hits),
            smoke_hits=smoke_count,
            smoke_needed=self.smoke_rule.required,
            smoke_window_len=len(self._smoke_hits),
            both_hits=both_count,
            both_needed=self.both_rule.required,
            both_window_len=len(self._both_hits),
            fire_history=list(self._fire_hits),
            smoke_history=list(self._smoke_hits),
            both_history=list(self._both_hits),
        )

        # Same-frame fire+smoke above thresholds → immediate fire_smoke
        if self.instant_dual_confirm and both_this_frame:
            state.both_confirmed = True
            state.event_type = "fire_smoke"
            self._log_debug(state, note="instant_dual_confirm")
            return state

        state.event_type = self._resolve_event_type(state)
        self._log_state(state)
        return state

    @staticmethod
    def _resolve_event_type(state: TemporalState) -> str | None:
        if state.both_confirmed:
            return "fire_smoke"
        if state.fire_confirmed and state.smoke_confirmed:
            return "fire_smoke"
        if state.fire_confirmed:
            return "fire"
        if state.smoke_confirmed:
            return "smoke"
        return None

    def _log_state(self, state: TemporalState) -> None:
        if state.event_type:
            if state.event_type == "fire_smoke":
                logger.warning("FIRE_SMOKE CONFIRMED")
            elif state.event_type == "fire":
                logger.warning("FIRE CONFIRMED")
            elif state.event_type == "smoke":
                logger.warning("SMOKE CONFIRMED")
        elif state.fire_detected or state.smoke_detected:
            logger.info(
                "confirmation pending | fire %s/%s (hist=%s) smoke %s/%s (hist=%s) "
                "both %s/%s (hist=%s)",
                state.fire_hits,
                state.fire_needed,
                _hist_str(state.fire_history),
                state.smoke_hits,
                state.smoke_needed,
                _hist_str(state.smoke_history),
                state.both_hits,
                state.both_needed,
                _hist_str(state.both_history),
            )
        self._log_debug(state)

    def _log_debug(self, state: TemporalState, note: str = "") -> None:
        if not TEMPORAL_DEBUG:
            return
        logger.warning(
            "TEMPORAL_DEBUG %s | frame fire=%s smoke=%s | fire_hist=%s smoke_hist=%s "
            "both_hist=%s | confirmed fire=%s smoke=%s both=%s event=%s",
            note,
            state.fire_detected,
            state.smoke_detected,
            state.fire_history,
            state.smoke_history,
            state.both_history,
            state.fire_confirmed,
            state.smoke_confirmed,
            state.both_confirmed,
            state.event_type,
        )

    def reset(self) -> None:
        self._fire_hits.clear()
        self._smoke_hits.clear()
        self._both_hits.clear()
        if TEMPORAL_DEBUG:
            logger.warning("TEMPORAL_DEBUG history reset")


def _hist_str(history: list[bool]) -> str:
    return "".join("1" if h else "0" for h in history) or "-"
