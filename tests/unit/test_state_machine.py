import unittest

from futures_monitor.strategy.state_machine import (
    BREAKOUT_DETECTED,
    HOLDING,
    MONITORING,
    StrategyStateMachine,
)


class TestStateMachine(unittest.TestCase):
    def test_default_state(self) -> None:
        machine = StrategyStateMachine()
        self.assertEqual(machine.get_state(), MONITORING)

    def test_legal_transitions(self) -> None:
        machine = StrategyStateMachine()
        machine.transition(BREAKOUT_DETECTED)
        self.assertEqual(machine.get_state(), BREAKOUT_DETECTED)

        machine.mark_bought("2026-03-07T09:30:00")
        self.assertEqual(machine.get_state(), HOLDING)
        self.assertEqual(machine.bought_at, "2026-03-07T09:30:00")

        machine.transition(MONITORING)
        self.assertEqual(machine.get_state(), MONITORING)

    def test_illegal_transition_raises(self) -> None:
        machine = StrategyStateMachine()
        with self.assertRaises(ValueError):
            machine.transition(HOLDING)


if __name__ == "__main__":
    unittest.main()
