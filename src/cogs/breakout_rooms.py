import random
from typing import List

import discord
from discord.ext import commands

from environment import PREFIX
import utils
import sql_utils as sqltils
import cogs.help as hp
from cogs.on_voice_update import make_channel

# just needed for migration, will be gone in the future
db_file = "data/fury1.db"


class Breakout(commands.Cog):
    """
    Create and manage breakout rooms (kick permissions required for execution)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="openroom", aliases=["bor", "brout", "break-out", "opro"],
                      help=f"""
                            Usage: `{PREFIX}break-out [members per channel]`\n
                            Creates breakout channels with given amount of members\n
                            Members must be in same channel as you are
                            The distribution is randomized\n
                            Channel settings are the same as in your current channel\n
                            Linked text channels will be created too\n
                            Rooms created with this command behave like other channels created by the bot
                            Empty VCs are deleted. Linked TCs will be deleted or archived as set in the settings\n
                            Alias: `{PREFIX}opro [num]`
                            """)
    @commands.has_permissions(kick_members=True)
    async def break_out_rooms(self, ctx: discord.ext.commands.Context, *split: str):

        # check if invoker is in a channel
        if not ctx.author.voice:
            await hp.send_embed(ctx, embed=utils.make_embed("You're not in a VoiceChannel", discord.Color.orange(),
                                                            value="Please enter a Voice Channel and try again"))
            return

        # ensuring members var is given and is int
        try:
            # check can fail when typecast fails or number too small
            if int(split[0]) > 0:
                split = int(split[0])  # saving integer in variable

            # number too small
            else:
                await hp.send_embed(ctx, embed=utils.make_embed("Number must be greater than 0", discord.Color.orange(),
                                                                value=f"Try again :wink:\nExample: `{PREFIX}opro 4`"))
                return

        # type conversion failed
        except (IndexError, ValueError):
            await hp.send_embed(ctx, embed=utils.make_embed("Wrong argument", discord.Color.orange(),
                                                            value=f"Please enter the amount of members per channel\n"
                                                                  f"Example: `{PREFIX}opro 4`"))
            return

        # channel invoker is based in
        base_vc: discord.VoiceChannel = ctx.author.voice.channel

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
                mv_channel, _ = await make_channel(ctx.author.voice, members[i], overwrites,
                                                   vc_name=f"Breakout Room {i // split + 1}",
                                                   tc_name=f"Breakout Room {i // split + 1}",
                                                   channel_type="brout")
            if members[i].voice is None:
                continue
            await members[i].move_to(mv_channel, reason="Moved to breakout room")

    @commands.command(name="closeroom", aliases=["cbr", "clbr", "close-rooms", "cl", "cloro"],
                      help=f"""
                            Closing all break-out rooms on server\n
                            Members in those channels will be moved to your channel\n
                            Break out rooms will be deleted
                            Text channels will be deleted or archived -> settings.\n
                            Alias: `{PREFIX}cloro`
                            """)
    @commands.has_permissions(kick_members=True)
    async def close_rooms(self, ctx: commands.Context):
        # check if member is not in voice
        if not ctx.author.voice:
            await hp.send_embed(ctx, embed=utils.make_embed("You're not in a VoiceChannel", discord.Color.orange(),
                                                            value="Please enter a Voice Channel and try again"))
            return

        # getting break-out rooms from database
        db = sqltils.DbConn(db_file, ctx.guild.id, "created_channels")
        breakout_rooms: List[sqltils.SQL_to_Obj] = db.search_table(value='"brout"', column="type")

        # iterating trough break out rooms, moving members back in main channel
        # deletion of channels will be handled in separate on_voice_channel_update event when channel is empty
        back_channel = ctx.author.voice.channel
        for room in breakout_rooms:
            ch: discord.VoiceChannel = ctx.guild.get_channel(room.channel)
            if ch is None:  # channel already deleted
                continue
            for m in ch.members:
                if m.voice is None:  # member left voice chat
                    continue
                await m.move_to(back_channel)


def setup(bot):
    bot.add_cog(Breakout(bot))
