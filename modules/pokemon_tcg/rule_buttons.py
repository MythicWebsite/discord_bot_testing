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
    def __init__(self, game_data: PokeGame, player: PokePlayer, placeholder: str, options: list[SelectOption], rules: list[dict], from_loc: list[PokeCard] = None, to_loc: list[PokeCard] = None, amount: int = 1):
        super().__init__(placeholder = placeholder, options = options)
        self.game_data = game_data
        self.player = player
        self.rules = rules
        self.specific_amount = rules[0].get("specific_amount", None)
        self.from_loc = from_loc
        self.to_loc = to_loc
        allowed = []
        if self.specific_amount:
            amount = 0
            for option in self.specific_amount:
                if self.specific_amount[option] > 0:
                    allowed.append(option)
                    amount += self.specific_amount[option]
        self.amount = amount
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            # self.player.com = "Idle"
            await lock_msg(self.player)
            card_type, card_num = self.values[0].split("_")
            card = self.from_loc.pop(int(card_num))
            self.to_loc.append(card)
            if self.amount > 1 and not card_type == "None":
                if self.specific_amount:
                    self.specific_amount[card_type] -= 1
                    options = game_rules.check_specifics(self.from_loc, self.specific_amount, return_options = True, no_min = self.rules[0].get("no_min", False))
                else:
                    options = []
                    dupes = []
                    for i, card in enumerate(self.from_loc):
                        if card.name not in dupes:
                            dupes.append(card.name)
                            options.append(SelectOption(label=f"{card.name}", value=f"blank_{i}"))
                    
                self.player.view.clear_items()
                self.player.view.add_item(Search_Select(self.game_data, self.player, f"Choose a card - {self.amount - 1} left)", options, self.rules, self.from_loc, self.to_loc, self.amount - 1))
                await edit_view.redraw_player(self.game_data, self.player, msg_type = "hand", buttons=False)
            else:
            # if self.game_data.players[0].com == "Idle" and self.game_data.players[1].com == "Idle":
                self.player.view.clear_items()
                if self.player != self.game_data.active:
                    self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                # else:
                #     edit_view.turn_view(self.game_data, self.game_data.active)
                await self.player.message.edit(view = self.player.view)
                await edit_view.redraw_player(self.game_data, self.player, msg_type = "zone")
                await game_rules.do_rule(self.game_data, self.game_data.active, rules = self.rules)