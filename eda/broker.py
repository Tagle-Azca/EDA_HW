import time

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from eda.config import CONNECT_DELAY_SECONDS, CONNECT_RETRIES, EXCHANGE, RABBITMQ_HOST
from eda.events import Event

PERSISTENT = 2


def connect() -> BlockingConnection:
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            return BlockingConnection(
                pika.ConnectionParameters(RABBITMQ_HOST, heartbeat=60)
            )
        except pika.exceptions.AMQPConnectionError:
            print(f"broker not ready (attempt {attempt}), retrying...", flush=True)
            time.sleep(CONNECT_DELAY_SECONDS)
    raise RuntimeError("could not connect to RabbitMQ")


def declare_exchange(channel: BlockingChannel) -> None:
    channel.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)


def declare_queue(
    channel: BlockingChannel, queue: str, routing_keys: list[str]
) -> None:
    channel.queue_declare(queue, durable=True)
    for key in routing_keys:
        channel.queue_bind(queue, EXCHANGE, routing_key=key)


def publish(channel: BlockingChannel, event: Event, queue: str | None = None) -> None:
    props = pika.BasicProperties(
        delivery_mode=PERSISTENT, content_type="application/json"
    )
    if queue:
        channel.basic_publish("", queue, event.to_json(), props)
    else:
        channel.basic_publish(EXCHANGE, event.event_type, event.to_json(), props)
