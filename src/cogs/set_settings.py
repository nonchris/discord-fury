#built in
import os
import time
import sql_utils as sqltils

#pip
import discord
from discord.ext import commands

#own files
import utils
import data.config as config

global db_file
db_file = config.DB_NAME


class Settings(commands.Cog):
	"""
	Set / cutsomize default Settings (beta)
	"""
	def __init__(self, bot):
		self.bot = bot


	@commands.command(name="set-voice-channel", aliases=["set-voice", "svc"], help=f"This command \
		allows you to set a custom 'create-voice-channel' channel name\n \
		Usage: \
		`{config.PREFIX}svc [pub-channel | priv-channel] [channel-id]` - alias: `{config.PREFIX}svc`.\n \
		`pub-channel` and `priv-channel` are the options of channels that are created when joining the creation-channel,\
		enter one of those options. \n \
		This option is - obviously - admin only")
	@commands.has_permissions(administrator=True) 
	async def set_voice(self, ctx, setting: str, value: str):
		#possible settings switch -returns same value but nothing if key isn't valid
		settings = {
			"pub-channel": utils.get_chan(ctx.guild, value),
			"priv-channel": utils.get_chan(ctx.guild, value)
		}
		#trying to get a corresponding channel / id
		value = settings.get(setting)
		#if value is "None" this means that there is no such setting or no such value for it
		# -> ensures that the process of getting a correct setting has worked
		if value is not None and value.type == discord.ChannelType.voice:

			#conneting to db - creating a new one if there is none yet
			db = sqltils.DbConn(db_file, ctx.guild.id, "setting")

			#Settings won't be storred if max watched channels are reached
			#-> searching for amaount of matching entries
			if len(db.search_table(value=setting, column="setting")) >= config.SET_LIMIT:

				text = f"Hey, you can't make me watch more than {config.SET_LIMIT} channels for this setting\n \
						If you wanna change the channels I watch use `{config.PREFIX}ds [channel-id]` to remove a channel from your settings"				
				emby = utils.make_embed(color=discord.Color.orange(), name= "Too many entries", value=text)
				await ctx.send(embed=emby)
			
			#writing entry to db - the way things sould go
			else:
				entry = (setting, "value_name", value.id, time.strftime("%Y-%m-%d %H:%M:%S"), config.VERSION_SQL)
				db.write_server_table(entry)

				emby = utils.make_embed(color=discord.Color.green(), name= "Success", value="Setting saved")
				await ctx.send(embed=emby)

		#when false inputs were given
		else:
			value = ("Please ensure that you've entered a valid setting \
					and channel-id for that setting.")
			emby = utils.make_embed(color=discord.Color.orange(), name="Can't get setting", value=value)
			await ctx.send(embed=emby)



	@commands.command(name="get-settings", aliases=["gs"], help=f"\
								Get a list of all watched 'create-voice' channels - alias: `{config.PREFIX}gvc`")
	@commands.has_permissions(administrator=True) 
	async def get_settings(self, ctx):
		"""
		prints set channels
		"""
		db = sqltils.DbConn(db_file, ctx.guild.id, "setting")
		results = db.read_server_table() #gets a list ob entry objects
		
		pub = "__Public Channels:__\n"
		priv = "__Private Channels:___\n"
		log = "__Log Channel__\n"
		archive = "__Archive Category__\n"
		for i in range(len(results)): #building strings
			if results[i].setting == "pub-channel":
				pub += f"`{ctx.guild.get_channel(results[i].value_id)}` with ID `{results[i].value_id}`\n"
				
			elif results[i].setting == "priv-channel":
				priv += f"`{ctx.guild.get_channel(results[i].value_id)}` with ID `{results[i].value_id}`\n"

			elif results[i].setting == "log":
				log += f"`{ctx.guild.get_channel(results[i].value_id)}` with ID `{results[i].value_id}`\n"

			elif results[i].setting == "archive":
				archive += f"`{ctx.guild.get_channel(results[i].value_id)}` with ID `{results[i].value_id}`\n"



		emby = utils.make_embed(color=discord.Color.green(), name="Server Settings", value=f"‌\n{pub}\n {priv}\n{archive}\n{log}")
		await ctx.send(embed=emby)	



	@commands.command(name="delete-setting", aliases=["ds"], help=f"Remove a channel from the list of watched 'create-voice' channels. \n\
						Usage: `{config.PREFIX}ds [channel-id]`, to get a list of all watched channels use `{config.PREFIX}gvc` \n\
						This command will only untrack the channel, it will _not_ delete anything on your server.")
	@commands.has_permissions(administrator=True) 
	async def delete_settings(self, ctx, value):
		"""
		remove set channels
		"""
		if value:
			db = sqltils.DbConn(db_file, ctx.guild.id, "setting")
			try:
				int(value) #fails when string is given
				if len(value) == 18:
					#all checks passed - removing that entry
					db.remove_line(int(value), column="value_id")
					channel = ctx.guild.get_channel(int(value))
					await ctx.send(embed=utils.make_embed(color=discord.Color.green(), name="Deleted",
												value=f"Removed `{channel}` from settings"))
				else:
					raise #enter except

			except:
				emby = utils.make_embed(color=discord.Color.orange(), name="No valid channel ID", value="It seems like you din't \
									give me a valid channel ID to work with")
				await ctx.send(embed=emby)
				#db.remove_line(value, column="value")

		else:
			emby = utils.make_embed(color=discord.Color.orange(), name="No input", value=f"This function requires exactly one input:\n \
								`channel-ID` please give a valid channel ID as argument to remove that channel from \
								the list of watched channels.\n \
								You can get a list of all watched channels with `{config.PREFIX}gs`")
			
			await ctx.send(embed=emby)


	

	@commands.command(name="set-archive", aliases=["sa"], help=f"Set an archive category for created text-channels and log channel.\n\
		Usage: \
		`{config.PREFIX}sa [archive | log] [category-id | channel-id]`.\n \
		Please not that text-channels will only be archived when they contain at least one message, they'll be deleted otherwise. \n \
		This option is - also - admin only")
	@commands.has_permissions(administrator=True) 
	async def set_archive(self, ctx, setting: str, value: str):
		#possible settings switch -returns same value but nothing if key isn't valid
		settings = {
			"archive": utils.get_chan(ctx.guild, value),
			"log": utils.get_chan(ctx.guild, value)
		}
		#trying to get a corresponding channel / id
		value = settings.get(setting)
		#if value is "None" this means that there is no such setting or no such value for it
		#checking if keyword mateches the entered channel type
		# -> ensures that the process of getting a correct setting has worked
		if value is not None and value.type == discord.ChannelType.text and setting == "log" \
									or value.type == discord.ChannelType.category and setting == "archive":

			#conneting to db - creating a new one if there is none yet
			db = sqltils.DbConn(db_file, ctx.guild.id, "setting")

			#Settings won't be storred if max watched channels are reached
			#-> searching for amaount of matching entries
			if len(db.search_table(value=setting, column="setting")) >= 1: #there can only be one archive and log

				text = f"Hey, you can only have one archive and log at once\n \
						If you wanna change those settings use `{config.PREFIX}ds [channel-id]` to remove a channel from your settings"				
				emby = utils.make_embed(color=discord.Color.orange(), name= "Too many entries", value=text)
				await ctx.send(embed=emby)
			
			#writing entry to db - the way things sould go
			else:
				entry = (setting, "value_name", value.id, time.strftime("%Y-%m-%d %H:%M:%S"), config.VERSION_SQL)
				db.write_server_table(entry)

				emby = utils.make_embed(color=discord.Color.green(), name= "Success", value="Setting saved")
				await ctx.send(embed=emby)

		#when false inputs were given
		else:
			value = ("Please ensure that you've entered a valid setting \
					and channel-id for that setting.")
			emby = utils.make_embed(color=discord.Color.orange(), name="Can't get setting", value=value)
			await ctx.send(embed=emby)



def setup(bot):
	bot.add_cog(Settings(bot))

