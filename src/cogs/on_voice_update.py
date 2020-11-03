#built in
from typing import Union
import random
import time

#pip
import discord
from discord.ext import commands

#own files
import data.config as config
import sql_utils as sqltils
import utils

global db_file
db_file = config.DB_NAME


class EventCheck:
	"""
	Responsible for DB access
	has methods to check which actions need to be triggered
	"""
	def __init__(self, member, before, after):
		self.member = member
		self.before = before
		self.after = after
		self.db = sqltils.DbConn(db_file, self.member.guild.id, "setting")

	def is_activate(self) -> Union[str, bool]:
		#checks if joined channel is in the list of watched channels
		#accessing db and searching for settings - building a dict
		self.channel_dict = {obj.value_id: "pub"
					for obj in self.db.search_table(value="pub-channel", column="setting")}
		self.channel_dict.update({obj.value_id: "priv"
					for obj in self.db.search_table(value="priv-channel", column="setting")})

		try: #return keyword "pub" or "priv", if channel id in dict
			return self.channel_dict[self.after.channel.id]
		except KeyError as e: #if not in dict, returning none
			return None

	def is_created_channel(self, channel: int) -> list:
		#checks if joined channel is a custom created one - returns all results as objects
		db = sqltils.DbConn(db_file, self.member.guild.id, "created_channels")
		return db.search_table(value=channel, column="channel_id")

	def get_archive(self): #resturns channel object
		result = self.db.search_table(value="archive", column="setting")
		try:
			return self.member.guild.get_channel(result[0].value_id)
		except IndexError:
			return None

	def get_log(self): #resturns channel object
		result = self.db.search_table(value="log", column="setting")
		try:
			return self.member.guild.get_channel(result[0].value_id)
		except IndexError:
			return None

	def del_entry(self, channel):
		db = sqltils.DbConn(db_file, self.member.guild.id, "created_channels")
		db.remove_line(channel, column="channel_id")


channel_names = {"pub": [["╠{0}'s discussion", "{0}'s discussion"],
					["╠{0}'s voice channel", "{0}'s text channel" ],
					["╠{0}'s room", "{0}'s room"],
					["╠{0}'s open talk", "{0}'s open talk"],
					["╠{0}'s bar", "{0}'s bar"],
					["╠{0}'s' public office", "{0}'s public office"]
					],

			"priv": [["╠{0}'s private discussion", "{0}'s private discussion"],
					["╠{0}'s private fellowship", "{0}'s private fellowship"],
					["╠{0}'s private room", "{0}'s private room"],
					["╠{0}'s elite room", "{0}'s elite room"],
					["╠{0}'s regular table", "{0}'s regular table"],
					["╠{0}'s private haven", "{0}'s private haven"]
				]
				}


class VoiceChannelCreator(commands.Cog):
	"""
	Contains the setup-voice command and the listener itself
	"""
	@commands.command(name="setup-voice", help="Creates a voice category, \
				including a public and a private creation channel.\
				Those channels will contain no specified settings.\
				Enter a role [id | mention] to add give this role the access permissions -\
				everyone role will be disabled")
	@commands.has_permissions(administrator=True)
	async def setup_voice(self, ctx, role=None):	
		await ctx.trigger_typing()
		ov = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)}
		
		if role: #if there was a role as input - making custom overwrite
			role, leng = utils.get_rid(ctx, [role])
			role = ctx.guild.get_role(role[0])
			print(role)
			if role:
				ov = {
					ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False, speak=False),
					role: discord.PermissiosnOverwrite(view_channel=True, connect=True, speak=True)
				}
			else:
				await ctx.send(embed=utils.make_embed(value="Hey, the given id is invalid,\
								I'm trying to create the channels but with the default settings.",\
								name="No valid role", color=discord.Color.orange()))
		#creating channels
		cat = await ctx.guild.create_category_channel("Voice Channels", overwrites=ov, reason="Created voice setup")
		await cat.edit(overwrites=ov, position=0) #move up didn't work in the creation
		pub_ch = await ctx.guild.create_voice_channel("╔create-voice-channel", category=cat, reason="Created voice setup")
		priv_ch = await ctx.guild.create_voice_channel("╠new-private-channel", category=cat, reason="Created voice setup")
		db = sqltils.DbConn(db_file, ctx.guild.id, "setting")
		#checking if db has three entries for one of those settings
		if len(results := db.search_table(value="pub-channel", column="setting")) < config.SET_LIMIT \
		or len(results := db.search_table(value="priv-channel", column="setting")) < config.SET_LIMIT:
			db.write_server_table(("pub-channel", "value_name", pub_ch.id, time.strftime("%Y-%m-%d %H:%M:%S"), config.VERSION_SQL))
			db.write_server_table(("priv-channel", "value_name", priv_ch.id, time.strftime("%Y-%m-%d %H:%M:%S"), config.VERSION_SQL))

			await ctx.send(embed=utils.make_embed(name="Sucessfully setup voice category",\
						value="You're category is set, have fun!\n \
						Oh, yeah - you can change the channel names how ever you like :)", color=discord.Color.green()))
		
		else: #if channel max was reached
			await ctx.send(embed=utils.make_embed(name="Too many channels!",
							value=f"Hey, you can't make me watch more than {config.SET_LIMIT} channels per creation type.\n\
							If you wanna change the channels I watch use \
							`{config.PREFIX}ds [channel-id]` to remove a channel from your settings\n \
							The channels were created but aren't watched, have a look at `{config.PREFIX}help settings`\
							to add them manually after you removed other watched channels from the settings"))

##Codename: PANTHEON
	"""
	A function that creates custom voice channels if triggered
	 - Creates a dedicated voice-channel
	 - Creates a private linked text-channel
	 - Members will be added and removed to text-channel
	 - There is an option for a customizable /private voice-channel
	"""
	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		
		def make_overwrite(members: list) -> dict: #creates the overwrites dict for the text-channel
			return {m:discord.PermissionOverwrite(view_channel=True) for m in members}

		def update_text_channel(cchannel):
			#function that makes the dict overwrites for text channels
			v_channel = member.guild.get_channel(cchannel[0].channel)
			t_channel = member.guild.get_channel(cchannel[0].linked_channel)
			overwrites = {member.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
			overwrites.update(make_overwrite(v_channel.members))
			return t_channel, overwrites
			
		#object that performs checks which cases are true
		checker = EventCheck(member, before, after) 
		l_channel = checker.get_log() #log channel

		if after.channel: #check if person is in channel
			#check if creating is triggered creation type or none
			ch_type = checker.is_activate() 
			#if joined channel was created - returns list with objects of all positive results
			cchannel = checker.is_created_channel(after.channel.id) 
			#creating channel
			if ch_type:
				channel_name = random.choice(channel_names[ch_type]) #getting channel name

				v_overwrites = {} #None except it's a private channel
				if ch_type == "priv": #giving member special perms when private channel
					v_overwrites = {
						member: discord.PermissionOverwrite(manage_permissions=True, manage_channels=True, connect=True), #give member connect and manage rights 
            			member.guild.default_role: discord.PermissionOverwrite(connect=False)
					}
				#creating channels
				v_channel = await member.guild.create_voice_channel(
								channel_name[0].format(member.name),
								category=after.channel.category, overwrites=v_overwrites)
				t_channel = await member.guild.create_text_channel(
								channel_name[1].format(member.name),
								category=after.channel.category,
								overwrites={member: discord.PermissionOverwrite(view_channel=True),
								member.guild.default_role: discord.PermissionOverwrite(view_channel=False)})

				#writing new channels to db
				db = sqltils.DbConn(db_file, member.guild.id, "created_channels")
				db.write_server_table((ch_type, v_channel.id, t_channel.id,
										time.strftime("%Y-%m-%d %H:%M:%S"), config.VERSION_SQL))
				
				if l_channel:
					await l_channel.send(embed=utils.make_embed(name="Created Voicechannel",
							value=f"{member.mention} created `{v_channel}` with {t_channel.mention}",
							color=discord.Color.green()))

				#moving creator to his channel
				await member.move_to(v_channel, reason=f'{member} issued creation')

			elif cchannel: #adding member to textchannel, if member joined created channel 
				t_channel, overwrites = update_text_channel(cchannel)
				await t_channel.edit(overwrites=overwrites)


		if before.channel: #if member leaves channel
			cchannel = checker.is_created_channel(before.channel.id)

			if before.channel.members == [] and cchannel: #if channel is empty -> delete
				v_channel = member.guild.get_channel(cchannel[0].channel)
				t_channel = member.guild.get_channel(cchannel[0].linked_channel)
				#check if archive is given and if channel contains messages to archive
				try: #trying to archive category - throws an error when category is full 
					if (archive := checker.get_archive()) and t_channel.last_message != None:
						await t_channel.edit(category=archive, reason="Voice is empty, this channel not")
					
					else: #empty channel
						await t_channel.delete(reason="Channel is empty and not needed anymore")
					
					checker.del_entry(v_channel.id) #removing entry from db
					await v_channel.delete(reason="Channel is empty")
					if l_channel: #logging
						await l_channel.send(embed=utils.make_embed(name="Created Voicechannel",
								value=f"{member.mention} created `{v_channel}` with {t_channel.mention}",
								color=discord.Color.green()))
				
				#happens when if archive is full
				except discord.errors.HTTPException:
					await l_channel.send(embed=utils.make_embed(name="ERROR", color=discord.Color.red(),
								value=f"This error probably means that the archive category is full, please check it and \n \
										set a new one or delete older channels - Nothing was deleted"))
					

			elif cchannel: #removing member from textchannel when left
				t_channel = member.guild.get_channel(cchannel[0].linked_channel)
				t_channel, overwrites = update_text_channel(cchannel)
				await t_channel.edit(overwrites=overwrites)


def setup(bot):
	bot.add_cog(VoiceChannelCreator(bot))