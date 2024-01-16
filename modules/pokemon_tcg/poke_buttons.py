from discord.ui import Button
from modules.pokemon_tcg.game_state import PokeGame, PokePlayer
from modules.pokemon_tcg.game_images import generate_hand_image, generate_player_image
from discord import Interaction, File, Embed
from discord.ui import View
from random import randint
import logging
import json

logger = logging.getLogger("discord")

class Poke_Join_Button(Button):
    def __init__(self, game_data: PokeGame):
        super().__init__(label="Join")
        self.game_data = game_data
    
    async def callback(self, ctx: Interaction):
        self.disabled = True
        new_player = PokePlayer(ctx.user, self.create_temp_deck())
        self.game_data.players.append(new_player)
        if len(self.game_data.players) == 2:
            view = View(timeout=None)
            self.game_data.setup()
            for i in range(2):
                p_view = View(timeout=None)
                hand = generate_hand_image(self.game_data.players[i].hand)
                p_view.add_item(DrawTestButton(self.game_data, self.game_data.players[i]))
                if i == 0:
                    await self.game_data.players[i].message.edit(embed=None,attachments=[File(fp=hand, filename="hand.jpeg")],view=p_view)
                    await self.game_data.zone_p1_msg.edit(content=None,embed=None, view=view, attachments=[File(fp=generate_player_image(self.game_data.players[0]), filename="zone.jpeg")])
                else:
                    await ctx.response.send_message(file=File(fp=hand, filename="hand.jpeg"), view=p_view, ephemeral=True)
                    self.game_data.players[i].message = await ctx.original_response()
                    await self.game_data.zone_p2_msg.edit(content=None,embed=None, view=view, attachments=[File(fp=generate_player_image(self.game_data.players[1]), filename="zone.jpeg")])
                
            # await self.game_data.zone_mid_msg.edit(content=f"Active Player: {self.game_data.active.user.display_name}",embed=None, view=view)
        else:
            await ctx.response.send_message(embed=Embed(title="Hand", description="Waiting for game to start"), ephemeral=True)
            new_player.message = await ctx.original_response()
            view = View(timeout=None)
            view.add_item(Poke_Join_Button(self.game_data))
            await self.game_data.zone_p1_msg.edit(embed=Embed(title="", description=f"Player 1: {new_player.user.display_name}"))
            await self.game_data.zone_p2_msg.edit(view=view)

    def create_temp_deck(self):
        with open("data/pokemon_decks/base1.json", encoding="utf-8") as f:
            deck_data = json.load(f)
        deck = []
        for card in deck_data[randint(1,4)]["cards"]:
            for _ in range(card["count"]):
                deck.append({"id": card["id"],
                              "set": "base1"})
        return deck
        
class DrawTestButton(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label="Draw")
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        self.player.draw(1)
        hand = generate_hand_image(self.player.hand)
        await ctx.response.edit_message(attachments=[File(fp=hand, filename="hand.png")])