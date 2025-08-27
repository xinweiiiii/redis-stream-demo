import os, json
from redis import Redis
from ..redis_client import connect_redis

STREAM = "tasks.basic"

def process(task):
    # replace with real work
    kind = task["kind"]; payload = json.loads(task["payload"])
    print(f"processing {kind} -> {payload}")

if __name__ == "__main__":
    r = redis_client()
    last_id = "$"  # start with only new messages
    print("worker_basic: waiting for tasks… Ctrl+C to quit")
    while True:
        resp = r.xread({STREAM: last_id}, block=10_000, count=10)
        if not resp:
            continue
        for _, entries in resp:
            for entry_id, fields in entries:
                process(fields)
                r.xdel(STREAM, entry_id)
                last_id = entry_id