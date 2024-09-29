from dotenv import load_dotenv
import os
import json

load_dotenv()

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
ASSET_ID = "bitcoin"

WEB3_PROVIDER = os.getenv("WEB3_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

with open("abi.json", "r") as file:
    CONTRACT_ABI = json.load(file)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
