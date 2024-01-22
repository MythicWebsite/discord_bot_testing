from discord.components import SelectOption
from discord.ui import Button, Select
from modules.pokemon_tcg.game_classes import PokeGame, PokePlayer, PokeCard
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image, generate_card
from modules.pokemon_tcg.thread_channel import game_msg
from discord import Interaction, File
from logging import getLogger

logger = getLogger("discord")


class Retreat_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label=f"Retreat")
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
            
class End_Turn_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(label=f"End Turn")
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
            self.game_data.active = other_player
            await game_msg(self.game_data.info_thread, f"It is now {other_player.user.display_name}'s turn - Turn {self.game_data.turn}")
            await other_player.draw()
            turn_view(self.game_data)
            await other_player.message.edit(attachments=[File(fp=generate_hand_image(other_player.hand), filename="hand.png")], view=other_player.view)
            for i, msg in enumerate(self.game_data.zone_msg):
                await msg.edit(attachments=[File(fp=generate_zone_image(self.game_data, self.game_data.players[i]), filename="zone.jpeg")])
            
            
class Play_Card_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer):
        super().__init__(placeholder = "Play a card", options = [])
        self.game_data = game_data
        self.player = player
        for card_no, card in enumerate(self.player.hand):
            if True: #Check if card can be played
                self.options.append(SelectOption(label=card["name"], value=card_no))
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            

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
            
            
class Generic_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, options: list):
        super().__init__(placeholder = "Inspect a card in play", options = options)
        self.game_data = game_data
        self.player = player
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            
def turn_view(game_data: PokeGame):
    game_data.active.view.add_item(Retreat_Button(game_data, game_data.active))
    game_data.active.view.add_item(End_Turn_Button(game_data, game_data.active))