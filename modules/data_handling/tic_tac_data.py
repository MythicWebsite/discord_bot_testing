from random import randint

class Tic_Tac_Data():
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.grid = [0,0,0,
                     0,0,0,
                     0,0,0]
        self.active = randint(0,1)
        self.winner = None
        self.winner_highlight = []
        
    def reset(self):
        self.grid = [0,0,0,
                     0,0,0,
                     0,0,0]
        self.active = randint(0,1)
        self.winner = None
        self.winner_highlight = []
        
    def action(self, player, pos):
        if self.grid[pos] == 0:
            self.grid[pos] = player
            self.active = 1 - self.active
            return True
        return False
    
    def check_win(self):
        for i in range(3):
            if self.grid[i*3] == self.grid[i*3+1] == self.grid[i*3+2] != 0:
                self.winner = self.p1 if self.grid[i*3] == 1 else self.p2
                self.winner_highlight = [i*3, i*3+1, i*3+2]
                return True
            if self.grid[i] == self.grid[i+3] == self.grid[i+6] != 0:
                self.winner = self.p1 if self.grid[i] else self.p2
                self.winner_highlight = [i, i+3, i+6]
                return True
        if self.grid[0] == self.grid[4] == self.grid[8] != 0:
            self.winner = self.p1 if self.grid[0] else self.p2
            self.winner_highlight = [0, 4, 8]
            return True
        if self.grid[2] == self.grid[4] == self.grid[6] != 0:
            self.winner = self.p1 if self.grid[2] else self.p2
            self.winner_highlight = [2, 4, 6]
            return True
        return False
    