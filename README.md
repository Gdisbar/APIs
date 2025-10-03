# APIs

### Async + Sync Redis - Chatbot
```
async_redis_client = async_redis.Redis(...)
sync_redis_client = redis.Redis(...)

# Test connection - test_redis_connection() -> bool:
set(), get(), delete(), ...
ping() -> sync                async
---------------------------------------------------------
router = FastAPI.APIRouter()
task_queue = asyncio.Queue()
ThreadPool = ThreadPoolExecutor(max_workers=3)

# LLM task processor (sync) - process_llm_task(task_id: str, prompt: str):

# use best_llt to print completion status
llm_client = LLM call through API + extract result

# worker that runs LLM task processor (async): background_worker(worker_id: int):
    loop = asyncio.get_event_loop()
    get task_id, prompt from task_queue
    result = loop.run_in_executor(
        ThreadPool, functools.partial(process_llm_task, task_id, prompt)
    )
    post task_done()

# Lifespan event for starting background workers -
@router.on_event("startup")
async def on_startup():
    # spawn background workers - store into workers[]
    [asyncio.create_task(background_worker(i)) for i in range(3)]
    # shutdown
    [worker.cancel() for worker in workers]
    await asyncio.gather(*workers, return_exceptions=True)

app = FastAPI(...)

app = FastAPI(...)

# Put everything in
# try, code + return
except Exception as e:
    # return with error - method signature + any variable value

@router.get("/health", tags=["health"], summary="Check API health")
a = ping() using async_redis_client <=> return result, a=ueue_2s

@router.post("/tasks", tags=["Tasks"], summary="Queue new LLM tasks")
async def create_task(prompt: Prompt):
# 1. async_redis_client.incr(task_id)
# 2. r = {
        "task_id": task_id,
        "status": "queued",
        "prompt": prompt[:100],
        "progress": "",
        "created_at": str(time.time()),
        "progress_prev": prompt[:100] if len(prompt) > 100 else prompt
    }

# 2. put task_id, prompt in task_queue & task_id
# 3. return { "task", "status": <queue task message> }

@router.get("/tasks/{task_id}/result", tags=["Tasks"], summary="Get specific task result")
# 1. Task data = async_redis_client.hgetall(f"task:{task_id}")

@router.get("/tasks/{task_id}/result", tags=["Tasks"], summary="Get specific task result")
async def get_task_result(task_id: str):
    # 1. task_data = async_redis_client.hgetall(f"task:{task_id}")

@router.get("/tasks", tags=["Tasks"], summary="Get task status by IDs")
async def get_task_status(task_ids: List[str]):
    # 1. store task_ids in a list of strings
    # 2. results = []
    # 3. for each task_id, get task_data using async_redis_client.hgetall(f"task:{task_id}")
    # 4. store in results[task_id] = task_data
    # 5. return { "results": results, "task_ids": task_ids }

@router.get("/queue/stats", tags=["Queue"], summary="Get queue statistics")
async def get_queue_stats():
    # get all task keys
    task_keys = await async_redis_client.keys("task:*")
    stats = { "queued": 0, "completed": 0, "failed": 0 }
    for k in task_keys:
        data = await async_redis_client.hgetall(k)
        if data["status"] == "unknown":
            stats["queued"] += 1
        elif data["status"] == "completed":
            stats["completed"] += 1
        elif data["status"] == "failed":
            stats["failed"] += 1

    stats["current_queue_size"] = task_queue.qsize()

# Include router in app
app.include_router(router, prefix="/api/v1", tags=["Tasks"])

```
