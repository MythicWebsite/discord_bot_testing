from discord import User, Message, Thread, TextChannel, File
from discord.ui import View
from random import shuffle
import logging

logger = logging.getLogger("discord")

class PokePlayer():
    def __init__(self, user: User, deck: list, info_thread: Thread) -> None:
        self.user: User = user
        self.deck: list = deck
        self.hand: list = []
        self.bench: list = []
        self.active: dict = None
        self.prize: list = []
        self.discard: list = []
        self.stadium: dict = None
        self.energy: bool = False
        self.message: Message = None
        self.p_num: int = None
        self.info_thread: Thread = info_thread
        self.com: str = "Idle"
        self.view: View = None
        
    async def draw(self, amount: int = 1):
        for _ in range(amount):
            self.hand.append(self.deck.pop())
        self.hand.sort(key = lambda x: (x.get('supertype', ''), x.get('types', ''), x.get('name', '')))
        await self.info_thread.send(f"{self.user.display_name} drew {amount} card{'s' if amount > 1 else ''}")
            
    async def make_prizes(self):
        for _ in range(6):
            self.prize.append(self.deck.pop())  
        await self.info_thread.send(f"{self.user.display_name} placed their prizes")      
        
    def basics_in_hand(self):
        count = 0
        for card in self.hand:
            if "Basic" in card.get("subtypes", {}) and not "Energy" in card.get("supertype", {}):
                count += 1
        return count
    
    async def mulligan(self, image: File):
        await self.info_thread.send(content = f"{self.user.display_name} has to take a mulligan, this was their hand.",file=image)
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
        self.phase: str = "setup"

    async def setup(self):
        logger.info(f"Setting up game with {self.players[0].user.name} and {self.players[1].user.name}")
        for i, player in enumerate(self.players):
            shuffle(player.deck)
            player.p_num = i
            await player.draw(7)


