from discord.ext import commands
from discord import app_commands, Interaction, Embed
from discord.ui import View
from modules.buttons.test_buttons import *
from modules.player_data import Player_Data

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counter = 0
    
    @app_commands.command(name="start", description="huuhhjdjjj")
    async def start(self, ctx: Interaction):
        player_data = Player_Data(ctx.user.id)
        view = View(timeout = None)
        embed = Embed(title=f"{ctx.user.display_name}'s Panel", description=f"{player_data.data['count']}")
        view.add_item(Ok_Button(player_data))
        view.add_item(Ok_Button(player_data, "Not Ok", "not_ok_button"))
        await ctx.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))