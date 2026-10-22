from eda.config import SERVICE_QUEUES
from eda.events import Event
from eda.service_runner import Produced, ServiceSpec, run_service

NAME = "order_placement"


def handle(event: Event) -> Produced:
    return [("order.placed", event.payload)]


if __name__ == "__main__":
    run_service(ServiceSpec(NAME, SERVICE_QUEUES[NAME], [], handle))
