"""
---
role: 状态机
depends: []
exports:
  - MONITORING
  - BREAKOUT_DETECTED
  - HOLDING
  - StrategyStateMachine
status: IMPLEMENTED
functions:
  - StrategyStateMachine.get_state() -> str
  - StrategyStateMachine.transition(new_state: str) -> None
  - StrategyStateMachine.mark_bought(timestamp: float | int | str) -> None
  - StrategyStateMachine.reset() -> None
---
"""

from __future__ import annotations

MONITORING = "MONITORING"
BREAKOUT_DETECTED = "BREAKOUT_DETECTED"
HOLDING = "HOLDING"


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    MONITORING: {BREAKOUT_DETECTED},
    BREAKOUT_DETECTED: {HOLDING, MONITORING},
    HOLDING: {MONITORING},
}


class StrategyStateMachine:
    def __init__(self) -> None:
        self._state = MONITORING
        self._bought_at: float | int | str | None = None

    def get_state(self) -> str:
        return self._state

    @property
    def bought_at(self) -> float | int | str | None:
        return self._bought_at

    def transition(self, new_state: str) -> None:
        if new_state == self._state:
            return

        allowed = _ALLOWED_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise ValueError(f"Illegal transition: {self._state} -> {new_state}")
        self._state = new_state

    def mark_bought(self, timestamp: float | int | str) -> None:
        self.transition(HOLDING)
        self._bought_at = timestamp

    def reset(self) -> None:
        self._state = MONITORING
        self._bought_at = None
