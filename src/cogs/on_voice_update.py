from typing import Union, Tuple, List, Dict
import random
import time

import discord
from discord.ext import commands

from environment import PREFIX, CHANNEL_TRACK_LIMIT
import database.db_models as db
import database.access_settings_db as settings_db
import database.access_channels_db as channels_db
import utils as utl


async def make_channel(voice_state: discord.VoiceState, member: discord.Member, bot_member: discord.Member,
                       voice_overwrites: Dict[Union[discord.Member, discord.Role], discord.PermissionOverwrite],
                       vc_name="voice-channel", tc_name="text-channel", channel_type="public") -> Tuple[
                       discord.VoiceChannel, discord.TextChannel]:
    """
    Method to create a voice-channel with linked text-channel logging to DB included\n
    -> VCs created with this method are meant to be deleted later on, therefore they're logged to DB

    :param voice_state: To detect which VC the member is in
    :param member: To access guild and give member TC access permissions
    :param bot_member: Bot as member to enable access on all created channels
    :param voice_overwrites: To give member extra permissions in the VC and TC (bot permissions will be added / edited)
    :param vc_name: Voice Channel name
    :param tc_name: Text Channel name
    :param channel_type: For SQL-logging can be "public" or "private"

    :returns: Created Text and VoiceChannel Objects
    """
    # TODO handle error on creation - especially admin permission errors
    # if ctx.me.guild_permissions.administrator...
    
    # add bot to voice channel overwrites to ensure that bot can mange the channel
    bot_overwrites: Union[discord.PermissionOverwrite, None] = voice_overwrites.get(bot_member, None)
    # check if some configurations for bot were made - update overwrites accordingly
    if bot_overwrites is not None:
        bot_overwrites.update(view_channel=True, connect=True)
    else:
        voice_overwrites[bot_member] = discord.PermissionOverwrite(view_channel=True, connect=True)

    # create channels
    v_channel: discord.VoiceChannel = await member.guild.create_voice_channel(
        vc_name, category=voice_state.channel.category, overwrites=voice_overwrites)

    t_channel: discord.TextChannel = await member.guild.create_text_channel(
        tc_name, category=voice_state.channel.category,
        overwrites={member: discord.PermissionOverwrite(view_channel=True),
                    bot_member: discord.PermissionOverwrite(view_channel=True),
                    member.guild.default_role: discord.PermissionOverwrite(view_channel=False)})

    # add channels to database
    channels_db.add_channel(v_channel.id, t_channel.id, member.guild.id, channel_type, v_channel.category.id)

    return v_channel, t_channel


def is_create_channel(guild: discord.Guild, channel: discord.VoiceChannel) -> bool:
    return True if settings_db.get_setting(guild.id, "create_channel", str(channel.id)) else False


channel_names = {"public_channel": [["╠{0}'s discussion", "{0}'s discussion"],
                            ["╠{0}'s voice channel", "{0}'s text channel"],
                            ["╠{0}'s room", "{0}'s room"],
                            ["╠{0}'s open talk", "{0}'s open talk"],
                            ["╠{0}'s bar", "{0}'s bar"],
                            ["╠{0}'s public office", "{0}'s public office"],
                            ["╠{0}'s pool", "{0}'s pool"],
                            ["╠{0}'s bench", "{0}'s bench"],
                            ["╠{0}'s couch", "{0}'s couch"],
                            ["╠{0}'s channel", "{0}'s channel"],
                            ],

                 "private_channel": [["╠{0}'s private discussion", "{0}'s private discussion"],
                             ["╠{0}'s private fellowship", "{0}'s private fellowship"],
                             ["╠{0}'s private room", "{0}'s private room"],
                             ["╠{0}'s elite room", "{0}'s elite room"],
                             ["╠{0}'s regular table", "{0}'s regular table"],
                             ["╠{0}'s private haven", "{0}'s private haven"],
                             ["╠{0}'s private garden", "{0}'s private garden"],
                             ]
                 }


async def create_new_channels(member: discord.Member,
                              after: discord.VoiceState,
                              channel_type: str,
                              bot_member: discord.Member) -> Tuple[discord.VoiceChannel, discord.TextChannel]:
    """
    :param member: member that issued the creation
    :param after: VoiceState that represents the state after the update
    :param channel_type: string that describes the type 'public_channel', 'private_channel'
    :param bot_member: needed to add bot itself to possibly hidden channel

    :returns: references to created voice and text channels
    """

    # check if creator is allowed to rename a public channel
    allowed_to_edit = settings_db.get_first_setting_for(member.guild.id, "allow_public_rename")

    # get channel names from dict above
    new_channel_name = random.choice(channel_names[channel_type])

    # default overwrites for new channel
    voice_channel_permissions = after.channel.category.overwrites

    # overwriting permissions if channel shall be private
    if channel_type == 'private_channel':

        # prohibit everybody from joining except creator, give creator channel edit permissions
        voice_channel_permissions = {
            member.guild.default_role: discord.PermissionOverwrite(connect=False),
            member: discord.PermissionOverwrite(connect=True,
                                                manage_channels=True,
                                                manage_permissions=True)
        }

    # set extra permissions for creator if creators are allowed to edit public channels on this server
    elif allowed_to_edit and int(allowed_to_edit.value):
        voice_channel_permissions[member] = discord.PermissionOverwrite(connect=True,
                                                                        manage_channels=True)

    # add bot to channel so the bot can see and manage this channel without administrator
    voice_channel_permissions[bot_member] = discord.PermissionOverwrite(view_channel=True, connect=True)

    # issue creation of channels
    voice_channel, text_channel = await make_channel(after, member, bot_member, voice_channel_permissions,
                                                     vc_name=new_channel_name[0].format(member.display_name),
                                                     tc_name=new_channel_name[1].format(member.display_name),
                                                     channel_type=channel_type)

    return voice_channel, text_channel


async def delete_text_channel(t_channel: discord.TextChannel, bot: commands.Bot,
                              archive=None) -> Union[discord.TextChannel, None]:
    """
    Checks whether channel shall be archived or deleted and executes that action

    Returns edited channel or None if channel was deleted
    """
    # if archive is given and channel is not empty: move to archive
    if archive and await is_message_in_channel():

        await t_channel.edit(category=archive,
                             reason="Connected voice channel is empty, archive channel with messages",
                             overwrites=archive.overwrites)
        return t_channel

    # delete channel
    await t_channel.delete(reason="Channel is empty and not needed anymore")
    return None


async def clean_after_exception(voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel,
                                bot: commands.Bot,
                                archive=None, log_channel=None):
    """ Cleanup routine that handles the deletion / activation of a voice- and text-channel"""
    await voice_channel.delete(reason="An error occurred - user most likely left the channel during the process")
    await delete_text_channel(text_channel, bot, archive=archive)
    if log_channel:
        log_channel.send(
            embed=utl.make_embed(
                name="Warning",
                value="An error occurred - user most likely left the voice during the channels were set up.\n"
                      "Cleanup finished.",
                color=utl.orange
            )
        )


def generate_text_channel_overwrite(
        voice_channel: discord.VoiceChannel,
        bot_member: discord.Member) -> Dict[Union[discord.Role, discord.Member], discord.PermissionOverwrite]:
    """
    Generates overwrites for linked text-channels\n
    Gives read/ write permission to:\n
    - roles that are registered as allowed in the settings
    - members that are currently in the voice channel
    - the bot member creating that channel

    Prohibits guilds default role from accessing the channel

    :param voice_channel: parent voice channel to create text channel overwrites for
    :param bot_member: needed to add bot itself to hidden channel

    :returns: overwrites dictionary ready to apply
    """

    guild: discord.Guild = voice_channel.guild

    # get roles that have permissions to see all private TCs - like mods or bots
    allowed_roles: List[db.Settings] = settings_db.get_all_settings_for(guild.id, "view_tc_role")

    # roles that are allowed to see and write in channel by default
    role_overwrites = {
        guild.get_role(int(r.value)): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        for r in allowed_roles} if allowed_roles else {}

    # exclude default role to make channel private
    role_overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)

    # overwrites that contain permissions for all member currently in the voice channel
    member_overwrites = {
        m: discord.PermissionOverwrite(view_channel=True, send_messages=True) for m in voice_channel.members
    }

    # add bot user self to channel, so bot can access the channel at any time
    member_overwrites[bot_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # return joined dicts
    return {**role_overwrites, **member_overwrites}


async def update_channel_overwrites(after_channel: discord.VoiceChannel,
                                    created_channel: db.CreatedChannels, bot_member: discord.Member):
    # get new overwrites for text channel
    overwrites = generate_text_channel_overwrite(after_channel, bot_member)
    # get linked text channel
    linked_channel: discord.TextChannel = after_channel.guild.get_channel(created_channel.text_channel_id)
    # TODO: logging if text channel not exists
    if linked_channel:
        await linked_channel.edit(overwrites=overwrites)


async def send_welcome_message(text_channel: discord.TextChannel, linked_vc: discord.VoiceChannel):
    await text_channel.send(
        embed=utl.make_embed(
            name='Welcome to your own private channel!',
            value=f'Hey, this channel is only visible for people that are in your voice chat:\n'
                  f'{linked_vc.mention}\n'
                  "You can use this channel to share conversation related stuff, "
                  "use bot commands or just for other things.\n"
                  'Have fun!',
            footer='Please note that this channel will be removed '
                   'when everyone has left the affiliated voice channel.',
            color=utl.green
        )
    )


class VCCreator(commands.Cog):
    # Codename: PANTHEON
    """
    A function that creates custom voice channels if triggered
     - Creates a dedicated voice-channel
     - Creates a private linked text-channel
     - Members will be added and removed to text-channel
    - There is an option for a customizable /private voice-channel
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):

        # this is the case that a state update happens that is not a channel switch, but a mute or something like that
        if before.channel and after.channel and before.channel.id == after.channel.id:
            return

        # as shorthand - we'll need this a few times
        guild: discord.Guild = member.guild
        bot_member_on_guild: discord.Member = guild.get_member(self.bot.user.id)
        after_channel: Union[discord.VoiceChannel, None] = after.channel
        before_channel: Union[discord.VoiceChannel, None] = before.channel

        # open db session
        session = db.open_session()

        # get settings for archive and log channel
        log_entry = settings_db.get_first_setting_for(guild.id, "log_channel", session)  # get entry if exists
        archive_entry = settings_db.get_first_setting_for(guild.id, "archive_category", session)

        # get channels from entries if existing
        log_channel: Union[discord.TextChannel, None] = guild.get_channel(int(log_entry.value)) if log_entry else None
        archive_category: Union[discord.CategoryChannel, None] = guild.get_channel(
            int(archive_entry.value)) if archive_entry else None

        # check if member has a voice channel after the state update
        # could trigger the creation of a new channel or require an update for an existing one
        if after_channel:

            # check db if channel is a channel that was created by the bot
            created_channel: Union[db.CreatedChannels, None] = channels_db.get_voice_channel_by_id(after_channel.id, session)

            # check if joined (after) channel is a channel that triggers a channel creation
            tracked_channel = settings_db.get_setting_by_value(guild.id, after_channel.id, session)

            if tracked_channel:
                voice_channel, text_channel = await create_new_channels(member, after,
                                                                        tracked_channel.setting, bot_member_on_guild)

                # write to log channel if configured
                if log_entry:
                    await log_channel.send(
                        embed=utl.make_embed(
                            name="Created voice channel",
                            value=f"{member.mention} created `{voice_channel.name if voice_channel else '`deleted`'}` "
                                  f"with {text_channel.mention if text_channel else '`deleted`'}",
                            color=utl.green
                        )
                    )

                # moving creator to created channel
                try:
                    await member.move_to(voice_channel, reason=f'{member} issued creation')
                    await send_welcome_message(text_channel, voice_channel)  # send message explaining text channel
                    
                # if user already left already
                except discord.HTTPException as e:
                    print("Handle HTTP exception during creation of channels - channel was already empty")
                    await clean_after_exception(voice_channel, text_channel, self.bot,
                                                archive=archive_category, log_channel=log_channel)

            # channel is in our database - add user to linked text_channel
            elif created_channel:

                # static channels need a new linked text-channel if they were empty before
                if created_channel.internal_type == 'static_channel' and created_channel.text_channel_id is None:

                    try:
                        tc_overwrite = generate_text_channel_overwrite(after_channel, self.bot.user)
                        text_channel = await guild.create_text_channel(after_channel.name,
                                                                       overwrites=tc_overwrite,
                                                                       category=after_channel.category,
                                                                       reason="User joined linked voice channel")
                        created_channel.text_channel_id = text_channel.id
                        session.add(created_channel)
                        session.flush()

                        await send_welcome_message(text_channel, after_channel)  # send message explaining text channel

                    except discord.HTTPException as e:
                        # TODO: log this
                        pass

                # processing 'normal', existing linked channel
                else:
                    # update overwrites to add user to joined channel
                    # TODO we can skip this API call when the creator just got moved
                    await update_channel_overwrites(after_channel, created_channel, bot_member_on_guild)

        if before_channel:

            # check db if before channel is a channel that was created by the bot
            created_channel: Union[db.CreatedChannels, None] = channels_db.get_voice_channel_by_id(before_channel.id, session)

            if created_channel:
                # member left but there are still members in vc
                if before_channel.members:
                    # remove user from left linked channel
                    await update_channel_overwrites(before_channel, created_channel, bot_member_on_guild)

                # left channel is now empty
                else:
                    # fetch needed information
                    before_channel_id: int = before_channel.id  # extract id before deleting, needed for db deletion
                    text_channel: Union[discord.TextChannel, None] = guild.get_channel(created_channel.text_channel_id)

                    # delete channels - catch AttributeErrors to still do the db access and the logging

                    # delete VC only if it's not a static_channel
                    if created_channel.internal_type != 'static_channel':
                        try:
                            await before_channel.delete(reason="Channel is empty")
                        except AttributeError:
                            pass

                    # archive or delete linked text channel
                    try:
                        archived_channel = await delete_text_channel(text_channel, self.bot, archive=archive_category)

                    except AttributeError:
                        archived_channel = None

                    except discord.errors.HTTPException:
                        # occurs when category that the channel shall be moved to is full
                        archived_channel = None
                        await log_channel.send(
                            embed=utl.make_embed(
                                name="ERROR handling linked text channel",
                                value=f"This error probably means that the archive `{archive_category.mention}` is full.\n"
                                      "Please check the category and it and set a new one or delete older channels.\n"
                                      "Text channel was not deleted",
                                color=utl.red))

                    if log_channel:
                        static = True if created_channel.internal_type == 'static_channel' else False  # helper variable

                        await log_channel.send(
                            embed=utl.make_embed(
                                name=f"Removed {text_channel.name}" if static else f"Deleted {before_channel.name}",
                                value=f"{text_channel.mention} was linked to {before_channel.name} and is " if static
                                      else f"The linked text channel {text_channel.mention} is"
                                      f"{'moved to archive' if text_channel.history() and archive_category else 'deleted'}",
                                color=utl.green
                            )
                        )

                    if created_channel.internal_type == 'static_channel':
                        # remove reference to now archived channel
                        created_channel.text_channel_id = None
                        session.add(created_channel)
                        session.flush()

                    else:
                        # remove deleted channel from database
                        channels_db.del_channel(before_channel_id)

        session.commit()
        session.close()


def setup(bot):
    bot.add_cog(VCCreator(bot))
