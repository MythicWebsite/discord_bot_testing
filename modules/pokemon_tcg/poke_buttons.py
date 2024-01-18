from typing import List, Optional
from discord.components import SelectOption
from discord.ui import Button, Select, View
from discord.utils import MISSING
from modules.pokemon_tcg.game_state import PokeGame, PokePlayer
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image, generate_card
from discord import Interaction, File, Embed
from random import randint, shuffle
import logging
import json

logger = logging.getLogger("discord")

class Poke_Join_Button(Button):
    def __init__(self, game_data: PokeGame):
        super().__init__(label="Join")
        self.game_data = game_data
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            if self.game_data.players == []:
                new_player = PokePlayer(ctx.user, self.create_bad_temp_deck(), self.game_data.info_thread)
            elif len(self.game_data.players) > 2:
                logger.warning("Too many players")
                return
            else:
                new_player = PokePlayer(ctx.user, self.create_bad_temp_deck(), self.game_data.info_thread)
            await self.game_data.info_thread.send(f"{new_player.user.display_name} has joined the game")
            self.game_data.players.append(new_player)
            view = View(timeout=None)
            if len(self.game_data.players) == 2:
                await self.game_data.setup()
                while not self.game_data.players[0].basics_in_hand() and not self.game_data.players[1].basics_in_hand():
                    for player in self.game_data.players:
                        await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                for i, player in enumerate(self.game_data.players):
                    p_view = View(timeout=None)
                    if player.basics_in_hand() == 0:
                        player.com = "WaitMulligan"
                    else:
                        player.com = "SelectActive"
                        p_view.add_item(Select_Active(self.game_data, player, "hand"))
                    if i == 1:
                        player.message = await ctx.followup.send(file=File(fp=generate_hand_image(player.hand), filename="hand.png"), view=p_view, ephemeral=True)
                    else:
                        await player.message.edit(embed=None,attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")],view=p_view)
                    await self.game_data.zone_msg[i].edit(content=player.user.display_name,embed=None, view=view, attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
            else:
                new_player.message = await ctx.followup.send(embed=Embed(title="Hand", description="Waiting for game to start"), ephemeral=True)
                view.add_item(Poke_Join_Button(self.game_data))
                await self.game_data.zone_msg[0].edit(embed=Embed(title="", description=f"Player 1: {new_player.user.display_name}"))
                await self.game_data.zone_msg[1].edit(view=view)

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
    
    def create_bad_temp_deck(self):
        with open("data/pokemon_data/mull_deck.json", encoding="utf-8") as f:
            deck_data = json.load(f)["base1"]
        with open(f"data/pokemon_data/cards.json", encoding="utf-8") as f:
                set_data = json.load(f)
        deck = []
        for card in deck_data[f"d-base1-1"]["cards"]:
            card_set = card["id"].split("-")[0]
            for _ in range(card["count"]):
                deck.append(set_data[card_set][card["id"]])
        return deck
        
class DrawFromMulligan(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer, amount: int):
        super().__init__(label=f"Draw {amount}")
        self.game_data = game_data
        self.player = player
        self.amount = amount
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            if self.amount > 0:
                await self.player.draw(self.amount)
            if self.game_data.players[1 - self.player.p_num].com == "ReadyForSelect":
                self.player.com = "SetupComplete"
            for i, player in enumerate(self.game_data.players):
                p_view = View(timeout=None)
                if player.com == "SetupComplete":
                    await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=p_view)
                elif player.com == "WaitMulligan":
                    await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                    if player.basics_in_hand() != 0:
                        player.com = "ReadyForSelect"
                elif player.com == "ReadyForSelect":
                    player.com = "SelectActive"
                    p_view.add_item(Select_Active(self.game_data, player, "hand"))
                else:
                    for i in range(3):
                        p_view.add_item(DrawFromMulligan(self.game_data, player, i))
                    await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=p_view)
                await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=p_view)
                await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
        
        
class Select_Active(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, zone: str = "bench"):
        super().__init__(placeholder = "Select active pokemon", options = [])
        self.game_data = game_data
        self.player = player
        self.zone = zone
        if zone == "hand":
            for card_no, card in enumerate(self.player.hand):
                if "Basic" in card.get("subtypes", {}) and not "Energy" in card.get("supertype", {}):
                    self.options.append(SelectOption(label=card["name"], value=card_no))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            if self.zone == "hand":
                self.player.active = self.player.hand.pop(int(self.values[0]))
                self.player.com = "SelectBench"
                if self.game_data.players[1 - self.player.p_num].com in ["SelectBench", "WaitMulligan","SetupComplete"]:
                    for i, player in enumerate(self.game_data.players):
                        p_view = View(timeout=None)
                        if player.com == "SelectBench":
                            await self.game_data.info_thread.send(content = f"{player.user.display_name} has selected their active pokemon")
                            p_view.add_item(Select_Bench(self.game_data, player, "setup"))
                        elif player.com == "WaitMulligan":
                            await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                            if player.basics_in_hand() != 0:
                                player.com = "ReadyForSelect"
                        if player.com != "SetupComplete":
                            await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=p_view)
                            await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])     
                else:
                    p_view = View(timeout=None)
                    await self.player.message.edit(attachments=[File(fp=generate_hand_image(self.player.hand), filename="hand.png")], view=p_view)

             
class Select_Bench(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, phase: str = None, zone: str = "hand"):
        super().__init__(placeholder = "Select bench pokemon", options = [])
        self.game_data = game_data
        self.player = player
        self.zone = zone
        self.phase = phase
        self.placeholder = "Select bench pokemon"
        if zone == "hand" and len(player.bench) < 5:
            for card_no, card in enumerate(player.hand):
                if "Basic" in card.get("subtypes", {}) and not "Energy" in card.get("supertype", {}):
                    self.options.append(SelectOption(label=card["name"], value=card_no))
        if phase == "setup":
            self.options.append(SelectOption(label="Done", value="done"))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            if self.zone == "hand" and self.phase == "setup" and self.values[0] != "done":
                self.player.bench.append(self.player.hand.pop(int(self.values[0])))
                p_view = View(timeout=None)
                p_view.add_item(Select_Bench(self.game_data, self.player, "setup"))
                await self.game_data.zone_msg[self.player.p_num].edit(attachments=[File(fp=generate_zone_image(self.game_data, self.player), filename="zone.jpeg")])
                await self.player.message.edit(attachments=[File(fp=generate_hand_image(self.player.hand), filename="hand.png")], view=p_view)
                await self.game_data.info_thread.send(content = f"{self.player.user.display_name} has placed a benched pokemon")
            elif self.values[0] == "done":
                self.player.com = "SetupComplete"
                p_view = View(timeout=None)
                if self.game_data.players[1 - self.player.p_num].com == "SetupComplete":
                    for i, player in enumerate(self.game_data.players):
                        await player.make_prizes()
                        await player.message.edit(view=p_view)
                        await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
                        await self.game_data.info_thread.send(content = f"{player.user.display_name} reveals their active pokemon", file=File(fp=generate_card(player.active), filename="active_pokemon.png"))
                elif self.game_data.players[1 - self.player.p_num].com in ["WaitMulligan","ReadyForSelect"]:
                    for i, player in enumerate(self.game_data.players):
                        p_view = View(timeout=None)
                        if player.com == "SetupComplete":
                            player.com = "DrawFromMulligan"
                            for i in range(3):
                                p_view.add_item(DrawFromMulligan(self.game_data, player, i))
                            await player.message.edit(view=p_view)
                        else:
                            await player.message.edit(view=p_view)
                else:
                    await self.player.message.edit(view=p_view)

                    