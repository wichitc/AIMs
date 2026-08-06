from app.modules.defect.service import _VALID_TRANSITIONS


def test_happy_path_transitions_are_all_allowed():
    happy_path = ["Finding", "Assessment", "Approval", "Repair", "Verification", "Closed"]
    for current, target in zip(happy_path, happy_path[1:]):
        assert target in _VALID_TRANSITIONS[current], f"{current} -> {target} should be allowed"


def test_failed_verification_can_return_to_repair():
    assert "Repair" in _VALID_TRANSITIONS["Verification"]


def test_closed_is_terminal():
    assert _VALID_TRANSITIONS["Closed"] == set()


def test_cannot_skip_steps():
    # Finding cannot jump straight to Repair or Closed — must pass through Assessment/Approval.
    assert "Repair" not in _VALID_TRANSITIONS["Finding"]
    assert "Closed" not in _VALID_TRANSITIONS["Finding"]


def test_cannot_move_backward_except_the_documented_verification_failure_case():
    for current, allowed in _VALID_TRANSITIONS.items():
        if current == "Verification":
            continue  # the one legitimate backward transition (failed verification)
        assert "Finding" not in allowed
