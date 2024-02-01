from discord import File, Thread, Interaction, Message, ComponentType
from discord.ui import Button, Select, View
from datetime import datetime

class Fake_Player():
    message: Message
    view: View

async def game_msg(thread: Thread, msg: str, image: File = None):
    timestamp = datetime.now().strftime("[%I:%M %p]: ")
    await thread.send(content = f"{timestamp}{msg}", file=image)
    
async def hand_msg(ctx: Interaction, player:Fake_Player, image: File, refresh: bool = False):
    if refresh:
        try:
            await player.message.delete()
        except:
            pass
        player.message = await ctx.followup.send(file = image, view = player.view, ephemeral=True)
    else:
        await player.message.edit(attachments=[image], view = player.view)
    
async def lock_msg(player:Fake_Player):
    for comp in player.view.children:
        if comp.type in [ComponentType.button, ComponentType.select]:
            comp.disabled = True
        if comp.type == ComponentType.select:
            comp.placeholder = "Thinking..."
    await player.message.edit(view = player.view)
    
