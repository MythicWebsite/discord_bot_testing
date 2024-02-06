from discord.ui import Select
from discord import Interaction

class Generic_Select(Select):
    def __init__(self, placeholder: str, options: list, disabled: bool = False):
        super().__init__(placeholder = placeholder, options = options, disabled=disabled)
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True