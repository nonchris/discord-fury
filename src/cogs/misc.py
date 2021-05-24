import time

import discord
from discord.ext import commands 

import data.config as config
import utils
class Misc(commands.Cog,):
	"""
	Various useful Commands for everyone
	"""
	def __init__(self, bot):
		self.bot = bot


	#A command that behaves like dynos "members" command but with a split between bots and humans and an included member-count
	#There are serval options like that admins can display more members on request
	@commands.command(name="members", help="Get a list and count of members that have a specific role e.g. `%smembers @role`\nThis command accepts an id, a mention or a name "
						"If you're an administrator your embeds will be larger and you're able to add an optional parameter to get a list that contains more than one embed."
						"Example: `%smembers 3 everyone` will give you three embeded messages packed with names of members" %(config.PREFIX, config.PREFIX))
	async def members(self, ctx, *role: str):
		await ctx.trigger_typing()
		try:
			#testing if there was a first number argument that gives the number of ebends to show
			#like a parameter in bash
			#identifying the parameter by checking for lenght (avoid role id), for more than one given argument and by trying to convert to integer
			emb_req = 1 #setting var to default
			try: #fails when no role argument is given

				if len(role[0]) < 12 and len(role) > 1:
					emb_req = int(role[0])
					role = role[1:] #cutting first vakue from "role name"
			except: #ignoring everything
				None

			#getting role-id and the actual role object (a role id is 18 characters long)
			role, le = utils.get_rid(ctx, role)
			if le > 1:
				emby = discord.Embed(title="Multiple possible roles", color=discord.Color.blue())
				possible_roles = ""
				for r in role: #iterating trough roles
					r = ctx.guild.get_role(r)
					i = 0
					for members in r.members: #counting members
						i += 1
					possible_roles += "%s with %s members - ID: %s\n" %(r.mention, i, r.id)

				emby.add_field(name="Which one do you mean?", value=possible_roles)
				emby.set_footer(text="To get the actual information you need to use the id or a mention of the role")
				await ctx.send(embed=emby)

			#if only one role is possible
			else:
				role = ctx.guild.get_role(role[0])
				#setting up for loop
				emby = discord.Embed(title="Members in %s" %role.name, color=discord.Color.green())
				role_members = "" #contains members list
				role_bots = ""  #contains bot list
				i_members = 0   #contains the members
				i_bots = 0      #contains the bot count
				#print(type(role.members))


				members_list = []
				bots_list = []

				#await ctx.send(content = self.bot.get_emoji(462278332583510037))
				for member in role.members: #iterating trough members and adding to list, icreasaing also counter

					#adding a custom emoji that shows the status of the listed member
					#emotes will be loaded from a switch in config.py
					if str(member.mobile_status) == "online":
						status_emoji = self.bot.get_emoji(config.switch_online.get("mobile"))
					else:
						status_emoji = self.bot.get_emoji(config.switch_online.get(str(member.status)))

					if member.bot == True: #checking if bot
						i_bots += 1
						#bots_list.append("%s %s" %(member.mention, status_emoji))
						bots_list.append(f"{member.mention} " + f"{status_emoji}".rjust(20))
					else: #human
						i_members += 1
						members_list.append("%s %s" %(member.mention, status_emoji))
				

				#an embed can't contain an empty field
				#so if there is no bot or human in this role this section replaces the emty field with the text "None"
				if not members_list:
					members_list.append("None")
				if not bots_list:
					bots_list.append("None")

				#checking if user can request more than one embed
				#first value: Amount of Embed Messages, second Number of fields per embed
				switch_admin = {
					True: [emb_req, 6],
					False: [1, 3]
				}

				#preparing the embeds
				#checking for admin perms, because only admins should be able to spam the channel
				props = switch_admin.get(ctx.author.guild_permissions.administrator)
				
				head = "Members [%s] " %(len(role.members))     #first field title of embed
				#creating Embeds is function (returns a list of embed objects)
				embys = utils.make_emby(emby, head, members_list, embed_limit=props[0], field_limit=props[1])   

				#sending multiple embeds - the last embed will be sent out when bots is finished (bellow)
				i = 0 #counter for making sure the last one stays
				for emby in embys:
					if i < len(embys)-1:
						await ctx.trigger_typing()
						await ctx.send(embed=emby)
						time.sleep(0.3) #waiting - don't spam the API too much!
					i += 1
				
				await ctx.trigger_typing()
				head = "Bots [%s]" %(i_bots) #head for bot section
				embys = utils.make_emby(emby, head, bots_list)
				i = 0 #counting embys
				for emby in embys:
					i +=1
					if i == len(embys): #setting footer in the last embed possible
						emby.set_footer(text="Role ID: %s" %role.id)
					await ctx.trigger_typing()
					await ctx.send(embed=emby)
					
			
		#this triggers when no ID or Role was given
		except: 
			emby = discord.Embed(title="", color=discord.Color.red())
			emby.add_field(name="Something went wrong", value="Please check your given argument.\n"
							"Note that name inputs are handled case-sensitive and spaces in names might cause trouble.\n"
							"Syntax: `%smembers <messages> <@role | role id | role name>`"%config.PREFIX)
			emby.set_footer(text="If you did everything right and this error keeps occuring, please contact the bot owner %s" %config.OWNER_NAME)
			await ctx.send(embed = emby)

	@commands.command(name='ping', help="Check if the Bot is available")
	async def ping(self, ctx):
		print("ping: %s" %round(self.bot.latency * 1000))
		await ctx.send(f'Bot is available - Ping: ``{round(self.bot.latency * 1000)}ms``')


	@commands.command(name='version', aliases=["v"], help="Gives the version this Bot is running on")
	async def version(self, ctx):
		await ctx.send("The Bot is running version `%s`" %config.VERSION)


def setup(bot):
	bot.add_cog(Misc(bot)) 