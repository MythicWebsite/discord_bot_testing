from discord.ext import commands
from discord import app_commands, Interaction, Embed
from discord.ui import View
from modules.data_handling.tic_tac_data import Tic_Tac_Data
from modules.pokemon_tcg.poke_setup_buttons import Poke_Join_Button
from modules.pokemon_tcg.game_classes import PokeGame
from modules.buttons.tic_tac_buttons import *

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tic_tac_toe", description="Play a game of tic tac toe")
    async def tic_tac_toe(self, ctx: Interaction):
        tick_tac_data = Tic_Tac_Data(ctx.user, None)
        view = View(timeout = None)
        view.add_item(Tic_Tac_Join_Button(tick_tac_data, "join_1", ctx.user.display_name, True))
        view.add_item(Tic_Tac_Join_Button(tick_tac_data, "join_2", "Join"))
        await ctx.response.send_message(embed=Embed(title="Tic Tac Toe", description="Click the button to join the game"), view=view)
    
    @app_commands.command(name="pokemon", description="Play a game of pokemon")
    async def pokemon(self, ctx: Interaction):
        await ctx.response.defer()
        game_data = PokeGame()
        view = View(timeout = None)
        view.add_item(Poke_Join_Button(game_data))
        await ctx.followup.send(content = "View the game logs in this thread")
        msg = await ctx.original_response()
        game_data.info_thread = await msg.create_thread(name="Game log",auto_archive_duration=1440)
        game_data.zone_msg.append(await ctx.channel.send(embed=Embed(title="", description="Player 1: None")))
        game_data.zone_msg.append(await ctx.channel.send(embed=Embed(title="", description="Player 2: None"), view=view))
        game_data.channel = ctx.channel

async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))