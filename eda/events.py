import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    timestamp: str
    producer: str
    payload: dict[str, Any]

    @property
    def order_id(self) -> str:
        return str(self.payload.get("order_id", "-"))

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")


def build_event(event_type: str, producer: str, payload: dict[str, Any]) -> Event:
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        producer=producer,
        payload=payload,
    )


def parse_event(body: bytes) -> Event:
    return Event(**json.loads(body))
