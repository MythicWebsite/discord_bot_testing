class Player_Data():
    def __init__(self, id):
        self.id = id
        self.data = {"count": 0}
        
    def increment(self, var: str, amount: int = 1):
        if var in self.data:
            self.data[var] += amount