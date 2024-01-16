from discord.ext import commands
from discord import app_commands, Interaction, Embed

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="clear", description="Clears the channel")
    async def clear(self, ctx: Interaction):
        if ctx.channel.id == 1196867005316337674:
            await ctx.response.send_message(embed=Embed(title="Cleared", description="Channel is being cleared"), ephemeral=True)
            await ctx.channel.purge()
        else:
            await ctx.response.send_message(embed=Embed(title="Error", description="You can't clear this channel"), ephemeral=True)
            
            
async def setup(bot: commands.Bot):
    await bot.add_cog(ClearCog(bot))