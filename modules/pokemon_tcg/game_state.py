from discord import User
import random

class PokeGame():
    def __init__(self, p1: User, p2: User) -> None:
        self.p1_deck = None
        self.p2_deck = None
        self.p1 = p1
        self.p2 = p2
        self.p1_hand = []
        self.p2_hand = []
        self.active = random.randint(0,1)
        self.winner = None
        self.p1_grave = []
        self.p2_grave = []
        self.p1_bench = [None,None,None,None,None]
        self.p2_bench = [None,None,None,None,None]
        self.p1_active = None
        self.p2_active = None
        
    def setup(self, p1_deck: list, p2_deck: list):
        random.shuffle(p1_deck)
        random.shuffle(p2_deck)
        self.p1_deck = p1_deck
        self.p2_deck = p2_deck
        for _ in range(7):
            self.p1_hand.append(self.p1_deck.pop())
            self.p2_hand.append(self.p2_deck.pop())