from datetime import datetime, timezone

from ironman.audit.events import AuditEvent


def test_audit_event_identifies_actor_and_subject() -> None:
    event = AuditEvent(
        event_type="foundation.test",
        actor_id="owner",
        actor_type="human",
        occurred_at=datetime.now(timezone.utc),
        subject_type="test",
        subject_id="1",
        metadata={},
    )
    assert event.actor_type == "human"
    assert event.subject_id == "1"
