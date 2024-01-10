from discord.ext import commands
from discord import app_commands, Interaction, Embed
from discord.ui import View
from modules.buttons.test_buttons import *
from modules.player_data import Player_Data
from modules.data_handling.tic_tac_data import Tic_Tac_Data
from modules.buttons.tic_tac_buttons import *

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

    @app_commands.command(name="tic_tac_toe", description="Play a game of tic tac toe")
    async def tic_tac_toe(self, ctx: Interaction):
        tick_tac_data = Tic_Tac_Data(ctx.user, None)
        view = View(timeout = None)
        view.add_item(Tic_Tac_Join_Button(tick_tac_data, "join_1", ctx.user.display_name))
        view.add_item(Tic_Tac_Join_Button(tick_tac_data, "join_2", "Join"))
        await ctx.response.send_message(embed=Embed(title="Tic Tac Toe", description="Click the button to join the game"), view=view)
    
async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))