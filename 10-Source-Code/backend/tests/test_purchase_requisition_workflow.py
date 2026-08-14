from app.modules.purchasing.service import _PR_VALID_TRANSITIONS


def test_draft_can_be_submitted_or_withdrawn():
    assert _PR_VALID_TRANSITIONS["Draft"] == {"Submitted", "Withdrawn"}


def test_submitted_can_be_approved_rejected_or_withdrawn():
    assert _PR_VALID_TRANSITIONS["Submitted"] == {"Approved", "Rejected", "Withdrawn"}


def test_approved_rejected_and_withdrawn_are_terminal():
    assert _PR_VALID_TRANSITIONS["Approved"] == set()
    assert _PR_VALID_TRANSITIONS["Rejected"] == set()
    assert _PR_VALID_TRANSITIONS["Withdrawn"] == set()


def test_draft_cannot_skip_straight_to_approved():
    assert "Approved" not in _PR_VALID_TRANSITIONS["Draft"]
