from discord.ui import Button
from modules.pokemon_tcg.game_state import PokeGame
from modules.pokemon_tcg.game_images import generate_hand_image
from discord import Interaction, File
from discord.ui import View
from random import randint
import logging
import json

logger = logging.getLogger("discord")

class Poke_Join_Button(Button):
    def __init__(self, game_data: PokeGame, custom_id: str, label: str = "Join", disabled: bool = False):
        super().__init__(label=label, custom_id=custom_id, disabled=disabled)
        self.game_data = game_data
    
    async def callback(self, interaction: Interaction):
        if self.custom_id == "join_2":
            self.diabled = True
            self.game_data.p2 = interaction.user
            view = View(timeout=None)
            deck1, deck2 = self.create_temp_decks()
            self.game_data.setup(deck1,deck2)
            hand1 = generate_hand_image(self.game_data.p1_hand)
            hand2 = generate_hand_image(self.game_data.p2_hand)
            await interaction.response.edit_message(content=f"Active Player: {self.game_data.p1.display_name if self.game_data.active == 0 else self.game_data.p2.display_name}",embed=None, view=view)
            await interaction.channel.send(file=File(fp=hand1, filename="hand1.png"))
            await interaction.channel.send(file=File(fp=hand2, filename="hand2.png"))
        else:
            await interaction.response.edit_message(view=self)

    def create_temp_decks(self):
        with open("data/pokemon_decks/base1.json", encoding="utf-8") as f:
            deck_data = json.load(f)
        deck1 = []
        deck2 = []
        for card in deck_data[randint(1,4)]["cards"]:
            for _ in range(card["count"]):
                deck1.append({"id": card["id"],
                              "set": "base1"})
        for card in deck_data[randint(1,4)]["cards"]:
            for _ in range(card["count"]):
                deck2.append({"id": card["id"],
                              "set": "base1"})
        return deck1, deck2
        

