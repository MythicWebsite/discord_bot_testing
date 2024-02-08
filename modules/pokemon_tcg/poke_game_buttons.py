from discord.components import SelectOption
from discord.ui import Button, Select
from modules.pokemon_tcg.game_classes import PokeGame, PokePlayer, PokeCard, evolve
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image, generate_card
from modules.pokemon_tcg.poke_messages import game_msg, hand_msg, lock_msg
from modules.pokemon_tcg.game_rules import do_rule, card_type_playable
from modules.pokemon_tcg.rule_buttons import Switch_Select
from discord import Interaction, File
from logging import getLogger
from copy import deepcopy

logger = getLogger("discord")


def clamp(value: int, smallest: int, largest: int):
    return max(smallest, min(value, largest))

class Retreat_Button(Button):
    def __init__(self, game_data: PokeGame, player: PokePlayer, disabled: bool = False):
        super().__init__(label=f"Retreat", disabled = disabled)
        self.game_data = game_data
        self.player = player
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            options = []
            dupes = []
            cost = deepcopy(self.player.active.retreatCost)
            self.player.view.clear_items()
            await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} has decided to retreat their active pokemon")
            if len(cost) > 0:
                for energy in self.player.active.attached_energy:
                    energy_name = energy.name.split(" Energy")[0]
                    if energy_name in cost or "Colorless" in cost:
                        if not energy_name in dupes:
                            dupes.append(energy_name)
                            options.append(SelectOption(label=energy.name, value=energy_name))
                self.player.view.add_item(Retreat_Select(self.game_data, self.player, options, cost))
            else:
                for num, pokemon in enumerate(self.player.bench):
                    options.append(SelectOption(label=f"{pokemon.name} - Bench {num + 1}", value=num))
                self.player.view.add_item(Switch_Select(self.game_data, self.player, "Select a pokemon to switch to", options, [{"target": "self"}]))
            await redraw_player(self.game_data, self.player, buttons=False)

            
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
            await redraw_player(self.game_data, self.game_data.players[0], msg_type = "zone", buttons=False)
            await redraw_player(self.game_data, self.game_data.players[1], msg_type = "zone", buttons=False)
            
            
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
            refresh = True
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
                    refresh = False
                    self.player.view.clear_items()
                    action_select = Follow_Up_Select(self.game_data, self.player, int(self.values[0]), "Select a pokemon to attach energy to", options, "energy")
                    self.player.view.add_item(action_select)
                    self.player.view.add_item(Retreat_Button(self.game_data, self.player, True))
                    self.player.view.add_item(End_Turn_Button(self.game_data, self.player, True))
                    # self.player.view.add_item(Cancel_Button(self.game_data, self.player))
                    await self.player.message.edit(view=self.player.view)
                if selected_card:
                    if selected_card == "active":
                        self.player.active.attached_energy.append(self.player.hand.pop(int(self.values[0])))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} on {self.player.active.name}",[card, self.player.active])
                    else:
                        self.player.bench[int(selected_card)].attached_energy.append(self.player.hand.pop(int(self.values[0])))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} on {self.player.bench[int(selected_card)].name}", [card, self.player.bench[int(selected_card)]])
                    self.player.energy = True
                    
            #Resolve playing Trainer cards
            elif card.supertype == "Trainer":
                refresh = False
                self.player.temp = self.player.hand.pop(int(self.values[0]))
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} played {card.name}", [card])
                await do_rule(self.game_data, self.player, card, "play")
            
            #Resolve playing Pokemon cards
            elif card.supertype == "Pok\u00e9mon":
                if "Basic" in card.subtypes:
                    self.player.bench.append(self.player.hand.pop(int(self.values[0])))
                    await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {card.name} onto their bench", [card])
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
                        refresh = False
                        self.player.view.clear_items()
                        action_select = Follow_Up_Select(self.game_data, self.player, int(self.values[0]), "Select a pokemon to evolve", options, "evolve")
                        self.player.view.add_item(action_select)
                        self.player.view.add_item(Retreat_Button(self.game_data, self.player, True))
                        self.player.view.add_item(End_Turn_Button(self.game_data, self.player, True))
                        # self.player.view.add_item(Cancel_Button(self.game_data, self.player))
                        await self.player.message.edit(view=self.player.view)
                    if selected_card:
                        if selected_card == "active":
                            evolve(card, self.player.active)
                            self.player.active = self.player.hand.pop(int(self.values[0]))
                        else:
                            evolve(card, self.player.bench[int(selected_card)])
                            self.player.bench[int(selected_card)] = self.player.hand.pop(int(self.values[0]))
                        await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} evolved their pokemon into {card.name}", [card])
            if refresh:
                turn_view(self.game_data, self.player)
                await redraw_player(self.game_data, self.player)
            

class Follow_Up_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, card_hand_loc: int, placeholder: str, options: list[SelectOption], custom_id: str):
        super().__init__(placeholder = placeholder, options = options, custom_id=custom_id)
        self.game_data = game_data
        self.player = player
        self.card_hand_loc = card_hand_loc
        self.card = self.player.hand[card_hand_loc]
        
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            if self.custom_id == "evolve":
                if self.values[0] == "active":
                    evolve(self.card, self.player.active)
                    self.player.active = self.player.hand.pop(int(self.card_hand_loc))
                else:
                    evolve(self.card, self.player.bench[int(self.values[0])])
                    self.player.bench[int(self.values[0])] = self.player.hand.pop(int(self.card_hand_loc))
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} evolved their pokemon into {self.card.name}", [self.card])
            elif self.custom_id == "energy":
                if self.values[0] == "active":
                    self.player.active.attached_energy.append(self.player.hand.pop(int(self.card_hand_loc)))
                    await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {self.card.name} on {self.player.active.name}",[self.card, self.player.active])
                else:
                    self.player.bench[int(self.values[0])].attached_energy.append(self.player.hand.pop(int(self.card_hand_loc)))
                    await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} placed {self.card.name} on {self.player.bench[int(self.values[0])].name}",[self.card, self.player.bench[int(self.values[0])]])
                self.player.energy = True
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
    def __init__(self, game_data: PokeGame, player: PokePlayer, options: list[SelectOption]):
        super().__init__(placeholder = "Use an attack", options = options)
        self.game_data = game_data
        self.player = player
        if options[0].value == "None":
            self.disabled = True
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            await lock_msg(self.player)
            attack = self.player.active.attacks[int(self.values[0])]
            damage = calculate_damage(self.game_data, attack)
            await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} used {attack['name']} for {damage} damage")
            opponent = self.game_data.players[1-self.player.p_num]
            defense_mon = opponent.active
            defense_mon.current_hp = clamp(defense_mon.current_hp - damage, 0, defense_mon.hp)
            self.game_data.turn += 1
            for mon in self.player.bench:
                mon.turn_cooldown = True
            self.player.active.turn_cooldown = True
            self.player.energy = False
            if defense_mon.current_hp == 0:
                await game_msg(self.game_data.info_thread, f"{opponent.user.display_name}'s {defense_mon.name} fainted! {self.player.user.display_name} takes a prize card",[defense_mon])
                self.player.hand.append(self.player.prize.pop())
                await redraw_player(self.game_data, self.player, msg_type = "zone", buttons=False)
                await redraw_player(self.game_data, opponent, msg_type = "zone", buttons=False)
                if len(self.player.prize) == 0:
                    await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} has no cards left in their prize pool, they win!")
                    self.game_data.winner = self.player
                    return
                elif len(opponent.bench) == 0:
                    await game_msg(self.game_data.info_thread, f"{opponent.user.display_name} has no pokemon left in play, they lose!")
                    self.game_data.winner = self.player
                    return
                elif len(opponent.deck) == 0:
                    await game_msg(self.game_data.info_thread, f"{opponent.user.display_name} has no cards left in their deck, they lose!")
                    self.game_data.winner = self.player
                    return
                else:
                    for _ in defense_mon.attached_energy:
                        opponent.discard.append(defense_mon.attached_energy.pop())
                    for _ in defense_mon.attached_tools:
                        opponent.discard.append(defense_mon.attached_tools.pop())
                    for _ in defense_mon.attached_mons:
                        opponent.discard.append(defense_mon.attached_mons.pop())
                    defense_mon.reset()
                    opponent.discard.append(defense_mon)
                    opponent.active = None
                    self.game_data.active = opponent
                    options = []
                    for card_no, card in enumerate(self.game_data.active.bench):
                        options.append(SelectOption(label=card.name, value=card_no))
                    self.player.view.clear_items()
                    self.game_data.active.view.clear_items()
                    self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                    self.game_data.active.view.add_item(Switch_Select(self.game_data, self.game_data.active, "Select a pokemon to switch to", options, [{"target": "self"}, {"action": "draw", "amount": 1}]))
                    await self.player.message.edit(view=self.player.view)
                    await self.game_data.active.message.edit(view=self.game_data.active.view)
            else:
                
                self.game_data.active = opponent
                await game_msg(self.game_data.info_thread, f"It is now {self.game_data.active.user.display_name}'s turn - Turn {self.game_data.turn}")
                await self.game_data.active.draw()
                turn_view(self.game_data, self.game_data.active)
                await redraw_player(self.game_data, self.player)
                await redraw_player(self.game_data, self.game_data.active)
            

def calculate_damage(game_data: PokeGame, attack: int):
    active_mon = game_data.active.active
    defense_mon = game_data.players[1-game_data.active.p_num].active
    for poke_type in active_mon.types:
        for sub_type in defense_mon.weaknesses:
            if poke_type == sub_type.get("type", ""):
                return int(attack["damage"]) * 2
        for sub_type in defense_mon.resistances:
            if poke_type == sub_type.get("type", ""):
                return int(attack["damage"]) + int(sub_type.get("value", 0))
    return int(attack["damage"])

def check_attack(game_data: PokeGame):
    player = game_data.active
    card = player.active
    if card.attacks:
        available_attacks = []
        attacks = deepcopy(card.attacks)
        for attack_no, attack in enumerate(attacks):
            cost: list = deepcopy(attack.get("cost", []))
            attack["attack_no"] = attack_no
            if cost:
                for energy in card.attached_energy:
                    energy_name = energy.name.split(" Energy")[0]
                    if energy_name in cost:
                        cost.remove(energy_name)
                    elif "Colorless" in cost:
                        cost.remove("Colorless")
                        if energy_name == "Double Colorless" and "Colorless" in cost:
                            cost.remove("Colorless")
                if len(cost) == 0:
                    available_attacks.append(attack)
            else:
                available_attacks.append(attack)
        if available_attacks:
            return available_attacks
    return False

def check_retreat(game_data: PokeGame, cost: list = None):
    player = game_data.active
    card = player.active
    if len(player.bench) > 0:
        if not cost:
            cost = deepcopy(card.retreatCost)
        for energy in card.attached_energy:
            energy_name = energy.name.split(" Energy")[0]
            if energy_name in cost:
                cost.remove(energy_name)
            elif "Colorless" in cost:
                cost.remove("Colorless")
                if energy_name == "Double Colorless" and "Colorless" in cost:
                    cost.remove("Colorless")
        if len(cost) == 0:
            return True
    return False


class Retreat_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, options: list[SelectOption], cost: list):
        super().__init__(placeholder = "Discard energy to retreat", options = options)
        self.game_data = game_data
        self.player = player
        self.cost = cost
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            await lock_msg(self.player)
            if self.values[0] == "Double Colorless":
                self.cost.remove("Colorless")
                if "Colorless" in self.cost:
                    self.cost.remove("Colorless")
            elif self.values[0] in self.cost:
                self.cost.remove(self.values[0])
            else:
                self.cost.remove("Colorless")
            
            discarded_card = None
            for energy_no, energy in enumerate(self.player.active.attached_energy):
                if energy.name.split(" Energy")[0] == self.values[0]:
                    discarded_card = self.player.active.attached_energy[energy_no]
                    self.player.discard.append(self.player.active.attached_energy.pop(energy_no))
                    break
            self.player.view.clear_items()
            options = []
            dupes = []
            if len(self.cost) > 0:
                for energy_no, energy in enumerate(self.player.active.attached_energy):
                    energy_name = energy.name.split(" Energy")[0]
                    if energy_name in self.cost or "Colorless" in self.cost:
                        if not energy_name in dupes:
                            dupes.append(energy_name)
                            options.append(SelectOption(label=energy.name, value=energy_name))
                self.player.view.add_item(Retreat_Select(self.game_data, self.player, options, self.cost))
            else:
                for num, pokemon in enumerate(self.player.bench):
                    options.append(SelectOption(label=f"{pokemon.name} - Bench {num + 1}", value=num))
                self.player.view.add_item(Switch_Select(self.game_data, self.player, "Select a pokemon to switch to", options, [{"target": "self"}]))
            await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} discarded {discarded_card.name} from their active pokemon", [discarded_card])
            await redraw_player(self.game_data, self.player, buttons=False)            

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
    options = []
    attacks = check_attack(game_data)
    if attacks: #Determine if active card has an attack that can be used
        for option in attacks:
            options.append(SelectOption(label=option["name"], value=str(option["attack_no"])))
    if len(options) == 0:
        options.append(SelectOption(label="No attacks to use", value="None"))
    player.view.add_item(Attack_Select(game_data, player, options))
    player.view.add_item(Retreat_Button(game_data, player, False if check_retreat(game_data) else True))
    player.view.add_item(End_Turn_Button(game_data, player))
    game_data.players[1-player.p_num].view.clear_items()
    game_data.players[1-player.p_num].view.add_item(Button(label = "Waiting...", disabled = True))

async def redraw_player(game_data: PokeGame, player: PokePlayer, msg_type: str = None, buttons: bool = True):
    if msg_type == "hand" or msg_type == None:
        player.hand.sort(key = lambda x: (x.supertype, x.types, x.name))
        if buttons:
            if player == game_data.active:
                turn_view(game_data, player)
        await player.message.edit(attachments=[File(fp=generate_hand_image(player.hand), filename="hand.png")], view=player.view)
    if msg_type == "zone" or msg_type == None:
        content = " " if player != game_data.active else f"↓{player.user.display_name}↓ ↑{game_data.players[1 - game_data.active.p_num].user.display_name}↑"
        await game_data.zone_msg[0 if player != game_data.active else 1].edit(content = content, attachments=[File(fp=generate_zone_image(game_data, player), filename="zone.jpeg")])