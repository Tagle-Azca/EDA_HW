import random

from eda.config import PAYMENT_DENY_RATE, SERVICE_QUEUES
from eda.events import Event
from eda.service_runner import Produced, ServiceSpec, run_service

NAME = "payment"


def handle(event: Event) -> Produced:
    forced = bool(event.payload.get("force_deny"))
    if forced or random.random() < PAYMENT_DENY_RATE:
        reason = "card declined (simulated)"
        return [("payment.denied", {**event.payload, "payment_status": "denied", "reason": reason})]
    return [("payment.applied", {**event.payload, "payment_status": "applied"})]


if __name__ == "__main__":
    run_service(ServiceSpec(NAME, SERVICE_QUEUES[NAME], ["order.placed"], handle))
