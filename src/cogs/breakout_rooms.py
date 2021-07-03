import random
from typing import List

import discord
from discord.ext import commands

from environment import PREFIX
import utils
import database.db_models as db
import database.access_channels_db as channels_db
import cogs.help as hp
from cogs.on_voice_update import make_channel


class Breakout(commands.Cog):
    """
    Create and manage breakout rooms (kick permissions required for execution)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="open", aliases=["bor", "brout", "break-out", "opro", "openroom"],
                      help=f"""
                            Usage: `{PREFIX}break-out [members per channel]`\n
                            Creates breakout channels with given amount of members\n
                            Members must be in same channel as you are
                            The distribution is randomized\n
                            Channel settings are the same as in your current channel\n
                            Linked text channels will be created too\n
                            Rooms created with this command behave like other channels created by the bot
                            Empty VCs are deleted. Linked TCs will be deleted or archived as set in the settings\n
                            Alias:`openroom`, `opro`, `break-out`, `brout`, `bor`\n\n
                            Requires kick permissions.
                            """)
    @commands.has_permissions(kick_members=True)
    async def break_out_rooms(self, ctx: discord.ext.commands.Context, *split: str):

        # check if invoker is in a channel
        if not ctx.author.voice:
            await hp.send_embed(ctx, embed=utils.make_embed("You're not in a VoiceChannel", utils.orange,
                                                            value="Please enter a Voice Channel and try again"))
            return

        # ensuring members var is given and is int
        try:
            # check can fail when typecast fails or number too small
            if int(split[0]) > 0:
                split = int(split[0])  # saving integer in variable

            # number too small
            else:
                await hp.send_embed(ctx, embed=utils.make_embed("Number must be greater than 0", utils.orange,
                                                                value=f"Try again :wink:\nExample: `{PREFIX}open 4`"))
                return

        # type conversion failed
        except (IndexError, ValueError):
            await hp.send_embed(ctx, embed=utils.make_embed("Wrong argument", utils.orange,
                                                            value=f"Please enter the amount of members per channel\n"
                                                                  f"Example: `{PREFIX}open 4`"))
            return

        # channel invoker is based in
        base_vc: discord.VoiceChannel = ctx.author.voice.channel

        # bot itself, needed to garant access to created channels
        bot_member: discord.Member = ctx.guild.get_member(self.bot.user.id)

        # making a copy of members in channel - used to move members
        members: List[discord.Member] = base_vc.members.copy()
        members.remove(ctx.author)  # invoker should not be moved to break-out-room
        random.shuffle(members)  # shuffling list

        overwrites = base_vc.category.overwrites  # settings for new channels
        mv_channel = None  # temp var for holding current created channel
        for i in range(len(members)):
            """
            Iterating trough members of VC
            Creating new channel when last one filled
            Moving members
            """
            if i % split == 0:
                mv_channel, _ = await make_channel(ctx.author.voice, members[i], bot_member, overwrites,
                                                   vc_name=f"Breakout Room {i // split + 1}",
                                                   tc_name=f"Breakout Room {i // split + 1}",
                                                   channel_type="breakout_room")
            if members[i].voice is None:
                continue
            await members[i].move_to(mv_channel, reason="Moved to breakout room")

    @commands.command(name="close", aliases=["collect", "closeroom", "cbr", "clbr", "close-rooms", "cl", "cloro"],
                      help=f"""
                            Closing all break-out rooms on server\n
                            Members in those channels will be moved to your channel\n
                            Break out rooms will be deleted
                            Text channels will be deleted or archived -> settings.\n
                            Alias: `collect`, `closeroom`, `cloro`, `close-room`, `close-rooms`, `cl`, `clbr`\n\n
                            Requires kick permissions.
                            """)
    @commands.has_permissions(kick_members=True)
    async def close_rooms(self, ctx: commands.Context):
        # check if member is not in voice
        if not ctx.author.voice:
            await hp.send_embed(ctx, embed=utils.make_embed("You're not in a VoiceChannel", utils.orange,
                                                            value="Please enter a Voice Channel and try again"))
            return

        # getting break-out rooms from database
        breakout_rooms: List[db.CreatedChannels] = channels_db.get_channels_by_type(ctx.guild.id, "breakout_room")

        if not breakout_rooms:
            await ctx.send(embed=utils.make_embed(
                name="No breakout rooms open",
                value="There are no rooms I can close.",
                color=utils.yellow
            ))

            return

        # iterating trough break out rooms, moving members back in main channel
        # deletion of channels will be handled in separate on_voice_channel_update event when channel is empty
        back_channel = ctx.author.voice.channel
        for room in breakout_rooms:
            ch: discord.VoiceChannel = ctx.guild.get_channel(room.voice_channel_id)
            if ch is None:  # channel already deleted
                continue
            for m in ch.members:
                if m.voice is None:  # member left voice chat
                    continue
                await m.move_to(back_channel)

        await ctx.send(embed=utils.make_embed(
            name="Done",
            value=f"Moved all members from breakout rooms to your channel ({back_channel.name}).\n"
                  "All empty rooms will be removed in a few seconds.",
            color=utils.green
        ))


def setup(bot):
    bot.add_cog(Breakout(bot))
