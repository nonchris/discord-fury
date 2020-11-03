#pip
import discord
from discord.ext import commands 

#own files
import data.config as config

"""This custom help command is a perfect replacement for the default one on any Discord Bot written in Discord.py!
However, you must put "bot.remove_command('help')" in your bot, and the command must be in a cog for it to work.

Written by Jared Newsom (AKA Jared M.F.)! - https://gist.github.com/StudioMFTechnologies/ad41bfd32b2379ccffe90b0e34128b8b
Modified by ceron21 for own bot"""

class Help(commands.Cog):
	"""
    Sends this help message
    """
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	#@commands.has_permissions(add_reactions=True,embed_links=True)
	async def help(self,ctx,*cog):
	    """Zeigt alle Module des Bots an"""
	    prefix = config.PREFIX
	    try:
	    	#checks if cog parameter was given
	    	#if not: general help
	        if not cog:
	            """Cog listing.  What more?"""
	            #Title & Introduction
	            owner=ctx.guild.get_member(config.OWNER)
	            halp=discord.Embed(title='Commands and modules', color=discord.Color.blue(),
	                               description='Use `%shelp <module>` to gain more information about that module :smiley:\n' %prefix)
	            #iterating trough cogs, gaining descriptions
	            cogs_desc = ''
	            for x in self.bot.cogs:
	                cogs_desc += ('`{}` {}'.format(x,self.bot.cogs[x].__doc__)+'\n')
	            #printing cogs
	            halp.add_field(name='Modules',value=cogs_desc[0:len(cogs_desc)-1],inline=False)
	            
	            #interating trough uncatheogorized commands
	            cmds_desc = ''
	            for y in self.bot.walk_commands():
	            	#if cog not in a cog
	                if not y.cog_name and not y.hidden:
	                    cmds_desc += ('{} - {}'.format(y.name,y.help)+'\n')
	            #adding those commands to embed
	            if cmds_desc:
	            	halp.add_field(name='Not belonging to a module',value=cmds_desc[0:len(cmds_desc)-1],inline=False)
	            #setting information about author
	            halp.add_field(name="About", value="This Bot is developed and maintained by %s \nPlease contact me for Ideas and Bugs\n" 
	            									"You can find me on https://discord.gg/sn1054"%(owner.mention))
	            halp.set_footer(text="Bot is running %s" %config.VERSION)

	            #output
	            #await ctx.message.add_reaction(emoji='✉') #adding reaction to !help
	            #await ctx.message.author.send('',embed=halp) #sending via PN
	            await ctx.send('',embed=halp)
	        
	        else:
	        	#too many cogs requested
	            """Helps me remind you if you pass too many args."""
	            if len(cog) > 1:
	                halp = discord.Embed(title='Error!',description="That's to much modules at once :sweat_smile:\n Please only ask for one module at the time",color=discord.Color.red())
	                await ctx.message.author.send('',embed=halp)
	            
	            else:
	                splice = cog[0]
	                cog = splice[0].upper() + splice[1:].lower()
	                #printing commands of cog
	                """Command listing within a cog."""
	                found = False
	                #finding Cog
	                for x in self.bot.cogs:
	                    #for y in cog:
	                    if x == cog: 
	                        #making title
	                        halp=discord.Embed(title=cog+' - Commands',description=self.bot.cogs[cog].__doc__, color=discord.Color.green())
	                        for c in self.bot.get_cog(cog).get_commands():
	                            if not c.hidden: #if cog not hidden
	                                halp.add_field(name="%s%s"%(config.PREFIX,c.name),value=c.help,inline=False)
	                        found = True
	                #if cog not found
	                if not found:
	                    """Reminds you if that cog doesn't exist."""
	                    halp = discord.Embed(title='Error!',description="The module %s doesn't exist :scream:" %cog, color=discord.Color.red())
	                #sending message with information
	                # else:
	                #     await ctx.message.add_reaction(emoji='✉')
	                #await ctx.message.author.send('',embed=halp)
	                await ctx.send('',embed=halp)
	    except Exception as e:
	        print(e)
	        await ctx.send("Sorry, I can't send any embeds.")
        
def setup(bot):
    bot.add_cog(Help(bot))