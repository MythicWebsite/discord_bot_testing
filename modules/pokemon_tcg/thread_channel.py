from discord import File, Thread
from datetime import datetime

async def game_msg(thread: Thread, msg: str, image: File = None):
    timestamp = datetime.now().strftime("[%I:%M %p]: ")
    await thread.send(content = f"{timestamp}{msg}", file=image)