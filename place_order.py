import argparse
import sys
import time
import uuid

from pika.adapters.blocking_connection import BlockingChannel

from eda import broker, event_log
from eda.config import EXCHANGE, ORDER_REQUESTS_QUEUE, SERVICE_QUEUES
from eda.events import Event, build_event, parse_event

NAME = "app"
TIMEOUT_SECONDS = 20
FINAL_TRIGGERS = {"order.shipped", "payment.denied"}


def build_order(deny: bool) -> dict:
    items = [
        {"title": "Fundamentals of Software Architecture", "qty": 1, "price": 59.99},
        {"title": "Designing Data-Intensive Applications", "qty": 2, "price": 45.50},
    ]
    return {
        "order_id": "ORD-" + uuid.uuid4().hex[:8].upper(),
        "customer": {"name": "Ada Lovelace", "email": "ada@example.com"},
        "items": items,
        "total": round(sum(i["qty"] * i["price"] for i in items), 2),
        "force_deny": deny,
    }


def wait_for_consumers(channel: BlockingChannel) -> None:
    deadline = time.time() + 60
    for queue in SERVICE_QUEUES.values():
        while True:
            try:
                ok = channel.queue_declare(queue, durable=True, passive=True)
                if ok.method.consumer_count > 0:
                    break
            except Exception:
                channel = channel.connection.channel()
            if time.time() > deadline:
                sys.exit(f"service queue {queue} has no consumer")
            time.sleep(1)


def is_final(event: Event, order_id: str) -> bool:
    return (
        event.event_type == "email.sent"
        and event.order_id == order_id
        and event.payload.get("trigger") in FINAL_TRIGGERS
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Place an order for a book.")
    parser.add_argument("--deny", action="store_true", help="force a payment denial")
    args = parser.parse_args()

    connection = broker.connect()
    channel = connection.channel()
    broker.declare_exchange(channel)
    for queue in SERVICE_QUEUES.values():
        channel.queue_declare(queue, durable=True)
    wait_for_consumers(connection.channel())

    audit = channel.queue_declare("", exclusive=True).method.queue
    channel.queue_bind(audit, EXCHANGE, routing_key="#")

    event_log.reset()
    request = build_event("order.requested", NAME, build_order(args.deny))
    broker.publish(channel, request, queue=ORDER_REQUESTS_QUEUE)
    event_log.record(NAME, "produced", request)

    deadline = time.time() + TIMEOUT_SECONDS
    for _method, _props, body in channel.consume(audit, auto_ack=True, inactivity_timeout=1):
        if body is not None:
            event = parse_event(body)
            print(f"[flow] {event.producer} -> {event.event_type} {event.order_id}", flush=True)
            if is_final(event, request.order_id):
                print("[flow] complete", flush=True)
                return 0
        if time.time() > deadline:
            print("[flow] timeout waiting for the flow to finish", flush=True)
            return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
