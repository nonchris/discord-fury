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
                       voice_overwrites: discord.PermissionOverwrite,
                       vc_name="voice-channel", tc_name="text-channel", channel_type="public") -> Tuple[
                       discord.VoiceChannel, discord.TextChannel]:
    """
    Method to create a voice-channel with linked text-channel logging to DB included\n
    -> VCs created with this method are meant to be deleted later on, therefore they're logged to DB

    :param voice_state: To detect which VC the member is in
    :param member: To access guild and give member TC access permissions
    :param bot_member: Bot as member to enable access on all created channels
    :param voice_overwrites: To give member extra permissions in the VC and TC
    :param vc_name: Voice Channel name
    :param tc_name: Text Channel name
    :param channel_type: For SQL-logging can be "public" or "private"

    :returns: Created Text and VoiceChannel Objects
    """
    # creating channels
    # TODO handle error on creation
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
                            ["╠{0}'s' public office", "{0}'s public office"]
                            ],

                 "private_channel": [["╠{0}'s private discussion", "{0}'s private discussion"],
                             ["╠{0}'s private fellowship", "{0}'s private fellowship"],
                             ["╠{0}'s private room", "{0}'s private room"],
                             ["╠{0}'s elite room", "{0}'s elite room"],
                             ["╠{0}'s regular table", "{0}'s regular table"],
                             ["╠{0}'s private haven", "{0}'s private haven"]
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
    allowed_to_edit = settings_db.get_all_settings_for(member.guild.id, "edit_public")

    # get channel names from dict above
    new_channel_name = random.choice(channel_names[channel_type])

    # default overwrites for new channel
    voice_channel_permissions = after.channel.category.overwrites

    voice_channel_permissions[bot_member] = discord.PermissionOverwrite(view_channel=True)

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
    elif allowed_to_edit:
        voice_channel_permissions[member] = discord.PermissionOverwrite(connect=True,
                                                                        manage_channels=True)

    # issue creation of channels
    voice_channel, text_channel = await make_channel(after, member, bot_member, voice_channel_permissions,
                                                     vc_name=new_channel_name[0].format(member.display_name),
                                                     tc_name=new_channel_name[1].format(member.display_name),
                                                     channel_type=channel_type)

    return voice_channel, text_channel


async def delete_text_channel(t_channel: discord.TextChannel, archive=None):
    """
    Checks whether channel shall be archived or deleted and executes that action
    """
    print(f"{archive=}")
    # if archive is given and channel is not empty: move to archive
    if archive and t_channel.last_message is not None:
        await t_channel.edit(category=archive,
                             reason="Connected voice channel is empty, archive channel with messages",
                             overwrites=archive.overwrites)
        return

    # delete channel
    await t_channel.delete(reason="Channel is empty and not needed anymore")


async def clean_after_exception(voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel,
                                archive=None, log_channel=None):
    """ Cleanup routine that handles the deletion / activation of a voice- and text-channel"""
    await voice_channel.delete(reason="An error occurred - user most likely left the channel during the process")
    await delete_text_channel(text_channel, archive=archive)
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


async def update_channel_overwrites(after_channel: discord.VoiceChannel, created_channel, bot_member: discord.Member):
    # get new overwrites for text channel
    overwrites = generate_text_channel_overwrite(after_channel, bot_member)
    # get linked text channel
    linked_channel: discord.VoiceChannel = after_channel.guild.get_channel(created_channel.text_channel_id)
    # TODO: logging if text channel not exists
    if linked_channel:
        await linked_channel.edit(overwrites=overwrites)


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

        # as shorthand - we'll need this a few times
        guild: discord.Guild = member.guild
        bot_member_on_guild: discord.Member = guild.get_member(self.bot.user.id)
        after_channel: Union[discord.VoiceChannel, None] = after.channel
        before_channel: Union[discord.VoiceChannel, None] = before.channel

        # get settings for archive and log channel
        log_entry = settings_db.get_first_setting_for(guild.id, "log_channel")  # get entry if exists
        archive_entry = settings_db.get_first_setting_for(guild.id, "archive_category")

        # get channels from entries if existing
        log_channel: Union[discord.TextChannel, None] = guild.get_channel(int(log_entry.value)) if log_entry else None
        archive_category: Union[discord.CategoryChannel, None] = guild.get_channel(
            int(archive_entry.value)) if archive_entry else None

        # check if member has a voice channel after the state update
        # could trigger the creation of a new channel or require an update for an existing one
        if after_channel:

            # check db if channel is a channel that was created by the bot
            created_channel: Union[db.CreatedChannels, None] = channels_db.get_voice_channel_by_id(after_channel.id)
            # print(f"{created_channel=}")

            # check if joined (after) channel is a channel that triggers a channel creation
            create_channel = settings_db.get_setting_by_value(guild.id, after_channel.id)
            # print(f"{create_channel=}")

            if create_channel:
                print(f"{create_channel.setting=}")
                voice_channel, text_channel = await create_new_channels(member, after,
                                                                        create_channel.setting, bot_member_on_guild)

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
                # if user already left already
                except discord.HTTPException as e:
                    print("Handle HTTP exception during creation of channels - channel was already empty")
                    await clean_after_exception(voice_channel, text_channel,
                                                archive=archive_category, log_channel=log_channel)

            # channel is a bot created channel - add user to linked text_channel
            elif created_channel:
                # update overwrites to add user to joined channel
                await update_channel_overwrites(after_channel, created_channel, bot_member_on_guild)

        if before_channel:
            # check db if before channel is a channel that was created by the bot
            created_channel: Union[db.CreatedChannels, None] = channels_db.get_voice_channel_by_id(before_channel.id)

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
                    try:
                        await before_channel.delete(reason="Channel is empty")
                    except AttributeError:
                        pass

                    # archive or delete linked text channel
                    try:
                        await delete_text_channel(text_channel, archive=archive_category)

                    except AttributeError:
                        pass

                    except discord.errors.HTTPException:
                        # occurs when category that the channel shall be moved to is full
                        await log_channel.send(
                            embed=utl.make_embed(
                                name="ERROR handling linked text channel",
                                value=f"This error probably means that the archive `{archive_category.mention}` is full.\n"
                                      "Please check the category and it and set a new one or delete older channels.\n"
                                      "Text channel was not deleted",
                                color=utl.red))

                    if log_channel:
                        await log_channel.send(
                            embed=utl.make_embed(
                                name=f"Deleted {before_channel.name}",
                                value=f"The linked text channel {text_channel.mention} was"
                                      f"{'moved to archive' if text_channel.history() and archive_category else 'deleted'}",
                                color=utl.green
                            )
                        )

                    # remove deleted channel from database
                    channels_db.del_channel(before_channel_id)


def setup(bot):
    bot.add_cog(VCCreator(bot))
