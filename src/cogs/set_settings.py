# built in
import os
import time
from typing import Union

import sql_utils as sqltils

# pip
import discord
from discord.ext import commands

# own files
from environment import PREFIX, CHANNEL_TRACK_LIMIT
import database.db_models as db_models
import database.access_settings_db as settings_db
import database.access_channels_db as channels_db
import utils as utils

global db_file
db_file = "data/fury1.db"  # variables will be gone with the next update 
SQL_VERSION = 1


class Settings(commands.Cog):
    """
    Set / customize default settings
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="svc", aliases=["set-voice", "set-voice-channel"],
                      help=f"Register a voice channel that members can join to get an own channel\n\n"
        "__Usage:__\n"
        f"`{PREFIX}svc` [_public_ | _private_] [_channel-id_]\n\n"
        "_public_ or _private_ is the option for the channel-type that is created when joining the tracked-channel.\n"
        "This option is - obviously - admin only\n\n"
        f"Aliases: `{PREFIX}set-voice [channel type] [channel id]`")
    @commands.has_permissions(administrator=True)
    async def set_voice(self, ctx: commands.Context, setting: str, value: str):
        """
        Add a voice channel setting to the database
        :param ctx: command context
        :param setting: setting to be added like 'public'
        :param value: id or mention the channel to be entered into the database
        """

        # channel to be returned with dict
        # cache variable - the function would be called for each key if we'd place it in each tuple of the dict
        _channel = utils.get_chan(ctx.guild, value)

        # 'translation' dict
        # used to verify that input is correct and to make sure that we always handle the same name internally
        settings = {
            "pub-channel": ("public_channel", _channel),
            "public-channel": ("public_channel", _channel),
            "pub": ("public_channel", _channel),
            "public": ("public_channel", _channel),

            "priv-channel": ("private_channel", _channel),
            "private-channel": ("private_channel", _channel),
            "priv": ("private_channel", _channel),
            "private": ("private_channel", _channel),
        }

        # trying to get a corresponding channel / id
        setting, channel = settings[setting]

        # if channel is "None" this means that there is no such setting or no such channel for it
        # -> ensures that the process of getting a correct setting has worked
        if channel is None:
            emby = utils.make_embed(
                color=discord.Color.orange(),
                name="Can't get setting",
                value="Please ensure that you've entered a valid setting and channel-id for that setting.")
            await ctx.send(embed=emby)
            return

        # if channel type is not voice channel
        if type(channel) is not discord.VoiceChannel:
            embed = utils.make_embed(
                name='Not a voice channel',
                value=f"The channel {channel.name} is no voice channel, please enter a valid channel-id",
                color=utils.yellow
            )
            await ctx.send(embed=embed)
            return

        # Settings won't be stored if max watched channels are reached
        # -> searching for amount of matching entries
        entries = settings_db.get_all_settings_for(ctx.guild.id, setting)
        if entries and len(entries) >= CHANNEL_TRACK_LIMIT:
            emby = utils.make_embed(
                color=utils.orange, name="Too many entries",
                value=f"Hey, you can't make me watch more than {CHANNEL_TRACK_LIMIT} channels for this setting\n"
                      f"If you wanna change the channels I watch use `{PREFIX}ds [channel-id]` "
                      f"to remove a channel from your settings")

            await ctx.send(embed=emby)
            return

        # check if channel was already given to track
        session = db_models.open_session()
        entry: Union[db_models.Settings, None] = settings_db.get_setting_by_value(ctx.guild.id, channel.id, session)

        # if channel is already registered - update
        if entry:
            entry.setting = setting

            session.add(entry)
            session.commit()

        # create new entry, channel not tracked yet
        else:
            # write entry to db
            settings_db.add_setting(
                guild_id=ctx.guild.id,
                setting=setting,
                value=channel.id,
                set_by=ctx.author.id,
            )

        emby = utils.make_embed(
            color=utils.green, name="Success", value=f"Set {channel.name} as {setting.replace('_', ' ')}")
        await ctx.send(embed=emby)

    @commands.command(name="settings", aliases=["gs", "get-settings"],
                      help=f"Get a list of all 'watched' channels as well as all other settings\n\n"
                           f"Aliases: `gs`, `get-settings` ")
    @commands.has_permissions(kick_members=True)
    async def get_settings(self, ctx):
        """
        prints setting on guild
        """

        tracked_channels = [*settings_db.get_all_settings_for(ctx.guild.id, "public_channel"),
                            *settings_db.get_all_settings_for(ctx.guild.id, "private_channel"),
                            *settings_db.get_all_settings_for(ctx.guild.id, "archive_category"),
                            *settings_db.get_all_settings_for(ctx.guild.id, "log_channel")]

        pub = "__Public Channels:__\n"
        priv = "__Private Channels:___\n"
        log = "__Log Channel:__\n"
        archive = "__Archive Category:__\n"
        for i, elm in enumerate(tracked_channels):  # building strings
            if elm.setting == "public_channel":
                pub += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"

            elif elm.setting == "private_channel":
                priv += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"

            elif elm.setting == "log_channel":
                log += f"`{ctx.guild.get_channel(int(elm.value)).mention}` with ID `{elm.value}`\n"

            elif elm.setting == "archive_category":
                archive += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"

        emby = utils.make_embed(color=utils.blue_light, name="Server Settings",
                                value=f"‌\n"
                                      f"{pub}\n"
                                      f"{priv}\n"
                                      f"{archive}\n"
                                      f"{log}")
        await ctx.send(embed=emby)

    @commands.command(name="delete-setting", aliases=["ds"],
                      help=f"Remove a setting for your guild.\n\n"
                           f"Usable to delete:\n"
                           f"- channels from the list of 'watched' channels\n"
                           f"- the archive category\n"
                           f"- the log channel\n"
                           "This command will only clear the setting from the bots database!\n"
                           f"It will _not_ delete anything on your server.\n\n"
                           f"Usage: `{PREFIX}ds` [_channel-id_]\n\n"
                           f"Get a list of all watched channels with `{PREFIX}gs`\n "
                           f"Aliases: `ds`")
    @commands.has_permissions(administrator=True)
    async def delete_settings(self, ctx: commands.Context, value: str):
        """
        remove tracked channel from database

        :param ctx: command context
        :param value: id of the channel to be deleted
        """
        if not value:
            emby = utils.make_embed(
                color=utils.orange,
                name="No input",
                value=f"This function requires exactly one input:\n"
                      "`channel-id` please give a valid channel ID as argument to remove that channel from"
                      "the list of watched channels.\n"
                      f"You can get a list of all watched channels with `{PREFIX}gs`")

            await ctx.send(embed=emby)
            return

        channel_id = utils.extract_id_from_message(value)
        if not channel_id:

            emby = utils.make_embed(color=utils.orange,
                                    name="No valid channel ID",
                                    value="It seems like you didn't give me a valid channel ID to work with")
            await ctx.send(embed=emby)
            return

        # all checks passed - removing that entry
        settings_db.del_setting_by_value(ctx.guild.id, channel_id)

        channel = ctx.guild.get_channel(channel_id)
        await ctx.send(embed=utils.make_embed(color=utils.green, name="Deleted",
                                              value=f"Removed "
                                                    f"`{channel.name if channel else channel_id}` from settings"))

    # command to set-edit-vc permissions
    @commands.command(name='allow-edit', aliases=['al', 'ae'],
                      help=f'Change whether the name of created public channels can be edited by the channel creator.\n'
                           'Arguments: [_yes_ | _no_]\n'
                           'Default is _no_\n'
                           f"Aliases: `al`, `as`\n\n"
                           f"This command is admin only.")
    @commands.has_permissions(administrator=True)
    async def edit_channel(self, ctx, value: str):
        settings = {'yes': 1,
                    'no': 0}

        yes_or_no = settings[value.lower()]
        if not yes_or_no:
            emby = utils.make_embed(color=discord.Color.orange(),
                                    name="Missing argument",
                                    value=f"Please enter `yes` or `no` as argument.")
            await ctx.send(embed=emby)
            return

        session = db_models.open_session()
        entry = settings_db.get_first_setting_for(ctx.guild.id, "allow_public_rename", session=session)

        # edit entry if exists
        if entry:
            entry.value = str(yes_or_no)
            entry.is_active = True  # set to true because it should be active if changed
            session.add(entry)
            session.commit()

        else:
            settings_db.add_setting(
                guild_id=ctx.guild.id,
                setting="allow_public_rename",
                value=str(yes_or_no),
                set_by=str(ctx.author.id)
            )

        emby = utils.make_embed(color=utils.green,
                                name="Success",
                                value=f'The channel creator {"can" if yes_or_no else "can _not_"} '
                                      f'edit the name of a created public channel\n',
                                footer="Note that this setting has no affect on private channels")
        await ctx.send(embed=emby)

    @commands.command(
        name="set", aliases=["sa", "sl", "archive", "log"],
        help=f"Change settings for:\n\n"
             f"__log:__\n"
             f"Channel for log messages\n"
             f"__archive:__\n"
             f"Category linked text channels shall be moved to after linked voice-channel was deleted.\n\n"
             "Usage\n:"
             f"`{PREFIX}set` [_archive_ | _log_] [_channel-id_]\n\n"
             "Note that text-channels will only be archived when they contain at least one message, "
             "they'll be deleted otherwise.\n\n"
             "Your setting will be updated if you already set a log / archive.\n\n"
             f"Aliases: `archive`, `log`, `sa`, `sl`\n\n"
             "This option is admin only")
    @commands.has_permissions(administrator=True)
    async def set_archive(self, ctx: commands.Context, setting: str, value: str):

        # async def set_archive(self, ctx: commands.Context, setting: str, value: str):
        if not setting:
            msg = ("Please ensure that you've entered a valid setting \
                                and channel-id or role-id for that setting.")
            emby = utils.make_embed(color=discord.Color.orange(), name="Can't get setting", value=msg)
            await ctx.send(embed=emby)

            return

        if not value:
            msg = ("Please ensure that you've entered a valid setting \
                                            and channel-id or role-id for that setting.")
            emby = utils.make_embed(color=discord.Color.orange(), name="Can't get setting", value=msg)
            await ctx.send(embed=emby)

            return

        # possible settings switch - returns same value but nothing if key isn't valid
        settings = {
            "archive": "archive_category",
            "achive": "archive_category",
            "arch": "archive_category",
            "log": "log_channel"
        }

        set_channel = utils.get_chan(ctx.guild, value)

        # trying to get a corresponding channel / id
        setting_type = settings[setting]

        # if value is "None" this means that there is no such setting or no such value for it
        # checking if keyword matches the entered channel type
        # -> ensures that the process of getting a correct setting has worked

        text = ""
        if type(set_channel) == discord.TextChannel and setting_type == "log_channel":
            text = "log channel"

        elif type(set_channel) == discord.CategoryChannel and setting_type == "archive_category":
            text = "archive category"

        # set channels
        if text:

            # check if not none
            session = db_models.open_session()
            entry = settings_db.get_first_setting_for(ctx.guild.id, setting_type, session=session)

            if entry:
                # TODO: SEND REPLY
                entry.value = setting_type
                session.add(entry)
                session.commit()

                await ctx.send(embed=utils.make_embed(name=f"Updated setting: {text}",
                                                      value=f"Set to {set_channel.name}",
                                                      color=utils.green))

                return

            settings_db.add_setting(
                guild_id=ctx.guild.id,
                setting=setting_type,
                value=set_channel.id,
                set_by=f"{ctx.author.id}"
            )
            await ctx.send(embed=utils.make_embed(name=f"Added setting: {text}",
                                                  value=f"Set to {set_channel.name}",
                                                  color=utils.green))


def setup(bot):
    bot.add_cog(Settings(bot))
