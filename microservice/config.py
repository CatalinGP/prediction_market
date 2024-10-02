from dotenv import load_dotenv
import os
import json

load_dotenv()

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
ASSET_ID = "bitcoin"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
WEB3_PROVIDER = os.getenv("WEB3_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WEB3_SOCK_PROVIDER = os.getenv("WEB3_SOCKET_URL")
DISCORD_BOT = os.getenv("DISCORD_BOT")
with open("abi.json", "r") as file:
    CONTRACT_ABI = json.load(file)

