import discord
import json
import os
import logging
from discord.ext import commands

logger = logging.getLogger("discord")

with open('private_data.json') as file:
    botKey = json.loads(file.read())['bot_key']
    
intents = discord.Intents.default()
bot = commands.Bot("",intents=intents)

@bot.event
async def setup_hook():
    for file in os.listdir('cmds'):
        if file.endswith('.py'):
            await bot.load_extension('cmds.' + file[:-3])
            logger.info(f"Loaded {file[:-3]}")
    await bot.tree.sync()

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    custom_status = "I love men" #f'in {len(bot.guilds):,} servers'
    await bot.change_presence(activity=discord.CustomActivity(name=custom_status))
    logger.info(f'Set status to "{custom_status}"')

@bot.event
async def on_message(message: discord.Message):
    pass

bot.run(botKey)