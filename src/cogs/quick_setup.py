import discord
from discord.ext import commands

import utils as ut
import database.db_models as db
import database.access_channels_db as channels_db
import database.access_settings_db as settings_db

from environment import PREFIX, CHANNEL_TRACK_LIMIT


class Setup(commands.Cog):
    """
    Quick start.
    Setup a category containing a channel for creating public and private channels.
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name="setup", aliases=["setup-voice"],
                      help="Creates a category containing:\n"
                           "- a channel to trigger the creation of a public channel\n"
                           "- a channel to issue the creation of a private channel\n\n"
                           "It is possible to enter an optional default role that is allowed see those channels "
                           "the channels won't be visible for the \@everyone-role\n"
                           "You can enter the role as id or mention.\n\n"
                           f"Usage: `{PREFIX}setup [role id]`")
    @commands.has_permissions(administrator=True)
    async def setup_voice(self, ctx: commands.Context, *role):

        await ctx.trigger_typing()

        # refresh channels to ensure that the category will be placed on the top
        await ctx.guild.fetch_channels()

        # check if more tracked channels are allowed on that guild, limit is set in environment
        if settings_db.is_track_limit_reached(ctx.guild.id):
            await ctx.send(embed=ut.make_embed(
                name="Too many tracked channels", color=ut.orange,
                value=f"Hey, I can only track {CHANNEL_TRACK_LIMIT} channels per type (public / private) for you.\n\n"
                      "If you want to change the channels I'm keeping track of "
                      f"use `{PREFIX}ds [channel-id]` to remove a channel from the settings\n"
                      f"Use `{PREFIX}gs` to get a list of all settings on your server."))

            return

        # overwrites for category and channels to be created
        overwrites = {}

        # if we've got an input for role
        if role:

            # check if we've got a custom 'standard' role, so we can disable the default role
            base_role = ctx.guild.get_role(ut.extract_id_from_message(role))

            # role is not found - interrupt setup
            if not base_role:
                await ctx.send(embed=ut.make_embed(
                    name="No valid role",
                    value="Hey, the given id is invalid, "
                          "I'll interrupt the setup process.\n"
                          "Try again with an other role id or skip this parameter to use the default \@everyone role",
                    color=ut.orange))
                return

            # role was valid - we can hide the channels for the default role
            else:
                overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(view_channel=False, connect=False)

        # okay, @everyone seems to be the wanted base role that shall see the channel
        else:
            base_role = ctx.guild.default_role

        # allow access for base role
        overwrites[base_role] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)

        # create channels
        category = await ctx.guild.create_category(
            "Voice Channels", overwrites=overwrites, reason="Created by setup process", position=0)

        public_channel = await ctx.guild.create_voice_channel("╔create-voice-channel", category=category,
                                                              reason="Created voice setup")
        private_channel = await ctx.guild.create_voice_channel("╠new-private-channel", category=category,
                                                               reason="Created voice setup")

        settings_db.add_setting(
            ctx.guild.id, 'public_channel', public_channel.id, set_by=f'Auto setup issued by {ctx.author.id}')

        settings_db.add_setting(
            ctx.guild.id, 'private_channel', private_channel.id, set_by=f'Auto setup issued by {ctx.author.id}')

        await ctx.send(embed=ut.make_embed(
            name="Done",
            value="The channels are set up, you're ready to create new voice channels on demand!\n\n"
                  "You can move, rename and edit the created channels how you like :smile:\n"
                  f"It's all tied to the channel IDs of {public_channel.name} and {private_channel.name}",
            footer=f"You can register additional channels using {PREFIX}add [channel id]",
            color=ut.green
        ))


def setup(bot: commands.Bot):
    bot.add_cog(Setup(bot))
