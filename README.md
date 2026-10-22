Claude Code was used on the markdown and on the file structure.

All was in English as industry standards.

# Event Driven Architecture: Order Flow

This project simulates the green flow of the order example we saw in class. It uses Python, RabbitMQ and Docker Compose, and each service and the broker run in their own container. Payments and emails are not real, only the events are generated.

## Green flow

```
 place_order.py --order.requested--> [Order Placement] --order.placed--+--> [Payment]
 (app container)                                                       |       |
                                                                       |       +-- payment.applied --> [Order Fulfillment]
                                                                       |       |                              |
                                                                       |       +-- payment.denied             order.fulfilled
                                                                       |                                      |
                                                                       |                                      v
                                                                       |                                 [Shipping]
                                                                       |                                      |
                                                                       |                                 order.shipped
                                                                       v                                      |
 [Notification] <--- order.placed, payment.denied, order.fulfilled, order.shipped <---------------------------+
      |
      +--> email.sent (one per consumed event; nothing is really sent)
```

A denied payment never triggers fulfillment or shipping.

## Services and events

| Service           | Consumes                                                      | Produces                         |
|-------------------|---------------------------------------------------------------|----------------------------------|
| app (place_order) | all events (audit queue, to print the flow)                   | `order.requested`                |
| order_placement   | `order.requested` (queue `order_requests`)                    | `order.placed`                   |
| payment           | `order.placed`                                                | `payment.applied` / `payment.denied` |
| order_fulfillment | `payment.applied`                                             | `order.fulfilled`                |
| shipping          | `order.fulfilled`                                             | `order.shipped`                  |
| notification      | `order.placed`, `payment.denied`, `order.fulfilled`, `order.shipped` | `email.sent`              |

## Event structure

```json
{
  "event_id": "89f6d993-dacd-44cc-9a0d-fb229f010b93",
  "event_type": "order.placed",
  "timestamp": "2026-10-22T04:29:36.682531+00:00",
  "producer": "order_placement",
  "payload": {
    "order_id": "ORD-79CFCF79",
    "customer": {"name": "Ada Lovelace", "email": "ada@example.com"},
    "items": [{"title": "Fundamentals of Software Architecture", "qty": 1, "price": 59.99}],
    "total": 150.99,
    "force_deny": false
  }
}
```

Later events extend the payload: `payment_status` and `reason` (payment),
`fulfillment_status` (fulfillment), `tracking_number` (shipping). `email.sent`
carries `to`, `subject` and `trigger` (the event that caused the email).

## How to run

From this folder:

```
docker compose run --rm app python place_order.py          # payment applied
docker compose run --rm app python place_order.py --deny   # forced payment denial
docker compose down                                        # stop everything
```

The first command builds the image, starts the broker (waits for its
healthcheck) and the five services, waits until each has a consumer, publishes
the order request, prints the flow and exits 0 when the final `email.sent`
arrives (exit 1 after 20 seconds without it). `PAYMENT_DENY_RATE` (default `0`,
range 0 to 1) makes Payment deny randomly, e.g.
`PAYMENT_DENY_RATE=0.5 docker compose run --rm app python place_order.py`.
The RabbitMQ UI is at http://localhost:15672 (guest / guest).

## Logs

Every produce/consume appends one line to `logs/events.log` (bind-mounted into
all containers) and prints it to stdout (`docker compose logs <service>`).
The file is created at runtime, git-ignored, and truncated at the start of each
`place_order.py` run. Format:

```
<ISO timestamp> | <service> | <produced|consumed> | <event_type> | event_id=<id> order_id=<id>
```

Real excerpt (denied run):

```
2026-10-22T04:29:41.705094+00:00 | app | produced | order.requested | event_id=8edf7cce-... order_id=ORD-51E8011E
2026-10-22T04:29:41.705662+00:00 | order_placement | consumed | order.requested | event_id=8edf7cce-... order_id=ORD-51E8011E
2026-10-22T04:29:41.707824+00:00 | order_placement | produced | order.placed | event_id=c204ffb2-... order_id=ORD-51E8011E
2026-10-22T04:29:41.708721+00:00 | payment | consumed | order.placed | event_id=c204ffb2-... order_id=ORD-51E8011E
2026-10-22T04:29:41.710636+00:00 | payment | produced | payment.denied | event_id=d6428447-... order_id=ORD-51E8011E
2026-10-22T04:29:41.711932+00:00 | notification | consumed | payment.denied | event_id=d6428447-... order_id=ORD-51E8011E
2026-10-22T04:29:41.712684+00:00 | notification | produced | email.sent | event_id=f8e9b4d9-... order_id=ORD-51E8011E
```

## Project layout

```
Dockerfile, docker-compose.yml, requirements.txt
place_order.py          initiates the flow and prints it
eda/config.py           env settings and constants
eda/events.py           Event dataclass, build/parse
eda/broker.py           connection with retry, topology, publish
eda/event_log.py        log line writer (file + stdout)
eda/service_runner.py   generic consumer loop
services/*.py           one thin handler per service
logs/                   runtime log (events.log is git-ignored)
```

## Design choices

- **Topic exchange** (`order_events`): events are published with their type as
  routing key; each consumer binds its own durable queue to the types it needs,
  so producers do not know their consumers.
- **Reliability**: durable queues, persistent messages, manual acks (an event is
  acked only after its follow-up events were published).
- **Startup**: the broker has a healthcheck and services depend on it; code also
  retries the connection. `place_order.py` declares the queues and waits until
  every service has a consumer, so no event is lost on a cold start.
- **Order request**: sent point-to-point to the `order_requests` queue (the
  "place an order" arrow); Order Placement then publishes `order.placed`.
- **Thin services**: a handler maps one incoming event to the events to produce;
  `service_runner.py` handles consuming, logging, publishing and acking.
