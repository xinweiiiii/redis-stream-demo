import os, json, time, socket, random
from redis import Redis
from redis_client import connect_redis_sync

STREAM = "tasks.cg"
GROUP  = "workers"

def process(fields: dict):
    # demo work
    payload = json.loads(fields["payload"])
    print(f"[do] {fields['kind']} -> {payload}")
    # simulate occasional crash/slow
    if random.random() < 0.1:
        raise RuntimeError("boom")  # to test retry
    time.sleep(random.uniform(0.05, 0.2))

if __name__ == "__main__":
    r = connect_redis_sync()
    consumer = f"{socket.gethostname()}-{os.getpid()}"

    # read loop
    print(f"worker {consumer} listening (group={GROUP}, stream={STREAM}) … Ctrl+C to quit")
    idle_reclaim_ms = 15_000   # how long before we try to steal stuck tasks
    reclaim_batch   = 20

    last_reclaim = 0.0

    while True:
        # First: drain our PEL (Pending Entries List) using ID '0'
        resp = r.xreadgroup(GROUP, consumer, {STREAM: ">"}, count=16, block=5000)
        if not resp:
            # No new messages; periodically attempt auto-claim from abandoned consumers
            now = time.time()
            if now - last_reclaim > 5:
                last_reclaim = now
                # XAUTOCLAIM: claim messages idle for idle_reclaim_ms and assign to me
                # returns (start_id, [(id, fields), ...])
                start_id = "0-0"
                res = r.xautoclaim(STREAM, GROUP, consumer, min_idle_time=idle_reclaim_ms, start_id=start_id, count=reclaim_batch)
                
                if isinstance(res, tuple) and len(res) == 2:
                    next_start, msgs = res                     # redis-py 5.x tuple
                elif isinstance(res, list) and len(res) >= 2:
                    next_start = res[0]                        # cursor
                    msgs = res[1]                              # list of (id, fields)
                    # res[2] (if present) is deleted/invalid ids; usually []
                else:
                    # redis-py 4.x old behavior (just the list)
                    msgs = res
                    next_start = start_id

                print(f"claimed cursor={next_start} count={len(msgs)}")
                
                for entry_id, fields in msgs:
                    try:
                        process(fields)
                        r.xack(STREAM, GROUP, entry_id)
                        print(f"[reclaimed✓] {entry_id}")
                    except Exception as e:
                        print(f"[reclaimed✗] {entry_id}: {e}")
                start_id = next_start
            continue

        # Handle new deliveries
        for _, entries in resp:
            for entry_id, fields in entries:
                try:
                    process(fields)
                    r.xack(STREAM, GROUP, entry_id)
                    print(f"[ack] {entry_id}")
                except Exception as e:
                    # do NOT ack on failure; it will remain pending and be retried
                    print(f"[fail] {entry_id}: {e}")
