from eda.config import SERVICE_QUEUES
from eda.events import Event
from eda.service_runner import Produced, ServiceSpec, run_service

NAME = "notification"
WATCHED = ["order.placed", "payment.denied", "order.fulfilled", "order.shipped"]


def handle(event: Event) -> Produced:
    payload = {
        "order_id": event.order_id,
        "to": event.payload.get("customer", {}).get("email"),
        "subject": f"Update on your order: {event.event_type}",
        "trigger": event.event_type,
    }
    return [("email.sent", payload)]


if __name__ == "__main__":
    run_service(ServiceSpec(NAME, SERVICE_QUEUES[NAME], WATCHED, handle))
