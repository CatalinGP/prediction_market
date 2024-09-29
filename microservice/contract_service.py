from web3 import Web3
from config import WEB3_PROVIDER, CONTRACT_ADDRESS, CONTRACT_ABI, PRIVATE_KEY
import logging
import json
from dotenv import load_dotenv

logging.basicConfig(
    filename="microservice.log",
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

if not web3.is_connected():
    raise ConnectionError("Failed to connect to the Ethereum network.")

with open("abi.json") as f:
    contract_abi = json.load(f)

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)


def create_pool(target_price: int, stop_loss: int, duration: int) -> dict:
    """
    Creates a pool on the blockchain with the given parameters.

    :param target_price: Target price in wei
    :param stop_loss: Stop loss in wei
    :param duration: Duration in seconds
    :return: Dictionary with transaction details
    """
    try:
        account = web3.eth.account.from_key(PRIVATE_KEY)

        tx = contract.functions.createPool(
            target_price,
            stop_loss,
            duration
        ).build_transaction({
            "chainId": 84532,
            "gas": 3000000,
            "gasPrice": web3.to_wei("20", "gwei"),
            "nonce": web3.eth.get_transaction_count(account.address),
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt.status == 1:
            return {
                "status": "success",
                "message": f"Pool created successfully with transaction hash: {tx_hash.hex()}",
                "target_price": target_price,
                "stop_loss": stop_loss,
            }
        else:
            return {"status": "failed", "message": "Transaction failed."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_pool_details(pool_id):
    """Retrieves the details of a specific pool."""
    try:
        pool = contract.functions.pools(pool_id).call()

        if pool[0] == '0x0000000000000000000000000000000000000000':
            logger.info(f"No pools active or pool {pool_id} does not exist.")
            return "No pools active or pool does not exist."

        return {
            "creator": pool[0],
            "target_price": pool[1] / 10**18,
            "stop_loss": pool[2] / 10**18,
            "end_time": pool[3],
            "is_finalized": pool[4],
            "final_price": pool[5] / 10**18,
            "outcome": pool[6]
        }

    except Exception as e:
        logger.error(f"Error retrieving pool details: {str(e)}")
        return None

def get_dynamic_gas_price():
    base_fee = web3.eth.gas_price
    priority_fee = web3.to_wei('2', 'gwei')
    max_fee_per_gas = base_fee + priority_fee
    return max_fee_per_gas, priority_fee

def finalize_pool(pool_id, current_price):
    """Finalizes a pool on the smart contract."""
    try:
        account = web3.eth.account.from_key(PRIVATE_KEY)
        balance = web3.eth.get_balance(account.address)
        max_fee_per_gas, max_priority_fee_per_gas = get_dynamic_gas_price()

        txn = contract.functions.resolvePool(pool_id, current_price).build_transaction({
            'chainId': 84532,
            'gas': 2000000,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'nonce': web3.eth.get_transaction_count(account.address, 'pending'),
        })

        gas_estimate = web3.eth.estimate_gas({
            'from': account.address,
            'to': contract.address,
            'data': txn['data'],
        })
        total_gas_fee = gas_estimate * max_fee_per_gas

        if balance < total_gas_fee:
            logger.error(f"Insufficient funds for gas. Required: {web3.from_wei(total_gas_fee, 'ether')} ETH, Available: {web3.from_wei(balance, 'ether')} ETH")
            return None

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        txn_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        logger.info(f"Pool {pool_id} finalized. Transaction hash: {txn_hash.hex()}")
        return txn_hash.hex()

    except Exception as e:
        logger.error(f"Error finalizing pool {pool_id}: {str(e)}")
        if hasattr(e, 'response') and 'error' in e.response:
            logger.error(f"RPC Error: {e.response['error']}")
        return None
