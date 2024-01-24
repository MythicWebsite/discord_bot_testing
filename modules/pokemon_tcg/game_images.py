from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from modules.pokemon_tcg.game_classes import PokeGame, PokePlayer, PokeCard

enegery_loc = "data/pokemon_energy/"

card_back = Image.open("data/pokemon_data/card_back.png")
background = Image.open("data/background.jpg").convert("RGBA")

energy_colors = {
    "Double Colorless Energy": "Colorless-attackb.png",
    "Darkness Energy": "Darkness-attackb.png",
    "Dragon Energy": "Dragon-attackb.png",
    "Fairy Energy": "Fairy-attackb.png",
    "Fighting Energy": "Fighting-attackb.png",
    "Fire Energy": "Fire-attackb.png",
    "Grass Energy": "Grass-attackb.png",
    "Lightning Energy": "Lightning-attackb.png",
    "Metal Energy": "Metal-attackb.png",
    "Psychic Energy": "Psychic-attackb.png",
    "Water Energy": "Water-attackb.png"
}

def generate_card(card: PokeCard):
    card_image = Image.open(f"data/pokemon_images/{card.set}/{card.id}.png")
    img_bytes = BytesIO()
    card_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def generate_hand_image(hand: list[PokeCard]):
    card_width = 240
    card_height = 330
    cards_per_row = 7
    spacing = 0
    total_cards = len(hand)
    rows = (total_cards + cards_per_row - 1) // cards_per_row
    if rows < 1:
        rows = 1
    
    image_width = card_width * cards_per_row + spacing * (cards_per_row -1)
    image_height = card_height * rows + spacing * (rows - 1)
    
    hand_image = Image.new('RGBA', (image_width, image_height))
    
    for i, card in enumerate(hand):
        cur_card = Image.open(f"data/pokemon_images/{card.set}/{card.id}.png")
        x = (i % cards_per_row) * card_width + spacing * (i % cards_per_row)
        y = (i // cards_per_row) * card_height + spacing * (i // cards_per_row)
        hand_image.paste(cur_card, (x, y))
    img_bytes = BytesIO()
    hand_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def energy_icon(x:int, y:int, zone_image: Image, energy: PokeCard, i: int, colorless_offset: int):
    spacing = 43
    energy_image = Image.open(f"{enegery_loc}{energy_colors[energy.name]}")
    new_x = x - energy_image.width//2
    new_y = y + 5 + i*spacing + colorless_offset
    zone_image.paste(energy_image, (new_x, new_y), energy_image)
    if energy.name == "Double Colorless Energy":
        colorless_offset += spacing
        new_y += colorless_offset
        zone_image.paste(energy_image, (new_x, new_y), energy_image)
    return colorless_offset

def health(x:int, y:int, zone_image: Image, health: int, card_width:int):
    font = ImageFont.truetype("data/ARLRDBD.ttf", 34)
    text_draw = ImageDraw.Draw(zone_image)
    text_draw.text((x + card_width - 48, y + 10), f"{health}", font=font, anchor="rt", fill=(200,0,0), stroke_width=5, stroke_fill=(255,255,255))

def generate_zone_image(game_data: PokeGame, player: PokePlayer):
    zone_image = background.copy()
    card_width = 240
    card_height = 330
    
    #Set up prize cards
    for i, _ in enumerate(player.prize):
        x = 0
        y = i * (card_height//5)
        zone_image.paste(card_back, (x, y))
    
    #Set up bench
    for i, card in enumerate(player.bench):
        
        x = (i % 5) * (card_width) + card_width
        y = zone_image.height - card_height
        if player.p_num == 0:
            y = 0
        if not game_data.active:
            zone_image.paste(card_back, (x, y))
        else:
            zone_image.paste(Image.open(f"data/pokemon_images/{card.set}/{card.id}.png"), (x, y))
            health(x, y, zone_image, card.current_hp, card_width)
        if len(card.attached_energy) > 0:
            card.attached_energy.sort(key = lambda x: x.name)
            colorless_offset = 0
            for i, energy in enumerate(card.attached_energy):
                colorless_offset = energy_icon(x, y, zone_image, energy, i, colorless_offset)
        
        
    
    #Set up deck
    if len(player.deck) > 0:
        font = ImageFont.truetype("data/ARLRDBD.ttf", 120)

        x = zone_image.width - card_width
        if player.p_num == 0:
            y = 0
        else:
            y = zone_image.height - card_height
            
        zone_image.paste(card_back, (x,y))
        text_draw = ImageDraw.Draw(zone_image)
        text_draw.text((x + card_width//2, y + card_height//2), f"{len(player.deck)}", font=font, anchor="mm", fill=(255,255,255), stroke_width=15, stroke_fill=(0,0,0))
    
    #Set up active pokemon
    if player.active:
        x = zone_image.width//2 - card_width//2
        y = 0
        if player.p_num == 0:
            y = zone_image.height - card_height
        if not game_data.active:
            zone_image.paste(card_back, (x, y))
        else:
            zone_image.paste(Image.open(f"data/pokemon_images/{player.active.set}/{player.active.id}.png"), (x, y))
            health(x, y, zone_image, player.active.current_hp, card_width)
        if len(player.active.attached_energy) > 0:
            player.active.attached_energy.sort(key = lambda x: x.name)
            colorless_offset = 0
            for i, energy in enumerate(player.active.attached_energy):
                colorless_offset = energy_icon(x, y, zone_image, energy, i, colorless_offset)
        
    
    img_bytes = BytesIO()
    zone_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes