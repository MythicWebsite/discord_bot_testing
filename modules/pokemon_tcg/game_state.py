from discord import User, Message
import random
import logging

logger = logging.getLogger("discord")

class PokePlayer():
    def __init__(self, user: User, deck: list) -> None:
        self.user: User = user
        self.deck: list = deck
        self.hand: list = []
        self.bench: list = [None,None,None,None,None]
        self.active: dict = None
        self.prize: list = []
        self.discard: list = []
        self.stadium: dict = None
        self.energy: bool = False
        self.message: Message = None
        self.p_num: int = None
        
    def draw(self, amount: int = 1):
        for _ in range(amount):
            self.hand.append(self.deck.pop())
            
    def make_prizes(self):
        for _ in range(6):
            self.prize.append(self.deck.pop())


class PokeGame():
    def __init__(self) -> None:
        self.players: list[PokePlayer,PokePlayer] = []
        self.zone_p1_msg: Message = None
        self.zone_p2_msg: Message = None
        self.active: PokePlayer = None
        self.winner: PokePlayer = None

    def setup(self):
        logger.info(f"Setting up game with {self.players[0].user.name} and {self.players[1].user.name}")
        self.active = self.players[random.randint(0,1)]
        for player in range(len(self.players)):
            random.shuffle(self.players[player].deck)
            self.players[player].p_num = player
            self.players[player].draw(7)
            self.players[player].make_prizes()


