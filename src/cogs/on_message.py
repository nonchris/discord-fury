import os
import time
import csv
import re

import discord
from discord.ext import commands


class MessageListener(commands.Cog):
	"""
	No commands here, just a message handler
	"""
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):

		lower_content = message.content.lower()
		
		if "hydrated" in lower_content or "hydro" in lower_content: #a secret for my friends :)
			#emote = self.bot.get_emoji("droplet")
			await message.add_reaction('\N{cup with straw}')


def setup(bot):
	bot.add_cog(MessageListener(bot))
