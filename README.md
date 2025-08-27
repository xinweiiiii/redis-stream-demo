# Redis Stream Demos (Python)

Two examples for using Redis Streams on Redis Cloud:
- basic_stream/ – a tiny, single-consumer task queue (no consumer groups)
- consumer_group/ – a robust queue using consumer groups with ack/retry & auto-reclaim

# Prerequisites
- Python 3.9+
- Redis Cloud database (TLS enabled is typical)

Prepare and activate the virtual environment
```bash
python3 -m venv .virtualenv && source .virtualenv/bin/activate
```

Install necessary libraries and dependencies
```
pip install -r requirements.txt
```

# Environment
Create .env at the project root (next to redis_client.py) with either a URL or host/port:
```
# Preferred
REDIS_URL=rediss://default:<PASSWORD>@<HOST>:<PORT>
# Or explicitly:
# REDIS_HOST=<host>
# REDIS_PORT=<port>
# REDIS_PASSWORD=<password>
```

# Basic Stream
## What it is?
A simple task queue for one consumer reading from a single stream. Good for demos, scripts, or background jobs where you don’t need parallelism or retries.

## Typical use-cases
Lightweight background processing (Image resizing, sending of email)
One worker that can process tasks in order
“Fire-and-forget” pipelines where replay and retry orchestration aren’t required

## How it works
Producer appends tasks to a stream with `XADD`
Consumer uses `XREAD` to read entries after a specific ID
You manage retention using `MAXLEN` (during XADD) or XTRIM -> This will help to clear the stream if you do not run `XDEL`

## Run
```
 Produce some tasks
python -m basic_stream.producer

# In another terminal, start the consumer
python -m basic_stream.consumer
```

## Key Behaviour
Common gotcha: If producer ran earlier and consumer starts later with `$`, the consumer won’t see the earlier messages by design. Use `0-0` (or your saved offset) to process backlog.

# Consumer Group - consumer groups with ack/retry
## What it is?
A production-style pattern using consumer groups:
- Multiple workers in a group share the stream (work-sharding)
- At-least-once delivery with XACK
- Retry stuck/unacked items via XAUTOCLAIM

## Typical use-cases
- Microservice pipelines (order → payment → shipping)
- Parallel job processing with fault tolerance
- Real-time ETL/analytics where each event must be processed at least once

## How it Works (flow)
1. Producer enqueues with XADD
2. Group is created (idempotently) with XGROUP CREATE ... id="0"
3. Workers call XREADGROUP GROUP <group> <consumer> ... ">" to get messages not yet delivered to the group
4. On success, workers call XACK
5. Periodically, workers call XAUTOCLAIM to steal idle unacked messages from dead/slow consumers and reprocess them

## Run
```
# 1) Create group (if your producer doesn't already do it)
python -m consumer_group.producer_cg   # also enqueues demo tasks

# 2) Start one or more workers (scale horizontally)
python -m consumer_group.worker_cg
python -m consumer_group.worker_cg  # start another terminal to see load sharing

# 3) Optional: see health
python -m consumer_group.monitor_cg
```

## Important Semantic
- Create the group with id="0"
This ensures the group sees existing entries the first time. Creating with id="$" would only deliver new entries.

- XACK does not delete
XACK removes the message from the group’s Pending Entries List (PEL). It does not delete the entry from the stream. Control retention with MAXLEN/XTRIM (producer or a janitor task). Only XDEL actually deletes entries (global).

- Retries via XAUTOCLAIM
Use a sensible min_idle_time (e.g., 15s–60s) so you only steal truly stuck work.
Some redis-py versions return (next_start, messages); others return [next_start, messages, deleted_ids]. Make your code handle both.

- Start position in XREADGROUP
Use ">" for “only messages not yet delivered to this group”. Use "0" to drain your own PEL first if you’re replaying pending tasks.

# How to monitor the output the data output
Run redis insights to see how the processing is done

# When to use which
## Basic Stream
- One worker is enough
- Simplicity over robustness
- You control backlog manually

## Consumer group
- Need parallelism, retries, and fault tolerance
- Clear ownership per message; unacked items are tracked in group PEL
- Easier operational visibility (XINFO, XPENDING, XAUTOCLAIM)

# For more Information
[URL](https://redis.io/docs/latest/develop/data-types/streams/)