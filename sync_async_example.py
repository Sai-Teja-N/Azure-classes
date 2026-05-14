import time
import asyncio

# ==========================================
# 1. SYNCHRONOUS APPROACH
# ==========================================
def sync_task(name):
    print(f"  [{name}] Started waiting...")
    time.sleep(2) # Blocks the entire program for 2 seconds
    print(f"  [{name}] Finished!")

def run_sync():
    print("--- Running Synchronously ---")
    start_time = time.time()
    
    # These run one after the other
    sync_task("Task A")
    sync_task("Task B")
    
    end_time = time.time()
    print(f"Sync Total Time: {end_time - start_time:.2f} seconds\n")

# ==========================================
# 2. ASYNCHRONOUS APPROACH
# ==========================================
async def async_task(name):
    print(f"  [{name}] Started waiting...")
    await asyncio.sleep(2) # Pauses this task, lets others run
    print(f"  [{name}] Finished!")

async def run_async():
    print("--- Running Asynchronously ---")
    start_time = time.time()
    
    # asyncio.gather runs both tasks concurrently
    await asyncio.gather(
        async_task("Task A"),
        async_task("Task B")
    )
    
    end_time = time.time()
    print(f"Async Total Time: {end_time - start_time:.2f} seconds")

# ==========================================
# EXECUTE BOTH
# ==========================================
if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
