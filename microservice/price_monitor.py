import httpx
from contract_service import get_pool_details, finalize_pool, contract
from config import COINGECKO_API_URL, ASSET_ID
import logging
import time
from web3 import Web3

logger = logging.getLogger(__name__)

async def get_current_price():
    """Fetch the current price of the asset from CoinGecko API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{COINGECKO_API_URL}/simple/price", params={
                'ids': ASSET_ID,
                'vs_currencies': 'usd'
            })
            response.raise_for_status()
            price = response.json()[ASSET_ID]['usd']
            logger.info(f"Fetched current price: ${price}")
            price_in_wei = Web3.to_wei(price, 'ether')
            return price_in_wei
    except Exception as e:
        logger.error(f"Error fetching price: {str(e)}")
        return None

def get_active_pools():
    """Retrieve active pools from the smart contract using Web3.py."""
    try:
        pool_ids = contract.functions.getActivePools().call()

        active_pools = []
        for pool_id in pool_ids:
            pool_details = get_pool_details(pool_id)
            if pool_details:
                active_pools.append({
                    "pool_id": pool_id,
                    "tp": pool_details['target_price'],
                    "sl": pool_details['stop_loss'],
                    "end_time": pool_details['end_time']
                })

        logger.info(f"Retrieved active pools: {active_pools}")
        return active_pools
    except Exception as e:
        logger.error(f"Error retrieving active pools: {str(e)}")
        return []

async def check_pool_conditions(pool_id=None):
    """Checks the conditions of active pools and finalizes them if necessary."""
    try:
        current_price_in_wei = await get_current_price()
        if current_price_in_wei is None:
            return {"status": "error", "message": "Failed to fetch current price."}

        if pool_id is None:
            active_pools = get_active_pools()
        else:
            active_pools = [{"pool_id": pool_id, \
                             "tp": get_pool_details(pool_id)['target_price'], \
                                "sl": get_pool_details(pool_id)['stop_loss'], \
                                    "end_time": get_pool_details(pool_id)['end_time']}]

        for pool in active_pools:
            pool_details = get_pool_details(pool['pool_id'])
            if pool_details['is_finalized']:
                logger.info(f"Pool {pool['pool_id']} is already finalized. Skipping...")
                continue

            target_price = pool_details['target_price']
            stop_loss = pool_details['stop_loss']

            if current_price_in_wei >= target_price:
                txn_hash = finalize_pool(pool['pool_id'], current_price_in_wei)
                logger.info(f"Pool {pool['pool_id']} finalized: Target price reached. Txn Hash: {txn_hash}")
                return {"message": "Pool finalized with target price reached", "transaction_hash": txn_hash}
            elif current_price_in_wei <= stop_loss:
                txn_hash = finalize_pool(pool['pool_id'], current_price_in_wei)
                logger.info(f"Pool {pool['pool_id']} finalized: Stop loss reached. Txn Hash: {txn_hash}")
                return {"message": "Pool finalized with stop loss hit", "transaction_hash": txn_hash}
            elif pool_details['end_time'] <= int(time.time()):
                txn_hash = finalize_pool(pool['pool_id'], current_price_in_wei)
                logger.info(f"Pool {pool['pool_id']} finalized: End time reached. Txn Hash: {txn_hash}")
                return {"message": "Pool finalized due to end time", "transaction_hash": txn_hash}
            else:
                logger.info(f"Conditions not met yet for pool {pool['pool_id']}. Current price: {Web3.from_wei(current_price_in_wei, 'ether')} $")

        return {"message": "All active pools checked. No conditions met."}
    except Exception as e:
        logger.error(f"Error checking and finalizing pools: {str(e)}")
        return {"status": "error", "message": str(e)}
