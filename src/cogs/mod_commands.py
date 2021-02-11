import random
from typing import List

import discord
from discord.ext import commands

import utils
from cogs.on_voice_update import make_channel


class Moderator(commands.Cog):
    """
    Here are commands that not any member can access but everyone with kick permissions (for now)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="break-out", aliases=["bro"])
    @commands.has_permissions(kick_members=True)
    async def break_out_rooms(self, ctx: discord.ext.commands.Context, *split: str):

        if not ctx.author.voice:
            await ctx.send(embed=utils.make_embed("You're not in a VoiceChannel", discord.Color.orange(),
                                                  value="Please enter a Voice Channel and try again"))
            return

        # ensuring members var is given
        try:
            if int(split[0]) > 0:
                split = int(split[0])

            else:
                await ctx.send(embed=utils.make_embed("Number must be greater than 0", discord.Color.orange(),
                                                      value="Try again :wink:"))
                return

        except ValueError:
            await ctx.send(embed=utils.make_embed("Wrong argument", discord.Color.orange(),
                                                  value="Please enter the amount of members per channel"))
            return

        base_vc: discord.VoiceChannel = ctx.author.voice.channel

        # channels_to_create = len(vc.members) // split
        # TODO: Remove invoker from list
        mv_channel = None
        members: List[discord.Member] = base_vc.members.copy()
        random.shuffle(members)
        overwrites = base_vc.category.overwrites

        for i in range(len(base_vc.members)):
            if i % split == 0:
                mv_channel, _ = await make_channel(ctx.author.voice, members[i], overwrites,
                                                   vc_name=f"Breakout Room {i // split + 1}",
                                                   tc_name=f"Breakout Room {i // split + 1}")

            await members[i].move_to(mv_channel, reason="Moved to breakout room")


def setup(bot):
    bot.add_cog(Moderator(bot))
