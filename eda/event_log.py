import os
from datetime import datetime, timezone

from eda.config import LOG_FILE
from eda.events import Event


def format_line(service: str, action: str, event: Event) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return (
        f"{now} | {service} | {action} | {event.event_type} | "
        f"event_id={event.event_id} order_id={event.order_id}"
    )


def record(service: str, action: str, event: Event) -> None:
    line = format_line(service, action, event)
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def reset() -> None:
    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
    open(LOG_FILE, "w", encoding="utf-8").close()
