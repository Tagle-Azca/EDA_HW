import uuid

from eda.config import SERVICE_QUEUES
from eda.events import Event
from eda.service_runner import Produced, ServiceSpec, run_service

NAME = "shipping"


def handle(event: Event) -> Produced:
    tracking = "TRK-" + uuid.uuid4().hex[:10].upper()
    return [("order.shipped", {**event.payload, "tracking_number": tracking})]


if __name__ == "__main__":
    run_service(ServiceSpec(NAME, SERVICE_QUEUES[NAME], ["order.fulfilled"], handle))
