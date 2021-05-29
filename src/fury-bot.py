import sys
import logging
import traceback

# pip
import discord
from discord.ext import commands

# own files
import log_setup
from environment import PREFIX, TOKEN
import utils
import data.config as config

logger = logging.getLogger("my-bot")

intents = discord.Intents.all()
# intents.presences = True

# loading token
TOKEN = config.DISCORD_TOKEN_FURY  # reading in the token from config.py file

server_channels = {}  # Server channel cache

# setting prefix and defining bot
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)
client = discord.Client()  # defining client

# LOADING Extensions
bot.remove_command('help')
initial_extensions = [
    'cogs.admin',
    # 'cogs.helix',
    'cogs.help',
    'cogs.misc',
    'cogs.on_message',
    'cogs.set_settings',
    'cogs.on_voice_update',
    'cogs.breakout_rooms'
]

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


# game = discord.Game('Waiting')
# login message
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected')
    guild = discord.utils.get(bot.guilds)  # , name=GUILD)

    print(f'Bot is connected to the following guilds:')
    print()
    member_count = 0
    for g in bot.guilds:
        print(f"{g.name} - {g.id} - Members: {g.member_count}")
        member_count += g.member_count
    print()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"{config.PREFIX}help"))


# error message if user has not right permissions
@bot.event
async def on_command_error(ctx, error):
    """
    Overwriting command error handler from discord.py
    """
    print(error)
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You can\'t do that. Pleases ask an Admin')

    elif isinstance(error, commands.errors.CommandNotFound):
        await utils.send_embed(ctx,
                               utils.make_embed(name="I'm sorry, I don't know this command", value=f'`{error}`',
                                                color=discord.Color.orange()))

    logger.warning(f"Command tried: {error}")


@bot.event
async def on_error(function, *args, **kwargs):
    """
    Overwriting error handler from discord.py
    """
    # exception type
    exception = sys.exc_info()[1]
    # traceback text
    tb_text = f'Error in: {function}\n{exception}\nTraceback (most recent call last):\n' \
              + "".join(traceback.format_tb(sys.exc_info()[2])) + f"{exception}"

    print("----------\n")
    print(tb_text)
    logger.error(tb_text)

    # sending message to member when channel creation process fails
    if function == "on_voice_state_update" and isinstance(exception, discord.errors.Forbidden):
        member = args[0]  # member is first arg that is passed in
        # check if it's the error we expect
        if tb_text.find("create_voice_channel") != -1:
            await member.send(
                embed=utils.make_embed(name=f"Something's wrong with my permissions",
                                       value="I can't prepare (create & edit) a channel for you "
                                             "or I can't move you.\n"
                                             "Please check whether a channel was created and inform the server team "
                                             "about that problem.\n I'm sorry! :confused:",
                                       color=discord.Color.red()))


bot.run(TOKEN)

# PANTHEON
# loaded via cogs

# Discontinued projects
# AIR
# Helix
# Orion
