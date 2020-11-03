#built in
import time
import os
import re

#pip
import discord
from discord.ext import commands

#own
import data.config as config
import utils

#wrinting suggestsion in file
def write_log(ctx, file_name, content):

	#checking if folder exists and creating if needed
	server_dir = ctx.guild.id
	if os.path.isdir('./data/%s' %server_dir):
		None
	else:
		os.mkdir('./data/%s' %server_dir)
		#writing current name of the guild as file
		#preventing from trying to create an sub folder
		open('./data/%s/%s.info' %(server_dir, str(ctx.guild).replace("/", "|")),"w").close()

	#checking if file exists and creating if needed
	file_path = file_name
	if os.path.isfile(file_path):
		None
	else:
		open(file_path, "w").close()

	data = content
	f = open(file_path, "a")
	f.write(data)
	f.close()


class Admin(commands.Cog):
	"""
	This commands are for the server team, most require admin or owner permissions
	"""
	def __init__(self, bot):
		self.bot = bot

	#AIR
	#ORION
	
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
				elif len(member.roles) == 1:
					print(member)
					await member.add_roles(role, reason="Reaction bot didn't work")
					i += 1
			await ctx.send(content=f"Done, added {i} new members to {role.name}")


	
	@commands.command(name='backup-roles', aliases=["broles", "br"], help="Creates a backupfile with all roles members have\n"
								"This can be executed by everyone with kick-permissions \n_Short term:_ `%sbroles`, `%sbr`"%(config.PREFIX, config.PREFIX))
	@commands.has_permissions(kick_members=True) 
	async def backup(self, ctx):#, member : discord.Member):
		#await ctx.send(ctx.message.guild.members)
		f_name = "backup_%s.csv" %time.strftime("%Y-%m-%d_%H-%M-%S")
		file_name="data/%s/%s" %(ctx.message.guild.id, f_name)
		restore_string = ""
		#remove roles from members
		for member in ctx.message.guild.members: #iterating trough all memebers
			#going through roles of member
			for role in member.roles:           #getting all roles of member
				#print(role)
				if role.id == member.guild.default_role.id:    #skipping if role is @everyone role
					None
				elif role.managed == True:      #skipping if role is managed, e.g. bot-role
					None
				else:                          #saving role
					#string that conatins member-name,memberID,role,roleID, date
					restore_string += "%s; %s; %s; %s\n" %(str(member).replace(";", ":"), member.id, str(role).replace(";", ":"), role.id)

		write_log(ctx, file_name, restore_string)
		
		emby = discord.Embed(title="", color=discord.Color.green())
		emby.add_field(name="Backup created", value="**Please save the name of this file, you need it for restoring it**\n`%s`" %f_name)
		await ctx.message.delete(delay=None)        #delete invoke message
		await ctx.send(embed=emby)
		
		print()
		print('Backup created by %s (%s)'%(ctx.message.author, ctx.message.author.id))
		print()
	


	#Reverse BACKUP
	#Precise Filename is needed as argument
	@commands.command(name="restore", help="Restore a backup from file - Usage: `%srestore <file_name>`\nThe filename was given, when the backup was created"%config.PREFIX)
	@commands.has_permissions(administrator=True) 
	async def re_escalate(self, ctx, file_name: str):
		try:
			owner = config.OWNER
			if ctx.message.author.id == owner: #check if owner
				#reading and iteration trough file
				f = open("data/%s/%s" %(ctx.message.guild.id, file_name), "r")
				await ctx.message.delete(delay=None) #delete invoke message - if we reached that point the filename is right
				#strrage for different types of errors
				line_errors = ""
				data_errors = ""
				perm_erros = ""
				for line in f:
					line = line.split(";") #making list
					#a rough check if the line has the right length, if not there might be a semicolon in the name - skipping
					if len(line) > 4:
						line_errors += str(line) + "\n"
					
					else:
						#getting member and role
						member = ctx.guild.get_member(int(line[1]))
						member_status = True #has to stay true for further actions
						if member == None:
							member_status = False #setting it to false
							data_errors += "Can't resolve member ID `%s`\n" %str(line[1].strip())

						
						role = ctx.guild.get_role(int(line[3]))
						role_status = True
						if role == None:
							role_status = False
							data_errors += "Can't resolve role ID `%s`\n" %str(line[3].strip())

						#adding role to member if gained information was valid
						#going trough the roles a member has and checking if he has the needed role
						#if he has not the role will be added
						if role_status == True and member_status == True:
							for r in member.roles:
								if r.id == role.id:
									break
							else:
								#check if bot can give this role from position
								if role.position > ctx.guild.me.top_role.position:
									perm_erros += "%s to %s\n" %(member.mention, role.mention)
								else:
									await member.add_roles(role, reason="Restored roles form backup")
									print("Adding %s to %s" %(member.display_name, role.name))

				

				print()
				print("Finished")
				print()
				emby = discord.Embed(title="Success", color=discord.Color.green())
				#emby.add_field(name="Restored status from backup", value="")
				emby.add_field(name="Line-Errors", value= "Problem with the following lines:\n\n" + line_errors)
				emby.add_field(name="Data-Errors", value= "Role and User IDs that were not available:\n\n" + data_errors)
				emby.add_field(name="Permission-Errors", value="Roles the bot can't give because they are too high:\n\n" + perm_erros)
				await ctx.send(embed=emby)

		except:
			await ctx.send(content="Error. Maybe the filename was wrong?")



	#ROLE ID
	@commands.command(name="role-id", aliases=["roleid", "rid", "r-id"], help="Mention a role or just give its name to get the roles ID\n Aliases: `roleid`, `rid`, `r-id`")
	@commands.has_permissions(kick_members=True)
	async def roleid(self, ctx, *role_name: str):
		try:
			role, le = utils.get_rid(ctx, role_name) #getting IDs
			if le == 1: #if only one ID returned
				role = ctx.guild.get_role(role[0])
				await ctx.send(content=role.id)
			
			else: #if more than one result - giving all possible roles
				emby = discord.Embed(title="Multiple possible roles", color=discord.Color.blue())
				possible_roles = ""
				for r in role: #iterating trough roles
					print(r)
					r = ctx.guild.get_role(r)
					i = 0
					for members in r.members: #counting members
						i += 1
					possible_roles += "%s with %s members - ID: %s\n" %(r.mention, i, r.id)

				emby.add_field(name="Which one do you mean?", value=possible_roles)
				emby.set_footer(text="To get an easy copy-pasteable ID mention the role you mean")
				await ctx.send(embed=emby)


		except:
			emby = discord.Embed(title="", color=discord.Color.red())
			emby.add_field(name="Something went wrong", value="Please check your given argument.\n"
							"Note that name inputs are handled case-sensitive and spaces in names might cause trouble.\n"
							"Syntax: `%smembers <@role | role id | role name>`"%config.PREFIX)
			emby.set_footer(text="If you did everything right and this error keeps occuring, please contact the bot owner %s" %config.OWNER_NAME)
			await ctx.send(embed = emby)


def setup(bot):
	bot.add_cog(Admin(bot)) 