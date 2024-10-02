import discord
from discord.ext import commands, tasks
import logging
import asyncio
from price_monitor import get_current_price, check_pool_conditions
from contract_service import create_pool, finalize_pool
from event_listener import event_listener
from web3 import Web3
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user}')
    print("Bot is online and ready to accept commands.")
    fetch_price.start()
    check_pools_periodically.start()
    asyncio.create_task(event_listener())

@tasks.loop(minutes=1)
async def fetch_price():
    """Fetch the current price every minute and send it to the Discord chat."""
    current_price = await get_current_price()
    if current_price is not None:
        current_price_converted = Web3.from_wei(current_price, 'ether')
        message = f"The current BITCOIN price is ${current_price_converted}."
        channel = discord.utils.get(bot.get_all_channels(), name="price-updates")
        if channel:
            await channel.send(message)
        logger.info(message)

@tasks.loop(minutes=1)
async def check_pools_periodically():
    """Periodically check pool conditions and finalize them if necessary."""
    result = await check_pool_conditions()
    logger.info(result['message'])
    channel = discord.utils.get(bot.get_all_channels(), name="pool-updates")
    if channel:
        await channel.send(result['message'])

@bot.command(name='finalize_pool')
async def finalize_pool_command(ctx, pool_id: int):
    """
    Manually finalize a specific pool by pool ID.
    """
    await ctx.send(f"Attempting to finalize pool {pool_id}...")
    current_price_in_wei = await get_current_price()
    if current_price_in_wei is None:
        await ctx.send("Failed to fetch the current price. Please try again later.")
        return

    txn_hash = finalize_pool(pool_id, current_price_in_wei)
    if txn_hash:
        await ctx.send(f"Pool {pool_id} finalized successfully! Transaction Hash: {txn_hash}")
    else:
        await ctx.send(f"Failed to finalize pool {pool_id}.")


@bot.command(name='create_pool')
async def create_pool_command(ctx):
    """
    Collects parameters from the user and creates a new pool on the blockchain.
    """
    await ctx.send("Let's create a new pool! Please provide the target price in USD (e.g., 1500):")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        target_price_message = await bot.wait_for('message', check=check, timeout=60.0)
        target_price_in_usd = float(target_price_message.content)

        current_price_in_wei = await get_current_price()
        current_price_in_eth = Web3.from_wei(current_price_in_wei, 'ether')

        target_price_in_eth = target_price_in_usd / float(current_price_in_eth)
        target_price_in_wei = Web3.to_wei(target_price_in_eth, 'ether')

        await ctx.send("Please provide the stop loss in USD (e.g., 1200):")
        stop_loss_message = await bot.wait_for('message', check=check, timeout=60.0)
        stop_loss_in_usd = float(stop_loss_message.content)
        stop_loss_in_eth = stop_loss_in_usd / float(current_price_in_eth)
        stop_loss_in_wei = Web3.to_wei(stop_loss_in_eth, 'ether')

        await ctx.send("Please provide the duration of the pool in seconds (e.g., 86400 for 1 day):")
        duration_message = await bot.wait_for('message', check=check, timeout=60.0)
        duration = int(duration_message.content)

        result = create_pool(target_price_in_wei, stop_loss_in_wei, duration)
        if result["status"] == "success":
            await ctx.send(f"{result['message']}")
            logger.info(f"Pool created successfully: {result}")
        else:
            await ctx.send(f"Failed to create pool: {result['message']}")
            logger.error(f"Failed to create pool: {result}")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please try creating the pool again.")
    except Exception as e:
        await ctx.send(f"An error occurred during the pool creation process: {str(e)}")
        logger.error(f"Error creating pool: {str(e)}")


bot.run(DISCORD_BOT)
