from discord.ui import Button
from modules.data_handling.tic_tac_data import Tic_Tac_Data
from discord import Interaction, ButtonStyle
from discord.ui import View
import logging

logger = logging.getLogger("discord")

class Tic_Tac_Button(Button):
    def __init__(self, tic_tac_data: Tic_Tac_Data, custom_id: str, emoji: str = "◾", disabled = False, style: ButtonStyle = ButtonStyle.gray):
        super().__init__(emoji=emoji, custom_id=custom_id)
        self.tic_tac_data = tic_tac_data
        self.row = int(custom_id) // 3
        self.disabled = disabled
        self.style = style
    
    async def callback(self, interaction: Interaction):
        slot = int(self.custom_id)
        if (self.tic_tac_data.active == 0 and self.tic_tac_data.p1.id == interaction.user.id) or (self.tic_tac_data.active == 1 and self.tic_tac_data.p2.id == interaction.user.id):
            if self.tic_tac_data.action(1, slot):
                winner = self.tic_tac_data.check_win()
                view = View()
                for i in range(len(self.tic_tac_data.grid)):
                    if self.tic_tac_data.grid[i] == 0:
                        view.add_item(Tic_Tac_Button(self.tic_tac_data, str(i), disabled = True if winner else False))
                    elif self.tic_tac_data.grid[i] == 1:
                        view.add_item(Tic_Tac_Button(self.tic_tac_data, str(i), "❌", True, ButtonStyle.green if i in self.tic_tac_data.winner_highlight else ButtonStyle.gray))
                    else:
                        view.add_item(Tic_Tac_Button(self.tic_tac_data, str(i), "⭕", True, ButtonStyle.green if i in self.tic_tac_data.winner_highlight else ButtonStyle.gray))
                if winner:
                    await interaction.response.edit_message(content=f"{self.tic_tac_data.winner.display_name} won!",embed=None, view=view)
                else:
                    await interaction.response.edit_message(content=f"Active Player: {self.tic_tac_data.p2.display_name}",embed=None, view=view)
            else:
                interaction.response.edit_message(view=self)
        
class Tic_Tac_Join_Button(Button):
    def __init__(self, tic_tac_data: Tic_Tac_Data, custom_id: str, label: str = "Join"):
        super().__init__(label=label, custom_id=custom_id)
        self.tic_tac_data = tic_tac_data
    
    async def callback(self, interaction: Interaction):
        if not self.tic_tac_data.p2 and self.custom_id == "join_2" and self.label == "Join":
            self.tic_tac_data.p2 = interaction.user
            self.label = interaction.user.display_name
        elif not self.tic_tac_data.p1 and self.custom_id == "join_1" and self.label == "Join":
            self.tic_tac_data.p1 = interaction.user
            self.label = interaction.user.display_name
        if self.tic_tac_data.p1 and self.tic_tac_data.p2:
            self.tic_tac_data.reset()
            view = View()
            for i in range(len(self.tic_tac_data.grid)):
                view.add_item(Tic_Tac_Button(self.tic_tac_data, str(i)))
            if self.tic_tac_data.active == 0:
                await interaction.response.edit_message(content=f"Active Player: {self.tic_tac_data.p1.display_name}",embed=None, view=view)
            else:
                await interaction.response.edit_message(content=f"Active Player: {self.tic_tac_data.p2.display_name}",embed=None, view=view)
        else:
            interaction.response.edit_message(view=self)


