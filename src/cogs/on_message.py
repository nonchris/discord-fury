import os
import time
import csv
import re

import discord
from discord.ext import commands

import data.config as config

class MessageListener(commands.Cog):
	"""
	No commands here, just a message handler
	"""
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):
		
		#adding :everyone: on pings

		#adds pings only if I get pinged
		try:
			owner = message.guild.get_member(config.OWNER)
		except:
			owner = None
		#if owner.mentioned_in(message) and message.author.id != config.OWNER:
		if "@%s" %config.OWNER in message.content or "@!%s" %config.OWNER in message.content \
		and message.author.id != config.OWNER and message.guild.id != 760421261649248296:
			try:
				#emote = self.bot.get_emoji(config.emote_id(message.guild.id))
				emote = self.bot.get_emoji(config.EVERYONE_EMOTE)

				await message.add_reaction(emote)
			except:
				None

		elif "hydrated" in message.content or "hydro" in message.content: #a secret for my friends :)
			#emote = self.bot.get_emoji("droplet")
			await message.add_reaction('\N{cup with straw}')


def setup(bot):
	bot.add_cog(MessageListener(bot))
