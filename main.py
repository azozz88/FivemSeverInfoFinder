import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from config import BOT_CONFIG, LOGGING_CONFIG, ERROR_MESSAGES, TOKEN
import logging

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SecurityBot')

# تحميل الإضافات
async def load_extensions():
    await bot.load_extension('ticket_system')
    await bot.load_extension('FiveMScanner')

@bot.event
async def on_ready():
    logger.info(f'Bot is ready as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    await bot.change_presence(
        activity=discord.Game(name=BOT_CONFIG['status_message'])
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(ERROR_MESSAGES['command_not_found'])
    else:
        logger.error(f"Error: {str(error)}")
        await ctx.send(ERROR_MESSAGES['general_error'])

# تشغيل البوت
async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())