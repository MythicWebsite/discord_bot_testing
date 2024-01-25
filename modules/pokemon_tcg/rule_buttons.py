from discord.ui import Select, Button
from modules.pokemon_tcg.game_classes import PokeCard, PokePlayer, PokeGame
from discord.components import SelectOption
from modules.pokemon_tcg.poke_messages import game_msg
from modules.pokemon_tcg.game_images import generate_hand_image, generate_zone_image
import modules.pokemon_tcg.poke_game_buttons as edit_view
from discord import Interaction, File

class Switch_Select(Select):
    def __init__(self, game_data: PokeGame, player: PokePlayer, placeholder: str, options: list, target: str = "self"):
        super().__init__(placeholder = placeholder, options = options, custom_id=target)
        self.game_data = game_data
        self.player = player
    
    async def callback(self, ctx: Interaction):
        await ctx.response.defer()
        if not self.disabled:
            self.disabled = True
            self.player.com = "Idle"
            if self.custom_id == "self":
                target_player = self.player
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} switched their active pokemon with {target_player.bench[int(self.values[0])].name}")
            elif self.custom_id == "opponent":
                target_player = self.game_data.players[1 - self.player.p_num]
                await game_msg(self.game_data.info_thread, f"{self.player.user.display_name} switched {target_player.user.display_name}'s active pokemon with {target_player.bench[int(self.values[0])].name}")
            target_player.temp = target_player.active
            target_player.active = target_player.bench.pop(int(self.values[0]))
            target_player.bench.append(target_player.temp)
            target_player.temp = None
            if self.game_data.players[0].com == "Idle" and self.game_data.players[1].com == "Idle":
                self.player.view.clear_items()
                edit_view.turn_view(self.game_data, self.game_data.active)
                if self.player != self.game_data.active:
                    self.player.view.add_item(Button(label = "Waiting...", disabled = True))
                    self.player.message.edit(view = self.player.view)
                for player in self.game_data.players:
                    await edit_view.redraw_player(self.game_data, player)
                
                # self.game_data.active.view = self.game_data.active.temp_view
                # self.game_data.active.temp_view = None
                # await self.game_data.active.message.edit(attachments=[File(fp=generate_hand_image(self.game_data.active.hand), filename="hand.png")], view=self.game_data.active.view)
                # for player in self.game_data.players:
                #     await self.game_data.zone_msg[player.p_num].edit(attachments=[File(fp=generate_zone_image(self.game_data, player), filename="zone.jpeg")])