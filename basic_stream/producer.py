import json, time
from redis import Redis
from redis_client import connect_redis_sync

STREAM = "tasks.basic"

def enqueue_task(r: Redis, kind: str, payload: dict):
    return r.xadd(STREAM, {"kind": kind, "payload": json.dumps(payload)}, maxlen=10000, approximate=True)

if __name__ == "__main__":
    r = connect_redis_sync()
    for i in range(5):
        task_id = enqueue_task(r, "resize_image", {"image_id": i, "size": "1024x1024"})
        print("enqueued", task_id)
        time.sleep(0.2)

