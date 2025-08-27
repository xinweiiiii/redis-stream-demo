import json, time
from redis import Redis
from redis.exceptions import ResponseError
from redis_client import connect_redis_sync

STREAM = "tasks.cg"
GROUP  = "workers"

def ensure_group(r: Redis):
    try:
        # start from '0' to let brand new workers read historical items if any
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        print(f"created group {GROUP} on {STREAM}")
    except ResponseError as e:
        # already exists
        if "BUSYGROUP" in str(e):
            pass
        else:
            raise

if __name__ == "__main__":
    r = connect_redis_sync()
    ensure_group(r)

    for i in range(10):
        task = {"kind": "render_pdf", "payload": json.dumps({"doc_id": i})}
        task_id = r.xadd(STREAM, task, maxlen=10000, approximate=True)
        print("enqueued", task_id)
        time.sleep(0.1)
