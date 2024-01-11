from discord.ui import Button
from modules.pokemon_tcg.game_state import PokeGame
from discord import Interaction, ButtonStyle, User
from discord.ui import View
import logging

logger = logging.getLogger("discord")

deck = ["boy", "dad", "mom", "helicopter","boy", "dad", "mom", "helicopter","boy", "dad", "mom", "helicopter","boy", "dad", "mom", "helicopter"]
     
class Poke_Join_Button(Button):
    def __init__(self, game_data: PokeGame, custom_id: str, label: str = "Join", disabled: bool = False):
        super().__init__(label=label, custom_id=custom_id, disabled=disabled)
        self.game_data = game_data
    
    async def callback(self, interaction: Interaction):
        if self.custom_id == "join_2":
            self.diabled = True
            self.game_data.p2 = interaction.user
            view = View(timeout=None)
            self.game_data.setup(deck,deck)
            # for i in range(len(self.game.grid)):
            #     view.add_item(Tic_Tac_Button(self.game, str(i)))
            await interaction.response.edit_message(content=f"Active Player: {self.game_data.p1.display_name if self.game_data.active == 0 else self.game_data.p2.display_name}\nHand 1: {self.game_data.p1_hand}\nHand 2: {self.game_data.p2_hand}",embed=None, view=view)
        else:
            await interaction.response.edit_message(view=self)


