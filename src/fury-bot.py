#built in
import os
import random
import fileinput
import time
import random

#pip
import discord
from discord.ext import commands
from discord.ext.commands import Bot

#own files
import data.config as config

intents = discord.Intents.all()
#intents.presences = True

#loading token
TOKEN = config.DISCORD_TOKEN_FURY #reading in the token from config.py file



server_channels = {} # Server channel cache

#setting prefix and defining bot
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)
client = discord.Client() #defining client

# LOADING Extentions
bot.remove_command('help')
initial_extensions = [
        'cogs.admin',
        # 'cogs.helix',
        'cogs.help',
        'cogs.misc',
        'cogs.on_message',
        'cogs.set_settings',
        'cogs.on_voice_update'
            ]    

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


#game = discord.Game('Waiting')
#login message
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected')
    guild = discord.utils.get(bot.guilds)#, name=GUILD)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="type !help to start"))
    print('Bot is connected to the following guilds')
    print()
    for g in bot.guilds:
        print(g, g.id)
    print()


#error message if user has not right permissions
# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.errors.CheckFailure):
#             await ctx.send('You can\'t do that. Pleases ask an Admin')


## PANTHEON
#loaded via cogs

#Discontinued projects
# AIR 
# Helix
# Orion


bot.run(TOKEN)

