from contract_service import contract
import asyncio
import logging
from config import *
import httpx

logger = logging.getLogger(__name__)

BLOCK_TRACK_FILE = "last_processed_block.json"

# async def send_discord_notification(message: str):
#     """Send a message to the Discord channel via the webhook."""
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
#             response.raise_for_status()
#     except Exception as e:
#         logger.error(f"Failed to send Discord notification: {str(e)}")

def get_last_processed_block():
    """Retrieve the last processed block number from the file."""
    try:
        with open(BLOCK_TRACK_FILE, 'r') as f:
            data = json.load(f)
            return data.get("last_processed_block", None)
    except FileNotFoundError:
        return None

def store_last_processed_block(block_number):
    """Store the last processed block number in a file."""
    with open(BLOCK_TRACK_FILE, 'w') as f:
        json.dump({"last_processed_block": block_number}, f)

async def handle_pool_created_event(event):
    pool_id = event['args']['poolId']
    pool = contract.functions.pools(pool_id).call()
    logger.info(f"Event {pool[4]})")
    if pool[4]:
        return

    creator = event['args']['creator']
    target_price = event['args']['targetPrice']
    stop_loss = event['args']['stopLoss']
    end_time = event['args']['endTime']

    logger.info(f"Event listener: \
                Pool Created: \
                Pool ID: {pool_id}, \
                    Creator: {creator}, "
                f"Target Price: {target_price}, \
                    Stop Loss: {stop_loss}, \
                        End Time: {end_time}, ")

    # message = (f"New Pool Created!\n"
    #            f"**Pool ID:** {pool_id}\n"
    #            f"**Creator:** {creator}\n"
    #            f"**Target Price:** {target_price}\n"
    #            f"**Stop Loss:** {stop_loss}\n"
    #            f"**End Time:** {end_time}")

    # await send_discord_notification(message)

async def handle_pool_finalized_event(event):
    pool_id = event['args']['poolId']
    final_price = event['args']['finalPrice']
    outcome = event['args']['outcome']

    logger.info(f"Event listener: \
                Pool Finalized: \
                Pool ID: {pool_id}, \
                    Final Price: {final_price}, \
                        Outcome: {outcome}")

    # message = (f"Pool Finalized!\n"
    #            f"**Pool ID:** {pool_id}\n"
    #            f"**Final Price:** {final_price}\n"
    #            f"**Outcome:** {outcome}")

    # await send_discord_notification(message)

async def handle_event(event):
    event_name = event.event
    if event_name == 'PoolCreated':
        await handle_pool_created_event(event)
    elif event_name == 'PoolFinalized':
        await handle_pool_finalized_event(event)
    else:
        logger.warning(f"Event listener: Unhandled event type: {event_name}")

async def event_listener():
    try:
        last_processed_block = get_last_processed_block()
        if last_processed_block is None:
            last_processed_block = 'latest'

        pool_created_filter = contract.events.PoolCreated.create_filter(from_block='latest')
        pool_finalized_filter = contract.events.PoolFinalized.create_filter(from_block='latest')

        while True:
            created_events = pool_created_filter.get_new_entries()
            finalized_events = pool_finalized_filter.get_new_entries()

            for event in created_events:
                await handle_event(event)

            for event in finalized_events:
                await handle_event(event)

            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Error in event listener: {e}")

def start_event_listener():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(event_listener())

if __name__ == "__main__":
    start_event_listener()
