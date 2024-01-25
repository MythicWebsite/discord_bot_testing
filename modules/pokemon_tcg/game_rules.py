from modules.pokemon_tcg.game_classes import PokeCard, PokePlayer, PokeGame

def card_playable(game_data:PokeGame, player:PokePlayer, card:PokeCard, rule_type:str) -> bool:
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
    return playable

async def do_rule(game_data:PokeGame, player:PokePlayer, card:PokeCard, rule_type:str):
    card_rule = card.rules.get(rule_type, [])
    for rule in card_rule:
        if rule["action"] == "draw":
            await draw_rule(game_data, player, rule.get("target", "self"), rule.get("amount",1))
  
async def draw_rule(game_data:PokeGame, player:PokePlayer, target: str = "self", amount: int = 1):
    if target == "self":
        await player.draw(amount)
    elif target == "opponent":
        await game_data.players[1 - player.p_num].draw(amount)