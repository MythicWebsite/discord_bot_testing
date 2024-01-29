from discord.ui import Select, Button
from modules.pokemon_tcg.game_classes import PokeCard, PokePlayer, PokeGame
from discord.components import SelectOption
from modules.pokemon_tcg.poke_messages import game_msg, lock_msg
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image
import modules.pokemon_tcg.poke_game_buttons as edit_view
import modules.pokemon_tcg.game_rules as game_rules
from discord import Interaction, File

class Switch_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, placeholder: str, options: list, rules: list[dict]):
        super().__init__(placeholder = placeholder, options = options)
        self.game_data = game_data
        self.player = player
        self.rules = rules
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            # self.player.com = "Idle"
            target = self.rules[0]["target"]
            await lock_msg(self.player)
            if target== "self":
                target_player = self.player
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} switched their active pokemon with {target_player.bench[int(self.values[0])].name}")
            elif target == "opponent":
                target_player = self.game_data.players[1 - self.player.p_num]
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} switched {target_player.user.display_name}'s active pokemon with {target_player.bench[int(self.values[0])].name}")
            target_player.temp_choices.append(target_player.active)
            target_player.active = target_player.bench.pop(int(self.values[0]))
            target_player.bench.append(target_player.temp_choices.pop())
            # if self.game_data.players[0].com == "Idle" and self.game_data.players[1].com == "Idle":
            self.player.view.clear_items()
            if self.player != self.game_data.active:
                self.player.view.add_item(Button(label = "Waiting...", disabled = True))
            # else:
            #     edit_view.turn_view(self.game_data, self.game_data.active)
            await self.player.message.edit(view = self.player.view)
            await edit_view.redraw_player(self.game_data, target_player, msg_type = "zone")
            await game_rules.do_rule(self.game_data, self.game_data.active, rules = self.rules)


class Search_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, placeholder: str, from_loc: list[PokeCard], to_loc: list[PokeCard], amount: int = 1, specific_amount: dict = False):
        super().__init__(placeholder = placeholder)
        self.game_data = game_data
        self.player = player
        self.amount = amount
        self.specific_amount = specific_amount
        self.from_loc = from_loc
        self.to_loc = to_loc
        self.options = []
        allowed = []
        self.from_loc = self.from_loc
        self.to_loc = self.to_loc
        if specific_amount:
            for option in specific_amount:
                if specific_amount[option] > 0:
                    allowed.append(option)
        dupes: list[PokeCard] = []
        for option_num, option in enumerate(self.from_loc):
            if not option in dupes:
                dupes.append(option)
                check = False
                if option.supertype in allowed or allowed == []:
                    check = True
                elif "basic_mon" in allowed and "Basic" in option.subtypes and option.supertype == "Pok\u00e9mon":
                    check = True
                elif "evo_mon" in allowed and (option.supertype == "Stage 1" or option.supertype == "Stage 2"):
                    check = True
                elif "basic_energy" in allowed and option.supertype == "Energy" and "Basic" in option.subtypes:
                    check = True
                if check:
                    self.options.append(SelectOption(label=f"{option.name} - {option.supertype}", value=f"{option.supertype}_{option_num}"))
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            # self.player.com = "Idle"
            await lock_msg(self.player)
            card_type, card_num = self.values[0].split("_")
            card = self.from_loc.pop(int(card_num))
            self.to_loc.append(card)
            if self.amount > 1:
                if self.specific_amount:
                    self.specific_amount[card_type] -= 1
                self.player.view.clear_items()
                self.player.view.add_item(Search_Select(self.game_data, self.player, f"Choose a card to discard - {self.amount - 1} left)", self.from_loc, self.to_loc, self.amount - 1, self.specific_amount))
                await self.player.message.edit(view = self.player.view)
            else:
            # if self.game_data.players[0].com == "Idle" and self.game_data.players[1].com == "Idle":
                self.player.view.clear_items()
                if self.player != self.game_data.active:
                    self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                else:
                    edit_view.turn_view(self.game_data, self.game_data.active)
                await self.player.message.edit(view = self.player.view)
                await edit_view.redraw_player(self.game_data, self.player, msg_type = "zone")