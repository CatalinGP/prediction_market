import hvac
import os

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

def get_private_key():
    """Retrieve the private key securely from HashiCorp Vault"""
    try:
        secret_response = client.secrets.kv.v2.read_secret_version(path='ethereum')
        private_key = secret_response['data']['data']['PRIVATE_KEY']
        return private_key
    except Exception as e:
        raise ValueError(f"Error retrieving private key: {e}")
