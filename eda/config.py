import os

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
LOG_FILE = os.environ.get("LOG_FILE", "logs/events.log")
PAYMENT_DENY_RATE = float(os.environ.get("PAYMENT_DENY_RATE", "0"))

EXCHANGE = "order_events"
ORDER_REQUESTS_QUEUE = "order_requests"
CONNECT_RETRIES = 30
CONNECT_DELAY_SECONDS = 2

SERVICE_QUEUES = {
    "order_placement": ORDER_REQUESTS_QUEUE,
    "payment": "payment_queue",
    "order_fulfillment": "order_fulfillment_queue",
    "shipping": "shipping_queue",
    "notification": "notification_queue",
}
