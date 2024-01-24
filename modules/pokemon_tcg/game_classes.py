from discord import User, Message, Thread, TextChannel, File
from modules.pokemon_tcg.thread_channel import game_msg
from discord.ui import View
from random import shuffle
import logging

logger = logging.getLogger("discord")

class PokeCard():
    def __init__(self, card: dict) -> None:
        self.name: str = card.get("name", None)
        self.id: str = card.get("id", None)
        self.supertype: str = card.get("supertype", "")
        self.subtypes: list = card.get("subtypes", [])
        self.hp: int = int(card.get("hp", 0))
        self.types: list = card.get("types", [])
        self.evolvesFrom: str = card.get("evolvesFrom", "")
        self.evolvesTo: str = card.get("evolvesTo", "")
        self.abilities: list = card.get("abilities", [])
        self.attacks: list = card.get("attacks", [])
        self.weaknesses: list = card.get("weaknesses", [])
        self.resistances: list = card.get("resistances", [])
        self.retreatCost: list = card.get("retreatCost", [])
        self.rules: list = card.get("rules", [])
        self.set: str = card.get("set", None)
        self.current_hp: int = self.hp
        self.turn_cooldown: bool = False
        self.special_conditions: list = []
        self.attached_mons: list[PokeCard] = []
        self.attached_energy: list[PokeCard] = []
        self.attached_tools: list[PokeCard] = []
        
    def reset(self):
        self.current_hp = self.hp
        self.turn_cooldown = False
        self.special_conditions = []
        
def evolve(card: PokeCard, sub_card: PokeCard):
    card.current_hp = card.hp - (sub_card.hp - sub_card.current_hp)
    for _ in range(len(sub_card.attached_energy)):
        card.attached_energy.append(sub_card.attached_energy.pop())
    for _ in range(len(sub_card.attached_tools)):
        card.attached_tools.append(sub_card.attached_tools.pop())
    sub_card.reset()
    card.attached_mons.append(sub_card)


class PokePlayer():
    def __init__(self, user: User, deck: list[PokeCard], info_thread: Thread) -> None:
        self.user: User = user
        self.deck: list[PokeCard] = deck
        self.hand: list[PokeCard] = []
        self.bench: list[PokeCard] = []
        self.active: PokeCard = None
        self.prize: list[PokeCard] = []
        self.discard: list[PokeCard] = []
        self.stadium: PokeCard = None
        self.energy: bool = False
        self.message: Message = None
        self.p_num: int = None
        self.info_thread: Thread = info_thread
        self.com: str = "Idle"
        self.view: View = None
        
    async def draw(self, amount: int = 1):
        for _ in range(amount):
            if len(self.deck) > 0:
                self.hand.append(self.deck.pop())
        self.hand.sort(key = lambda x: (x.supertype, x.types, x.name))
        await game_msg(self.info_thread, f"{self.user.display_name} drew {amount} card{'s' if amount > 1 else ''}")
            
    async def make_prizes(self):
        for _ in range(6):
            self.prize.append(self.deck.pop())  
        await game_msg(self.info_thread, f"{self.user.display_name} places their prizes")
    
    async def discard_cards(self, amount:int = "All"):
        if amount == "All":
            amount = len(self.hand)
        for _ in range(amount):
            self.discard.append(self.hand.pop())
        await game_msg(self.info_thread, f"{self.user.display_name} discards {amount} card{'s' if amount > 1 else ''}")
    
    def basics_in_hand(self):
        count = 0
        for card in self.hand:
            if "Basic" in card.subtypes and not "Energy" in card.supertype:
                count += 1
        return count
    
    async def mulligan(self, image: File):
        await game_msg(self.info_thread, f"{self.user.display_name} has to take a mulligan, this was their hand.", image)
        for _ in range(7):
            self.deck.append(self.hand.pop())
        shuffle(self.deck)
        await self.draw(7)


class PokeGame():
    def __init__(self) -> None:
        self.players: list[PokePlayer,PokePlayer] = []
        self.zone_msg: list[Message,Message] = []
        self.info_thread: Thread = None
        self.channel: TextChannel = None
        self.active: PokePlayer = None
        self.winner: PokePlayer = None
        self.turn: int = 0

    async def setup(self):
        logger.info(f"Setting up game with {self.players[0].user.name} and {self.players[1].user.name}")
        for i, player in enumerate(self.players):
            shuffle(player.deck)
            player.p_num = i
            await player.draw(7)


