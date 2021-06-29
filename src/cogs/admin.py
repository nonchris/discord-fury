# built in
import time
import os
import re

# pip
import discord
from discord.ext import commands

# own
from environment import PREFIX, OWNER_NAME, OWNER_ID
import utils


class Admin(commands.Cog):
    """
    This commands are for the server team, most require admin or owner permissions
    """

    def __init__(self, bot):
        self.bot = bot

    # AIR
    # ORION

    @commands.command(name="fetch-reactions", hidden=True)
    @commands.has_permissions(administrator=True)
    async def fetch_message(self, ctx):
        """
        A butch, that fixes a problem with the reaction bot
        It's disgusting and hardcoded but I'm gonna leave it here, cause I need it to fix an other bot
        """
        if ctx.guild.id == 760421261649248296:
            channel = ctx.guild.get_channel(760455084353650698)
            message = await channel.fetch_message(760455425610350602)
            users = await message.reactions[0].users().flatten()
            role = ctx.guild.get_role(760434164146634752)
            i = 0
            for user in users:
                member = ctx.guild.get_member(user.id)
                if member == None:
                    pass
                if len(member.roles) == 1:
                    print(member)
                    await member.add_roles(role, reason="Reaction bot didn't work")
                    i += 1
            await ctx.send(content=f"Done, added {i} new members to {role.name}")

    # ROLE ID
    @commands.command(name="role-id", aliases=["roleid", "rid", "r-id"],
                      help="Mention a role or just give its name to get the roles ID\n Aliases: `roleid`, `rid`, `r-id`")
    @commands.has_permissions(kick_members=True)
    async def roleid(self, ctx, *role_name: str):
        try:
            role, le = utils.get_rid(ctx, role_name)  # getting IDs
            if le == 1:  # if only one ID returned
                role = ctx.guild.get_role(role[0])
                await ctx.send(content=role.id)

            else:  # if more than one result - giving all possible roles
                emby = discord.Embed(title="Multiple possible roles", color=discord.Color.blue())
                possible_roles = ""
                for r in role:  # iterating trough roles
                    print(r)
                    r = ctx.guild.get_role(r)
                    i = 0
                    for members in r.members:  # counting members
                        i += 1
                    possible_roles += "%s with %s members - ID: %s\n" % (r.mention, i, r.id)

                emby.add_field(name="Which one do you mean?", value=possible_roles)
                emby.set_footer(text="To get an easy copy-pasteable ID mention the role you mean")
                await ctx.send(embed=emby)

        except:
            emby = discord.Embed(title="", color=discord.Color.red())
            emby.add_field(name="Something went wrong", value="Please check your given argument.\n"
                                                              "Note that name inputs are handled case-sensitive and spaces in names might cause trouble.\n"
                                                              "Syntax: `%smembers <@role | role id | role name>`" % PREFIX)
            emby.set_footer(
                text="If you did everything right and this error keeps occurring, please contact the bot owner %s" % OWNER_NAME)
            await ctx.send(embed=emby)


def setup(bot):
    bot.add_cog(Admin(bot))
