from discord.components import SelectOption
from discord.ui import Button, Select, View
from modules.pokemon_tcg.game_classes import PokeGame, PokePlayer, PokeCard
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image, generate_card
from modules.pokemon_tcg.poke_messages import game_msg, hand_msg, lock_msg
from modules.pokemon_tcg.poke_game_buttons import turn_view
from discord import Interaction, File, Embed
from random import randint
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
            if len(self.game_data.players) == 2:
                logger.warning("Too many players")
                return
            else:
                new_player = PokePlayer(ctx.user, self.create_temp_deck(), self.game_data.info_thread)
            await game_msg(self.game_data.info_thread, f"{new_player.user.display_name} has joined the game")
            self.game_data.players.append(new_player)
            if len(self.game_data.players) == 2:
                await self.game_data.setup()
                while not self.game_data.players[0].basics_in_hand() and not self.game_data.players[1].basics_in_hand():
                    for player in self.game_data.players:
                        await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                for i, player in enumerate(self.game_data.players):
                    player.view = View(timeout=None)
                    view = View(timeout=None)
                    if player.basics_in_hand() == 0:
                        player.com = "WaitMulligan"
                        player.view.add_item(Button(label = "Waiting...", disabled = True))
                    else:
                        player.com = "SelectActive"
                        player.view.add_item(Select_Startup_Active(self.game_data, player))
                    if i == 1:
                        view.add_item(Refresh_Hand_Button(self.game_data))
                        player.message = await ctx.followup.send(file=File(fp=generate_hand_image(player.hand), filename="hand.png"), view=player.view, ephemeral=True)
                    else:
                        await player.message.edit(embed=None,attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")],view=player.view)
                    await self.game_data.zone_msg[i].edit(content=player.user.display_name,embed=None, view=view, attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
            else:
                view = View(timeout=None)
                new_player.message = await ctx.followup.send(embed=Embed(title="Hand", description="Waiting for game to start"), ephemeral=True)
                view.add_item(Poke_Join_Button(self.game_data))
                await self.game_data.zone_msg[0].edit(embed=Embed(title="", description=f"Player 1: {new_player.user.display_name}"))
                await self.game_data.zone_msg[1].edit(view=view)

    def create_temp_deck(self):
        with open("data/pokemon_data/decks.json", encoding="utf-8") as f:
            deck_data= json.load(f)["base1"]
        with open(f"data/pokemon_data/cards.json", encoding="utf-8") as f:
                set_data = json.load(f)
        deck = []
        for card in deck_data[f"d-base1-{randint(1,5)}"]["cards"]:
            card_set = card["id"].split("-")[0]
            for _ in range(card["count"]):
                deck.append(PokeCard(set_data[card_set][card["id"]]))
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
                deck.append(PokeCard(set_data[card_set][card["id"]]))
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
            await lock_msg(self.player)
            if self.amount > 0:
                await self.player.draw(self.amount)
            if self.game_data.players[1 - self.player.p_num].com == "ReadyForSelect":
                self.player.com = "SetupComplete"
            for i, player in enumerate(self.game_data.players):
                player.view.clear_items()
                if player.com == "SetupComplete":
                    player.view.add_item(Button(label = "Waiting...", disabled = True))
                    await hand_msg(ctx, player, File(fp=generate_hand_image(player.hand), filename="hand.png"))
                    # await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=player.view)
                elif player.com == "WaitMulligan":
                    await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                    if player.basics_in_hand() != 0:
                        player.com = "ReadyForSelect"
                elif player.com == "ReadyForSelect":
                    player.com = "SelectActive"
                    player.view.add_item(Select_Startup_Active(self.game_data, player))
                else:
                    for amount in range(3):
                        player.view.add_item(DrawFromMulligan(self.game_data, player, amount))
                await hand_msg(ctx, player, File(fp=generate_hand_image(player.hand), filename="hand.png"))
                # await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=player.view)
                await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
        
        
class Select_Startup_Active(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Select active pokemon", options = [])
        self.game_data = game_data
        self.player = player
        for card_no, card in enumerate(self.player.hand):
            if "Basic" in card.subtypes and not "Energy" in card.supertype:
                self.options.append(SelectOption(label=card.name, value=card_no))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            await lock_msg(self.player)
            self.player.active = self.player.hand.pop(int(self.values[0]))
            self.player.com = "SelectBench"
            if self.game_data.players[1 - self.player.p_num].com in ["SelectBench", "WaitMulligan","SetupComplete"]:
                for i, player in enumerate(self.game_data.players):
                    player.view.clear_items()
                    if player.com == "SelectBench":
                        await game_msg(self.game_data.info_thread, f"{player.user.display_name} selects their active pokemon")
                        player.view.add_item(Select_Startup_Bench(self.game_data, player))
                    elif player.com == "WaitMulligan":
                        await player.mulligan(File(fp=generate_hand_image(player.hand), filename="hand.png"))
                        player.view.add_item(Button(label = "Waiting...", disabled = True))
                        if player.basics_in_hand() != 0:
                            player.com = "ReadyForSelect"
                    if player.com != "SetupComplete":
                        await hand_msg(ctx, player, File(fp=generate_hand_image(player.hand), filename="hand.png"))
                        # await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=player.view)
                        await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])     
            else:
                self.player.view.clear_items()
                self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                await hand_msg(ctx, self.player, File(fp=generate_hand_image(self.player.hand), filename="hand.png"))
                # await self.player.message.edit(attachments=[File(fp=generate_hand_image(self.player.hand), filename="hand.png")], view=self.player.view)

             
class Select_Startup_Bench(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Select bench pokemon", options = [])
        self.game_data = game_data
        self.player = player
        self.placeholder = "Select bench pokemon"
        if len(player.bench) < 5:
            for card_no, card in enumerate(player.hand):
                if "Basic" in card.subtypes and not "Energy" in card.supertype:
                    self.options.append(SelectOption(label=card.name, value=card_no))
        self.options.append(SelectOption(label="Done", value="done"))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            await lock_msg(self.player)
            if self.values[0] != "done":
                self.player.bench.append(self.player.hand.pop(int(self.values[0])))
                self.player.view.clear_items()
                self.player.view.add_item(Select_Startup_Bench(self.game_data, self.player))
                await self.game_data.zone_msg[self.player.p_num].edit(attachments=[File(fp=generate_zone_image(self.game_data, self.player), filename="zone.jpeg")])
                await hand_msg(ctx, self.player, File(fp=generate_hand_image(self.player.hand), filename="hand.png"))
                # await self.player.message.edit(attachments=[File(fp=generate_hand_image(self.player.hand), filename="hand.png")], view=self.player.view)
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} has placed a benched pokemon")
            elif self.values[0] == "done":
                self.player.com = "SetupComplete"
                self.player.view.clear_items()
                if self.game_data.players[1 - self.player.p_num].com == "SetupComplete":
                    for i, player in enumerate(self.game_data.players):
                        player.com = "Idle"
                        player.view.clear_items()
                        if not self.game_data.active:
                            self.game_data.active = self.game_data.players[randint(0,1)]
                            self.game_data.turn = 1
                        await player.make_prizes()
                        if player != self.game_data.active:
                            player.view.add_item(Button(label = "Waiting...", disabled = True))
                            await player.message.edit(view=player.view)
                        await self.game_data.zone_msg[i].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])
                        await game_msg(self.game_data.info_thread, f"{player.user.display_name} reveals their active pokemon", File(fp=generate_card(player.active), filename="active_pokemon.png"))
                    await game_msg(self.game_data.info_thread, f"{self.game_data.active.user.display_name} won the coin flip and will go first")
                    await self.game_data.active.draw()
                    turn_view(self.game_data, self.game_data.active)
                    await self.game_data.active.message.edit(attachments=[File(fp=generate_hand_image(self.game_data.active.hand), filename="hand.png")], view=self.game_data.active.view)
                elif self.game_data.players[1 - self.player.p_num].com in ["WaitMulligan","ReadyForSelect"]:
                    for i, player in enumerate(self.game_data.players):
                        player.view.clear_items()
                        if player.com == "SetupComplete":
                            player.com = "DrawFromMulligan"
                            for amount in range(3):
                                player.view.add_item(DrawFromMulligan(self.game_data, player, amount))
                            await player.message.edit(view=player.view)
                        else:
                            player.view.add_item(Button(label = "Waiting...", disabled = True))
                            await player.message.edit(view=player.view)
                else:
                    self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                    await self.player.message.edit(view=self.player.view)


class Refresh_Hand_Button(Button):
    def __init__(self, game_data: PokeGame):
        super().__init__(label="Refresh Hand")
        self.game_data = game_data
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            player = None
            for user in self.game_data.players:
                if user.user == ctx.user:
                    player = user
            if player:
                self.disabled = True
                try:
                    await player.message.delete()
                except:
                    pass
                player.message = await ctx.followup.send(file=File(fp=generate_hand_image(player.hand), filename="hand.png"), view=player.view, ephemeral=True)
                self.disabled = False