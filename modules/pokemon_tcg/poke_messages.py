from discord import File, Thread, Interaction
from discord.ui import Button, Select
# from modules.pokemon_tcg.game_classes import PokePlayer
from datetime import datetime

async def game_msg(thread: Thread, msg: str, image: File = None):
    timestamp = datetime.now().strftime("[%I:%M %p]: ")
    await thread.send(content = f"{timestamp}{msg}", file=image)
    
async def hand_msg(ctx: Interaction, player, image: File, refresh: bool = False):
    if refresh:
        try:
            await player.message.delete()
        except:
            pass
        player.message = await ctx.followup.send(file = image, view = player.view, ephemeral=True)
    else:
        await player.message.edit(attachments=[image], view = player.view)
    
async def lock_msg(player):
    for comp in player.message.components:
        if type(comp) == Button or type(comp) == Select:
            comp.disabled = True
        if type(comp) == Select:
            comp.placeholder = "thinking..."
    await player.message.edit(view = player.view)
    
