from discord.ui import Button
from modules.pokemon_tcg.game_state import PokeGame, PokePlayer
from modules.pokemon_tcg.game_images import generate_hand_image, generate_player_image
from discord import Interaction, File, Embed
from discord.ui import View
from random import randint, shuffle
from asyncio import sleep
import logging
import json

logger = logging.getLogger("discord")

class Poke_Join_Button(Button):
    def __init__(self, game_data: PokeGame):
        super().__init__(label="Join")
        self.game_data = game_data
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        self.disabled = True
        new_player = PokePlayer(ctx.user, self.create_temp_deck(), self.game_data.info_thread)
        self.game_data.players.append(new_player)
        if len(self.game_data.players) == 2:
            view = View(timeout=None)
            await self.game_data.setup()
            for i in range(2):
                p_view = View(timeout=None)
                hand = generate_hand_image(self.game_data.players[i].hand)
                if self.game_data.players[i].basics_in_hand() == 0:
                    p_view.add_item(MulliganButton(self.game_data, self.game_data.players[i]))
                else:
                    p_view.add_item(DrawTestButton(self.game_data, self.game_data.players[i]))
                if i == 0:
                    await self.game_data.players[i].message.edit(embed=None,attachments=[File(fp=hand, filename="hand.png")],view=p_view)
                    await self.game_data.zone_p1_msg.edit(content=self.game_data.players[i].user.display_name,embed=None, view=view, attachments=[File(fp=generate_player_image(self.game_data.players[0]), filename="zone.jpeg")])
                else:
                    self.game_data.players[i].message = await ctx.followup.send(file=File(fp=hand, filename="hand.png"), view=p_view, ephemeral=True)
                    await self.game_data.zone_p2_msg.edit(content=self.game_data.players[i].user.display_name,embed=None, view=view, attachments=[File(fp=generate_player_image(self.game_data.players[1]), filename="zone.jpeg")])

        else:
            new_player.message = await ctx.followup.send(embed=Embed(title="Hand", description="Waiting for game to start"), ephemeral=True)
            # await ctx.original_response()
            view = View(timeout=None)
            view.add_item(Poke_Join_Button(self.game_data))
            await self.game_data.zone_p1_msg.edit(embed=Embed(title="", description=f"Player 1: {new_player.user.display_name}"))
            await self.game_data.zone_p2_msg.edit(view=view)

    def create_temp_deck(self):
        with open("data/pokemon_data/decks.json", encoding="utf-8") as f:
            deck_data = json.load(f)["base1"]
        with open(f"data/pokemon_data/cards.json", encoding="utf-8") as f:
                set_data = json.load(f)
        deck = []
        for card in deck_data[f"d-base1-{randint(1,5)}"]["cards"]:
            card_set = card["id"].split("-")[0]
            for _ in range(card["count"]):
                deck.append(set_data[card_set][card["id"]])
        return deck
        
class DrawTestButton(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label="Draw")
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        await self.player.draw(1)
        hand = generate_hand_image(self.player.hand)
        await self.player.message.edit(attachments=[File(fp=hand, filename="hand.png")])
        
class MulliganButton(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label="Mulligan")
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        await self.game_data.info_thread.send(content = f"{self.player.user.display_name} has taken a mulligan, this was their hand.",file=File(fp=generate_hand_image(self.player.hand), filename="hand.png"))
        for _ in range(len(self.player.hand)):
            self.player.deck.append(self.player.hand.pop())
        shuffle(self.player.deck)
        await self.player.draw(7)
        await self.player.message.edit(attachments=[File(fp=generate_hand_image(self.player.hand), filename="hand.png")])