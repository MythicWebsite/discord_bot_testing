from modules.pokemon_tcg.game_classes import PokeCard, PokePlayer, PokeGame
from discord.ui import Button
from discord.components import SelectOption
from modules.pokemon_tcg.rule_buttons import Switch_Select, Search_Select
from modules.pokemon_tcg.poke_messages import game_msg
from copy import deepcopy
import modules.pokemon_tcg.poke_game_buttons as edit_view
from random import shuffle

def rule_playable(game_data:PokeGame, player:PokePlayer, card:PokeCard, rule_type:str) -> bool:
    if not card.rules.get(rule_type, None):
        return False
    for rule in card.rules[rule_type]:
        if rule["action"] == "draw":
            if rule.get("target", "self") == "self":
                if len(player.deck) < rule.get("amount", 1):
                    return False
            elif rule.get("target", "self") == "opponent":
                if len(game_data.players[1 - player.p_num].deck) < rule.get("amount", 1):
                    return False
        elif rule["action"] == "switch":
            if rule.get("target", "self") == "self":
                if len(player.bench) == 0:
                    return False
            elif rule.get("target", "self") == "opponent":
                if len(game_data.players[1 - player.p_num].bench) == 0:
                    return False
        elif rule["action"] == "search":
            if rule.get("target", "self") == "self":
                target_player = player
            else:
                target_player = game_data.players[1 - player.p_num]
            from_loc = get_location(target_player, rule.get("from_loc", None))
            if rule.get("from_loc", None) == "hand" or rule.get("from_loc", None) == "discard" or rule.get("from_loc", None) == "bench":
                if rule.get("specific_amount", None) is not None:
                    if len(from_loc) == 0:
                        return False
                    if not check_specifics(from_loc, rule["specific_amount"]):
                        return False
            if rule.get("amount", 0) != "all":
                if len(from_loc) < rule.get("amount", 1) and rule.get("from_loc", None) != "hand":
                    return False
                elif len(from_loc) - 1 < rule.get("amount", 1) and rule.get("from_loc", None) == "hand":
                    return False
    return True

def card_type_playable(game_data: PokeGame, player: PokePlayer, card: PokeCard ):
    if card.supertype == "Energy" and not player.energy:
        return True
    if card.supertype == "Trainer":
        if rule_playable(game_data, player, card, "play"):
            return True
    if card.supertype == "Pok\u00e9mon":
        if "Basic" in card.subtypes:
            if len(player.bench) < 5:
                return True
        else:
            if card.evolvesFrom == player.active.name and player.active.turn_cooldown:
                return True
            for field_card in player.bench:
                if card.evolvesFrom == field_card.name and field_card.turn_cooldown:
                    return True      
    return False

def check_specifics(card_list: list[PokeCard], specific_amount: dict, return_options: bool = False, no_min: bool = False):
    specific_amount = deepcopy(specific_amount)
    dupes = []
    options = []
    for card_num, card in enumerate(card_list):
        check = False
        if isinstance(specific_amount.get(card.supertype), int):
            if specific_amount[card.supertype] != "all":
                specific_amount[card.supertype] -= 1
            check = card.supertype
        elif isinstance(specific_amount.get("basic_mon"), int) and "Basic" in card.subtypes and card.supertype == "Pok\u00e9mon":
            if specific_amount["basic_mon"] != "all":
                specific_amount["basic_mon"] -= 1
            check = "basic_mon"
        elif isinstance(specific_amount.get("evo_mon"), int) and (card.supertype == "Stage 1" or card.supertype == "Stage 2"):
            if specific_amount["evo_mon"] != "all":
                specific_amount["evo_mon"] -= 1
            check = "evo_mon"
        elif isinstance(specific_amount.get("basic_energy"), int) and card.supertype == "Energy" and "Basic" in card.subtypes:
            if specific_amount["basic_energy"] != "all":
                specific_amount["basic_energy"] -= 1
            check = "basic_energy"
        if check and return_options:
            if not card.name in dupes:
                dupes.append(card.name)
                options.append(SelectOption(label=f"{card.name}", value=f"{check}_{card_num}"))
    for specific in specific_amount:
        if specific_amount[specific] > 0 and specific_amount[specific] != "all":
            return False
    if return_options:
        if no_min:
            options.append(SelectOption(label="None", value="None_None"))
        return options
    else:
        return True

async def do_rule(game_data:PokeGame, player:PokePlayer, card:PokeCard = None, rule_type:str = None, rules: list[dict] = "fresh"):
    if rules == "fresh":
        rules = deepcopy(card.rules.get(rule_type, []))
        await edit_view.redraw_player(game_data, player, msg_type = "hand")
    else:
        rules.pop(0)
    if len(rules) > 0:
        if rules[0]["action"] == "draw":
            await draw_rule(game_data, player, rules)
        elif rules[0]["action"] == "switch":
            await switch_rule(game_data, player, rules)
        elif rules[0]["action"] == "search":
            await search_rule(game_data, player, rules)
    else:
        for player in game_data.players:
            if len(player.temp_discard) > 0 or player.temp:
                if player.temp:
                    player.discard.append(player.temp)
                    player.temp = None
                for _ in player.temp_discard:
                    player.discard.append(player.temp_discard.pop())
                await edit_view.redraw_player(game_data, player, msg_type = "zone")
            if game_data.active == player:
                edit_view.turn_view(game_data, player)
                await player.message.edit(view = player.view)
  
async def draw_rule(game_data:PokeGame, player:PokePlayer, rules: list[dict]):
    target = rules[0].get("target", "self")
    amount = rules[0].get("amount",1)
    if target == "self":
        await player.draw(amount)
        # if len(rules) > 1:
        await edit_view.redraw_player(game_data, player, msg_type = "hand", buttons=False)
    elif target == "opponent":
        await game_data.players[1 - player.p_num].draw(amount)
        await edit_view.redraw_player(game_data, game_data.players[1 - player.p_num], msg_type = "hand", buttons=False)
    await do_rule(game_data, player, rules = rules)
        
async def switch_rule(game_data:PokeGame, player:PokePlayer, rules: list[dict]):
    target = rules[0].get("target", "self")
    choice = rules[0].get("choice", "self")
    options = []
    for i, card in enumerate(player.bench if target == "self" else game_data.players[1 - player.p_num].bench):
        options.append(SelectOption(label=f"{card.name} - Bench {i + 1}", value=i))
    choosing_player = player if choice == "self" else game_data.players[1 - player.p_num]
    choosing_player.view.clear_items()
    choosing_player.view.add_item(Switch_Select(game_data, choosing_player, "Choose a pokemon to switch", options, rules))
    choosing_player.view.add_item(Button(label = "Retreat", disabled = True))
    choosing_player.view.add_item(Button(label = "End Turn", disabled = True))
    await choosing_player.message.edit(view = choosing_player.view)

def get_location(player: PokePlayer, location: str):
    if location == "hand":
        return player.hand
    elif location == "discard":
        return player.discard
    elif location == "bench":
        return player.bench
    elif location == "deck":
        return player.deck
    elif location == "prize":
        return player.prize
    elif location == "temp_discard":
        return player.temp_discard

async def search_rule(game_data:PokeGame, player:PokePlayer, rules: list[dict]):
    target_player = player if rules[0].get("target", "self") == "self" else game_data.players[1 - player.p_num]
    from_loc = get_location(target_player, rules[0].get("from_loc", "self"))
    to_loc = get_location(player, rules[0].get("to_loc", "hand"))
    amount = rules[0].get("amount", 1)
    specific_amount = rules[0].get("specific_amount", False)
    all_check = False
    if specific_amount:
        amount = 0
        for option in specific_amount:
            if specific_amount[option] == "all":
                all_check = True
            else:
                amount += specific_amount[option]
    elif amount == "all":
        all_check = True
    if not all_check:
        if specific_amount:
            options = check_specifics(from_loc, specific_amount, return_options = True, no_min = rules[0].get("no_min", False))
        else:
            options = []
            dupes = []
            for i, card in enumerate(from_loc):
                if card.name not in dupes:
                    dupes.append(card.name)
                    options.append(SelectOption(label=f"{card.name}", value=f"blank_{i}"))
        choosing_player = player if rules[0].get("choice","self") == "self" else game_data.players[1 - player.p_num]
        choosing_player.view.clear_items()
        choosing_player.view.add_item(Search_Select(game_data, choosing_player, f"Send a card to {rules[0]['to_loc'] if rules[0]['to_loc'] != 'temp_discard' else 'discard'} - {amount} left", options, rules, from_loc, to_loc, amount))
        choosing_player.view.add_item(Button(label = "Retreat", disabled = True))
        choosing_player.view.add_item(Button(label = "End Turn", disabled = True))
        await choosing_player.message.edit(view = choosing_player.view)
    elif specific_amount:
        for card in from_loc:
            check = False
            if card.supertype in specific_amount:
                check = True
            elif "basic_mon" in specific_amount and "Basic" in card.subtypes and card.supertype == "Pok\u00e9mon":
                check = True
            elif "evo_mon" in specific_amount and (card.supertype == "Stage 1" or card.supertype == "Stage 2"):
                check = True
            elif "basic_energy" in specific_amount and card.supertype == "Energy" and "Basic" in card.subtypes:
                check = True
            if check:
                to_loc.append(from_loc.pop(from_loc.index(card)))
        await edit_view.redraw_player(game_data, target_player, buttons=False)
        await do_rule(game_data, player, rules = rules)
    else:
        for _ in range(len(from_loc)):
            to_loc.append(from_loc.pop())
        if rules[0].get("to_loc", "hand") == "deck":
            shuffle(to_loc)
        await game_msg(game_data.info_thread, f"{player.user.display_name} sent all cards from their {rules[0]['from_loc']} to their {rules[0]['to_loc']}")
        await edit_view.redraw_player(game_data, target_player, buttons=False)
        await do_rule(game_data, player, rules = rules)
    