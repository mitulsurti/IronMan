from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor_id: str
    actor_type: str
    occurred_at: datetime
    subject_type: str
    subject_id: str
    metadata: dict[str, Any]
