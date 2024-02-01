from typing import Any
from discord.components import SelectOption
from discord.ui import Button, Select, View
from modules.pokemon_tcg.game_classes import PokeGame, PokePlayer, PokeCard, evolve
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image, generate_card
from modules.pokemon_tcg.poke_messages import game_msg, hand_msg, lock_msg
from modules.pokemon_tcg.game_rules import do_rule, card_type_playable
from modules.pokemon_tcg.generic_buttons import Generic_Select
from discord import Interaction, File
from logging import getLogger
from asyncio import sleep

logger = getLogger("discord")


class Retreat_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer, disabled: bool = False):
        super().__init__(label=f"Retreat", disabled = disabled)
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
            

class Cancel_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label=f"Cancel")
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True  
            self.player.com = "Cancel"
            turn_view(self.game_data, self.player)
            await self.player.message.edit(view=self.player.view)
            
class End_Turn_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer, disabled: bool = False):
        super().__init__(label=f"End Turn", disabled=disabled)
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            other_player = self.game_data.players[1-self.player.p_num]
            self.player.view.clear_items()
            other_player.view.clear_items()
            await self.player.message.edit(view=self.player.view)
            #Resolve special conditions
            
            if len(other_player.deck) == 0:
                await game_msg(self.game_data.info_thread, f"{other_player.user.display_name} has no cards left in their deck, they lose!")
                self.game_data.winner = self.player
                await other_player.message.edit(view=other_player.view)
                return
            self.game_data.turn += 1
            for mon in self.player.bench:
                mon.turn_cooldown = True
            self.player.active.turn_cooldown = True
            self.player.energy = False
            self.game_data.active = other_player
            await game_msg(self.game_data.info_thread, f"It is now {other_player.user.display_name}'s turn - Turn {self.game_data.turn}")
            await other_player.draw()
            turn_view(self.game_data, other_player)
            # await hand_msg(ctx, other_player, generate_hand_image(other_player.hand), True)
            await hand_msg(ctx, self.player, File(fp=generate_hand_image(self.player.hand), filename="hand.png"), True)
            await other_player.message.edit(attachments=[File(fp=generate_hand_image(other_player.hand), filename="hand.png")], view=other_player.view)
            # await self.player.message.edit(view=self.player.view)
            for i, msg in enumerate(self.game_data.zone_msg):
                await msg.edit(attachments=[File(fp=generate_zone_image(self.game_data, self.game_data.players[i]), filename="zone.jpeg")])
            
            
class Play_Card_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, options: list[SelectOption]):
        super().__init__(placeholder = "Play a card", options = options)
        self.game_data = game_data
        self.player = player
        if options[0].value == "None":
            self.disabled = True
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            await lock_msg(self.player)
            card: PokeCard = self.player.hand[int(self.values[0])]
            
            #Resolve playing Energy cards
            if card.supertype == "Energy":
                selected_card = None
                options: list[SelectOption] = []
                options.append(SelectOption(label=f"{self.player.active.name} - Active", value="active"))
                for field_card_no, field_card in enumerate(self.player.bench):
                    options.append(SelectOption(label=f"{field_card.name} - Bench {field_card_no + 1}", value=field_card_no))
                if len(options) == 1:
                    selected_card = options[0].value
                else:
                    self.player.view.clear_items()
                    action_select = Generic_Select(placeholder="Place energy where?", options = options)
                    self.player.view.add_item(action_select)
                    # self.player.view.add_item(Retreat_Button(self.game_data, self.player, True))
                    # self.player.view.add_item(End_Turn_Button(self.game_data, self.player, True))
                    self.player.view.add_item(Cancel_Button(self.game_data, self.player))
                    await self.player.message.edit(view=self.player.view)
                    while not action_select.values and self.player.com != "Cancel":
                        await sleep(0.3)
                    if self.player.com == "Cancel":
                        self.player.com = "Idle"
                        return
                    else:
                        selected_card = action_select.values[0]
                if selected_card:
                    if selected_card == "active":
                        self.player.active.attached_energy.append(self.player.hand.pop(int(self.values[0])))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} on {self.player.active.name}")
                    else:
                        self.player.bench[int(selected_card)].attached_energy.append(self.player.hand.pop(int(self.values[0])))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} on {self.player.bench[int(selected_card)].name}")
                    self.player.energy = True
                    
            #Resolve playing Trainer cards
            elif card.supertype == "Trainer":
                self.player.com = "Playing"
                self.player.temp = self.player.hand.pop(int(self.values[0]))
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} played {card.name}")
                await do_rule(self.game_data, self.player, card, "play")
            
            #Resolve playing Pokemon cards
            elif card.supertype == "Pok\u00e9mon":
                if "Basic" in card.subtypes:
                    self.player.bench.append(self.player.hand.pop(int(self.values[0])))
                    await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} onto their bench", File(fp=generate_card(card), filename="card.png"))
                else:
                    options: list[SelectOption] = []
                    selected_card = None
                    if card.evolvesFrom == self.player.active.name:
                        options.append(SelectOption(label=f"{self.player.active.name} - Active", value="active"))
                    for field_card_no, field_card in enumerate(self.player.bench):
                        if card.evolvesFrom == field_card.name:
                            options.append(SelectOption(label=f"{field_card.name} - Bench {field_card_no + 1}", value=field_card_no))
                    if len(options) == 1:
                        selected_card = options[0].value
                    else:
                        self.player.view.clear_items()
                        action_select = Generic_Select(placeholder="Select a pokemon to evolve", options = options)
                        self.player.view.add_item(action_select)
                        # self.player.view.add_item(Retreat_Button(self.game_data, self.player, True))
                        # self.player.view.add_item(End_Turn_Button(self.game_data, self.player, True))
                        self.player.view.add_item(Cancel_Button(self.game_data, self.player))
                        await self.player.message.edit(view=self.player.view)
                        while not action_select.values and self.player.com != "Cancel":
                            await sleep(0.3)
                        if self.player.com == "Cancel":
                            self.player.com = "Idle"
                            return
                        else:
                            selected_card = action_select.values[0]
                    if selected_card:
                        if selected_card == "active":
                            evolve(card, self.player.active)
                            self.player.active = self.player.hand.pop(int(self.values[0]))
                        else:
                            evolve(card, self.player.bench[int(selected_card)])
                            self.player.bench[int(selected_card)] = self.player.hand.pop(int(self.values[0]))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} evolved their pokemon into {card.name}", File(fp=generate_card(card), filename="card.png"))
            if self.player.com == "Idle":
                turn_view(self.game_data, self.player)
                await redraw_player(self.game_data, self.player)
            

class Use_Ability_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Use an ability", options = [])
        self.game_data = game_data
        self.player = player
        for card_no, card in enumerate(self.player.bench):
            if True: #Determine if card has an ability that can be used
                self.options.append(SelectOption(label=card["name"], value=card_no))
        if self.player.active:
            if True: #Determine if active card has an ability that can be used
                self.options.append(SelectOption(label=self.player.active["name"], value="active"))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
            
class Attack_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Use an attack", options = [])
        self.game_data = game_data
        self.player = player
        if self.player.active:
            if True: #Determine if active card has an attack that can be used
                self.options.append(SelectOption(label=self.player.active["name"], value="active"))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
            
class Inspect_Played_Card_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Inspect a card in play", options = [])
        self.game_data = game_data
        self.player = player
        for card_no, card in enumerate(self.player.hand):
            if True: #Determine if card has an ability that can be used
                self.options.append(SelectOption(label=card["name"], value=card_no))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
            
def turn_view(game_data: PokeGame, player: PokePlayer):
    player.view.clear_items()
    dupes = []
    options = []
    for num, card in enumerate(player.hand):
        if card.name in dupes:
            continue
        dupes.append(card.name)
        if card_type_playable(game_data, player, card):
            options.append(SelectOption(label=card.name, value=num))
        if len(options) > 24:
            break
    if len(options) == 0:
        options.append(SelectOption(label="No cards to play", value="None"))
    player.view.add_item(Play_Card_Select(game_data, player, options))
    player.view.add_item(Retreat_Button(game_data, player, True))
    player.view.add_item(End_Turn_Button(game_data, player))
    game_data.players[1-player.p_num].view.clear_items()
    game_data.players[1-player.p_num].view.add_item(Button(label = "Waiting...", disabled = True))

async def redraw_player(game_data: PokeGame, player: PokePlayer, msg_type: str = None, buttons: bool = True):
    if buttons:
        if player == game_data.active:
            turn_view(game_data, player)
    if msg_type == "hand" or msg_type == None:
        player.hand.sort(key = lambda x: (x.supertype, x.types, x.name))
        await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=player.view)
    if msg_type == "zone" or msg_type == None:
        await game_data.zone_msg[player.p_num].edit(attachments=[File(fp=generate_zone_image(game_data, player), filename="zone.jpeg")])