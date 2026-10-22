from dataclasses import dataclass
from typing import Any, Callable

from pika.adapters.blocking_connection import BlockingChannel

from eda import broker, event_log
from eda.events import Event, build_event, parse_event

Produced = list[tuple[str, dict[str, Any]]]
Handler = Callable[[Event], Produced]


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    queue: str
    routing_keys: list[str]
    handler: Handler


def run_service(spec: ServiceSpec) -> None:
    connection = broker.connect()
    channel = connection.channel()
    broker.declare_exchange(channel)
    broker.declare_queue(channel, spec.queue, spec.routing_keys)
    channel.basic_qos(prefetch_count=1)

    def on_message(ch: BlockingChannel, method: Any, _props: Any, body: bytes) -> None:
        event = parse_event(body)
        event_log.record(spec.name, "consumed", event)
        for event_type, payload in spec.handler(event):
            out = build_event(event_type, spec.name, payload)
            broker.publish(ch, out)
            event_log.record(spec.name, "produced", out)
        ch.basic_ack(method.delivery_tag)

    channel.basic_consume(spec.queue, on_message)
    print(f"{spec.name} waiting for events on {spec.queue}", flush=True)
    channel.start_consuming()
