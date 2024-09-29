from scheduler import start_scheduler
from fastapi import FastAPI, HTTPException
from contract_service import create_pool, get_pool_details, finalize_pool
from price_monitor import check_pool_conditions
from pydantic import BaseModel
import uvicorn
from event_listener import event_listener
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting WebSocket event listener...")
    loop = asyncio.get_event_loop()
    listener_task = loop.create_task(event_listener())
    start_scheduler()
    yield
    print("Shutting down WebSocket event listener...")
    listener_task.cancel()

app = FastAPI(lifespan=lifespan)

class PoolData(BaseModel):
    target_price: int
    stop_loss: int
    duration: int

class PoolRequest(BaseModel):
    target_price: float
    stop_loss: float
    duration: int

class FinalizeRequest(BaseModel):
    pool_id: int
    current_price: float

@app.post("/create_pool")
async def create_pool_route(pool_data: PoolData):
    result = create_pool(
        pool_data.target_price * 10**18,
        pool_data.stop_loss * 10**18,
        pool_data.duration * 10**18
    )

    if result["status"] == "success":
        return result
    elif result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["message"])
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@app.get("/get-pool/{pool_id}")
async def get_pool(pool_id: int):
    """Endpoint to get details of a specific pool."""
    pool_details = get_pool_details(pool_id)
    if pool_details:
        return pool_details
    else:
        raise HTTPException(status_code=404, detail="Pool not found")

@app.post("/check-conditions/{pool_id}")
async def check_conditions_route(pool_id: int):
    """Endpoint to check and finalize pool conditions manually."""
    try:
        result = await check_pool_conditions(pool_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking conditions: {str(e)}")

@app.post("/finalize-pool")
async def finalize_existing_pool(request: FinalizeRequest):
    """Endpoint to manually finalize a pool."""
    current_price = int(request.current_price * 10**18)
    txn_hash = finalize_pool(request.pool_id, current_price)
    if txn_hash:
        return {"message": "Pool finalized successfully", "transaction_hash": txn_hash}
    else:
        raise HTTPException(status_code=500, detail="Failed to finalize pool")

@app.get("/logs")
async def get_logs():
    """Endpoint to fetch the latest logs from the microservice."""
    try:
        with open("microservice.log", "r") as log_file:
            logs = log_file.readlines()[-50:]
            return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

if __name__ == "__main__":
    # start_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=8000)
