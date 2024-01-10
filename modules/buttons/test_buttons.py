from discord.ui import Button
from modules.player_data import Player_Data
from discord import Interaction

class Ok_Button(Button):
    def __init__(self, player_data: Player_Data, label: str = "Ok", custom_id: str = "ok_button"):
        super().__init__(label=label, custom_id=custom_id)
        self.player_data = player_data
    
    async def callback(self, interaction: Interaction):
        self.player_data.increment("count", -1 if self.custom_id == "not_ok_button" else 1)
        embed = interaction.message.embeds[0]
        embed.description = f"{self.player_data.data['count']}"
        await interaction.response.edit_message(embed = embed)


