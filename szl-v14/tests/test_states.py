import pytest

from szl_v14.lib.states import State, promote, worst_state, Finding


def test_unknown_never_promotes_to_pass():
    with pytest.raises(ValueError):
        promote(State.UNKNOWN, State.PASS)


def test_unknown_can_be_acknowledged_but_not_passed():
    assert promote(State.UNKNOWN, State.BLOCKED) == State.BLOCKED


def test_worst_state_critical_is_fail():
    assert worst_state([Finding("CRITICAL", "X", "y")]) == State.FAIL


def test_worst_state_info_is_pass():
    assert worst_state([Finding("INFO", "X", "y")]) == State.PASS
