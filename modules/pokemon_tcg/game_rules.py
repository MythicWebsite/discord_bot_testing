from modules.pokemon_tcg.game_classes import PokeCard, PokePlayer, PokeGame
# from discord.ui import Button, Select
from discord.components import SelectOption
# from modules.pokemon_tcg.generic_buttons import Generic_Select
from modules.pokemon_tcg.rule_buttons import Switch_Select
import modules.pokemon_tcg.poke_game_buttons as edit_view

def rule_playable(game_data:PokeGame, player:PokePlayer, card:PokeCard, rule_type:str) -> bool:
    playable = True
    if not card.rules.get(rule_type, None):
        return False
    for rule in card.rules.get(rule_type, []):
        if rule["action"] == "draw":
            if rule.get("target", "self") == "self":
                if len(player.deck) < rule.get("amount", 1):
                    playable = False
            elif rule.get("target", "self") == "opponent":
                if len(game_data.players[1 - player.p_num].deck) < rule.get("amount", 1):
                    playable = False
        elif rule["action"] == "switch":
            if rule.get("target", "self") == "self":
                if len(player.bench) == 0:
                    playable = False
            elif rule.get("target", "self") == "opponent":
                if len(game_data.players[1 - player.p_num].bench) == 0:
                    playable = False
    return playable

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

async def do_rule(game_data:PokeGame, player:PokePlayer, card:PokeCard = None, rule_type:str = None, rules: list[dict] = "fresh"):
    if rules == "fresh":
        rules = card.rules.get(rule_type, [])
    else:
        rules.pop(0)
    if len(rules) > 0:
        if rules[0]["action"] == "draw":
            await draw_rule(game_data, player, rules)
        elif rules[0]["action"] == "switch":
            await switch_rule(game_data, player, rules)
    else:
        for player in game_data.players:
            if len(player.temp_choices) > 0 or player.temp:
                if player.temp:
                    player.discard.append(player.temp)
                    player.temp = None
                for _ in player.temp_choices:
                    player.discard.append(player.temp_choices.pop())
                await edit_view.redraw_player(game_data, player, msg_type = "zone")
        player.com = "Idle"
  
async def draw_rule(game_data:PokeGame, player:PokePlayer, rules: list[dict]):
    target = rules[0].get("target", "self")
    amount = rules[0].get("amount",1)
    if target == "self":
        await player.draw(amount)
        await edit_view.redraw_player(game_data, player, msg_type = "hand", buttons=False)
    elif target == "opponent":
        await game_data.players[1 - player.p_num].draw(amount)
        await edit_view.redraw_player(game_data, game_data.players[1 - player.p_num], msg_type = "hand", buttons=False)
    await do_rule(game_data, player, rules = rules)
        
async def switch_rule(game_data:PokeGame, player:PokePlayer, rules: list[dict]):
    target = rules[0].get("target", "self")
    choice = rules[0].get("choice", "self")
    # player.com = "Switching"
    options = []
    for i, card in enumerate(player.bench if target == "self" else game_data.players[1 - player.p_num].bench):
        options.append(SelectOption(label=f"{card.name} - Bench {i + 1}", value=i))
    choosing_player = player if choice == "self" else game_data.players[1 - player.p_num]
    choosing_player.view.clear_items()
    choosing_player.view.add_item(Switch_Select(game_data, choosing_player, "Choose a pokemon to switch", options, rules))
    await choosing_player.message.edit(view = choosing_player.view)
    
    