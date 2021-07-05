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
import database.db_models as db
import database.access_settings_db as settings_db

logger = logging.getLogger("my-bot")

intents = discord.Intents.all()
# intents.presences = True


# inspired by https://github.com/Rapptz/RoboDanny
def _prefix_callable(_bot: commands.Bot, msg: discord.Message):
    user_id = _bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    if msg.guild is None:  # we're in DMs
        base.append(PREFIX)
        return base

    # look if there are custom prefix settings here
    entries = settings_db.get_all_settings_for(msg.guild.id, "prefix")
    if entries is not None:
        prefixes = [entry.value for entry in entries]
        base.extend(prefixes)
    else:  # nope boring, using standard prefix
        base.append(PREFIX)
    return base


# setting prefix and defining bot
bot = commands.Bot(command_prefix=_prefix_callable, intents=intents)


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
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help"))


# error message if user has not right permissions
@bot.event
async def on_command_error(ctx, error):
    """
    Overwriting command error handler from discord.py
    """
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You can\'t do that. Pleases ask an Admin')

    elif isinstance(error, commands.errors.CommandNotFound):
        await utils.send_embed(ctx,
                               utils.make_embed(name="I'm sorry, I don't know this command", value=f'`{error}`',
                                                color=discord.Color.orange()))

    logger.warning(f"Command tried: {error}")


# TODO recreate 'normal' print stack-trace... disable custom handling until then
# @bot.event
# async def on_error(function, *args, **kwargs):
#     """
#     Overwriting error handler from discord.py
#     """
#     # exception type
#     exception = sys.exc_info()[1]
#     # traceback text
#     tb_text = f'Error in: {function}\n{exception}\nTraceback (most recent call last):\n' \
#               + "".join(traceback.format_tb(sys.exc_info()[2])) + f"{exception}"
#
#     print("----------\n")
#     print(tb_text)
#     logger.error(tb_text)
#
#     # sending message to member when channel creation process fails
#     if function == "on_voice_state_update" and isinstance(exception, discord.errors.Forbidden):
#         member = args[0]  # member is first arg that is passed in
#         # check if it's the error we expect
#         if tb_text.find("create_voice_channel") != -1:
#             await member.send(
#                 embed=utils.make_embed(name=f"Something's wrong with my permissions",
#                                        value="I can't prepare (create & edit) a channel for you "
#                                              "or I can't move you.\n"
#                                              "Please check whether a channel was created and inform the server team "
#                                              "about that problem.\n I'm sorry! :confused:",
#                                        color=discord.Color.red()))


# Here we load our extensions(cogs) listed above in [initial_extensions]
# and start the bot
if __name__ == '__main__':
    # LOADING Extensions
    bot.remove_command('help')
    initial_extensions = [
        'cogs.admin',
        # 'cogs.helix',
        'cogs.help',
        'cogs.misc',
        'cogs.on_message',
        'cogs.set_settings',
        'cogs.quick_setup',
        'cogs.on_voice_update',
        'cogs.breakout_rooms'
    ]

    # load extensions - must happen before migration try
    # modules will init the database, not the bot itself
    for extension in initial_extensions:
        bot.load_extension(extension)

    bot.run(TOKEN)

# PANTHEON
# loaded via cogs

# Discontinued projects
# AIR
# Helix
# Orion
