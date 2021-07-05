import re
from typing import Union, Tuple

import discord
from discord.ext import commands

from environment import PREFIX, CHANNEL_TRACK_LIMIT, MAX_PREFIX_LENGTH
import database.db_models as db_models
import database.access_settings_db as settings_db
import database.access_channels_db as channels_db
import utils as utils

# possible settings switch - returns same value but nothing if key isn't valid
# used to verify that input is correct and to make sure that we always handle the same name internally

settings = {
    "archive": "archive_category",
    "achive": "archive_category",
    "arch": "archive_category",
    "log": "log_channel",
    "prefix": "prefix",

    "pub-channel": "public_channel",
    "public-channel": "public_channel",
    "pub": "public_channel",
    "public": "public_channel",

    "priv-channel": "private_channel",
    "private-channel": "private_channel",
    "priv": "private_channel",
    "private": "private_channel",
}


class Settings(commands.Cog):
    """
    Set / customize default settings
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="add", aliases=["svc", "set-voice", "set-voice-channel"],
        help=f"Register a voice channel that members can join to get an own channel\n\n"
        "__Usage:__\n"
        f"`{PREFIX}add` [_public_ | _private_] [_channel-id_]\n\n"
        "_public_ or _private_ is the option for the channel-type that is created when joining the tracked-channel.\n"
        "This option is - obviously - admin only\n\n"
        f"Aliases: `{PREFIX}svc` `{PREFIX}set-voice [channel type] [channel id]`")
    @commands.has_permissions(administrator=True)
    async def set_voice(self, ctx: commands.Context, setting: str, value: str):
        """
        Add a voice channel setting to the database
        :param ctx: command context
        :param setting: setting to be added like 'public'
        :param value: id or mention the channel to be entered into the database
        """

        # trying to get a corresponding channel / id
        setting = settings[setting]
        channel = utils.get_chan(ctx.guild, value)

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

        tracked_channels = []
        # conversion to set since some keys appear multiple times due to aliases
        for setting in set(settings.values()):
            entries = settings_db.get_all_settings_for(ctx.guild.id, setting)
            if entries:
                tracked_channels.extend(entries)

        pub = "__Public Channels:__\n"
        priv = "__Private Channels:___\n"
        log = "__Log Channel:__\n"
        archive = "__Archive Category:__\n"
        prefix = "__Prefixes:__\n"
        if not tracked_channels:
            emb = utils.make_embed(color=utils.yellow, name="No configuration yet",
                                   value="You didn't configure anything yet.\n"
                                         "Use the help command or try the quick-setup to get started :)")
            await ctx.send(embed=emb)
            return

        for i, elm in enumerate(tracked_channels):  # building strings
            if elm.setting == "public_channel":
                pub += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"

            elif elm.setting == "private_channel":
                priv += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"

            elif elm.setting == "log_channel":
                log += f"`{ctx.guild.get_channel(int(elm.value)).mention}` with ID `{elm.value}`\n"

            elif elm.setting == "archive_category":
                archive += f"`{ctx.guild.get_channel(int(elm.value))}` with ID `{elm.value}`\n"
            elif elm.setting == "prefix":
                prefix += f"`{elm.value}` example `{elm.value}help`\n"

        emby = utils.make_embed(color=utils.blue_light, name="Server Settings",
                                value=f"‌\n"
                                      f"{pub}\n"
                                      f"{priv}\n"
                                      f"{archive}\n"
                                      f"{log}\n"
                                      f"{prefix}")
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

        # get channel setting or setting string
        setting_setting = settings.get(value, None)  # name of setting
        value_setting = utils.extract_id_from_message(value)  # id / value of setting
        if not (setting_setting or value_setting):
            emby = utils.make_embed(color=utils.orange,
                                    name="No valid setting",
                                    value="It seems like you didn't give me a valid channel ID or "
                                          "setting name to work with")
            await ctx.send(embed=emby)
            return

        # all checks passed - removing that entry
        if setting_setting:
            settings_db.del_setting_by_setting(ctx.guild.id, setting_setting)

        elif value_setting:
            settings_db.del_setting_by_value(ctx.guild.id, str(value_setting))

        # channel only applied to setting by value
        channel = ctx.guild.get_channel(value_setting)
        await ctx.send(embed=utils.make_embed(color=utils.green, name="Deleted",
                                              value=f"Removed "
                                                    f"`{channel.name if channel else setting_setting}` from settings"))

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


    @staticmethod
    async def validate_channel(ctx: commands.Context, channel_id: str):

        set_channel = utils.get_chan(ctx.guild, channel_id)

        if set_channel is None:
            await ctx.send(embed=utils.make_embed(name="No valid channel id",
                                                  value="I can't find a channel / category that matches your input.\n"
                                                        "Please make sure that I can see the channel "
                                                        "and that the given id is valid.",
                                                  color=utils.orange))

        return set_channel


    @staticmethod
    async def channel_from_input(ctx, channel_type: str, channel_id: str) -> Union[Tuple[str, str], Tuple[None, None]]:
        """
        Get the channel for a given channel id, send error message if no channel was found\n
        - checks if channel exists\n
        - checks if type matches the given setting\n
        
        :param ctx: discord.Context to send possible help message and to extract guild id
        :param channel_type: channel type searched, like log_channel. Matched with names from settings dict
        :param channel_id: channel id that was given

        :returns: (channel id as string, best way to mention / name channel) if found, else (None, None)
        """
        set_channel = await Settings.validate_channel(ctx, channel_id)

        if set_channel is None:
            return None, None

        # check if channel type and wanted setting match
        if type(set_channel) == discord.TextChannel and channel_type == "log_channel":
            return str(set_channel.id), set_channel.mention

        elif type(set_channel) == discord.CategoryChannel and channel_type == "archive_category":
            return str(set_channel.id), set_channel.name

    @staticmethod
    async def prefix_validation(ctx: commands.Context, new_prefix: str) -> Union[Tuple[str, str], Tuple[None, None]]:
        """
        Validate that a prefix fit the set criteria, send error message if it does not match\n
        Criteria:\n
        - shorter or equal to env variable MAX_PREFIX_LENGTH\n
        - ends on a non-word character like '!'
        
        :param ctx: context of the command, used to send a possible message
        :param new_prefix: string to validate
        
        :returns: (prefix, prefix) if its valid, else (None, None)
        """
        example_prefix = f"A valid prefix would be `{'f' * (MAX_PREFIX_LENGTH - 1)}!` or just `?`"

        # validate length and scheme
        # example: r"^\w{0,3}\W$" (the upper limit can be changed dynamically)
        pattern = re.compile(r"^\w{0," + str(MAX_PREFIX_LENGTH - 1) + r"}\W$")
        if re.search(pattern, new_prefix) is not None:
            return new_prefix, new_prefix  # prefix shall be entered to db and be sent in message

        await ctx.send(embed=utils.make_embed(
            name="Prefix should be short and easy to remember",
            value=f"The length limit for this bot is {MAX_PREFIX_LENGTH - 1} letters or digits, "
                  f"followed by one 'non-word' character like !, ?, ~\n"
                  f"{example_prefix}",
            color=utils.yellow))
        return None, None

    @commands.command(
        name="set", aliases=["sa", "sl", "archive", "log"],
        help=f"Change settings for:\n\n"
             f"__log:__\n"
             f"Channel for log messages\n"
             f"__archive:__\n"
             f"Category linked text channels shall be moved to after linked voice-channel was deleted.\n\n"
             f"__prefix:__\n"
             f"Prefix the bot listens to on your server.\n\n"
             "Usage\n:"
             f"`{PREFIX}set` [_archive_ | _log_] [_channel-id_]\n\n"
             f"`{PREFIX}set` [_prefix_] [_new-prefix_]\n\n"
             "Note that text-channels will only be archived when they contain at least one message, "
             "they'll be deleted otherwise.\n\n"
             "Your setting will be updated if you already set a log / archive.\n\n"
             f"Aliases: `archive`, `log`, `sa`, `sl`\n\n"
             "This option is admin only")
    @commands.has_permissions(administrator=True)
    async def set_setting(self, ctx: commands.Context, setting: str, value: str):

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

        # look if setting name is valid
        setting = setting.lower()  # dict only handles lower case, so do we all the time
        setting_type = settings.get(setting, None)
        nice_string = setting_type.replace('_', ' ')

        if not setting_type:
            await ctx.send(embed=utils.make_embed(name=f"'{setting}' is no valid setting name",
                                                  value="Use the help command to get an overview of possible settings",
                                                  color=utils.yellow))
            return

        # setting is validated, let's see if the value matches the required setting
        value = value.strip()  # just in case
        set_value, set_name = None, None
        if setting_type in ['archive_category', 'log_channel']:
            # trying to get a corresponding channel (id: str, name/ mention: str)
            set_value, set_name = await self.channel_from_input(ctx, setting_type, value)

        if setting_type == "prefix":
            # need to await since it sends the error message if we can't match
            set_value, set_name = await self.prefix_validation(ctx, value)

        # make database entry
        if set_value:

            # check if there is an entry for that setting - toggle it
            session = db_models.open_session()
            entry = settings_db.get_first_setting_for(ctx.guild.id, setting_type, session=session)

            if entry:
                # TODO: SEND REPLY
                entry.value = set_value
                session.add(entry)
                session.commit()

                await ctx.send(embed=utils.make_embed(name=f"Updated setting: {nice_string}",
                                                      value=f"Set to {set_name}",
                                                      color=utils.green))

                return

            settings_db.add_setting(
                guild_id=ctx.guild.id,
                setting=setting_type,
                value=set_value,
                set_by=f"{ctx.author.id}"
            )
            await ctx.send(embed=utils.make_embed(name=f"Added setting: {nice_string}",
                                                  value=f"Set to {set_name}",
                                                  color=utils.green))


def setup(bot):
    bot.add_cog(Settings(bot))
