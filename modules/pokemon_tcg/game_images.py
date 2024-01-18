from PIL import Image
from io import BytesIO
from modules.pokemon_tcg.game_state import PokeGame, PokePlayer

def generate_hand_image(hand: list):
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
        cur_card = Image.open(f"data/pokemon_images/{card['set']}/{card['id']}.png")
        # cur_card = cur_card.resize((card_width, card_height))
        x = (i % cards_per_row) * card_width + spacing * (i % cards_per_row)
        y = (i // cards_per_row) * card_height + spacing * (i // cards_per_row)
        hand_image.paste(cur_card, (x, y))
    img_bytes = BytesIO()
    hand_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes
    
def generate_zone_image(game_data: PokeGame, player: PokePlayer):
    card_back = Image.open("data/pokemon_data/card_back.png")
    zone_image = Image.open("data/background.jpg").convert("RGBA")
    card_width = 240
    card_height = 330
    
    #Set up prize cards
    for i, _ in enumerate(player.prize):
        x = (i % 2) * (card_width//2)
        y = (i // 2) * (card_height//2)
        if player.p_num == 0:
            x = zone_image.width - card_width - x
            y = zone_image.height - card_height - y
        zone_image.paste(card_back, (x, y))
    
    #Set up bench
    for i, card in enumerate(player.bench):
        if player.com == "SelectBench":
            cur_card = card_back
        else:
            cur_card = Image.open(f"data/pokemon_images/{card['set']}/{card['id']}.png")
        x = (i % 5) * (card_width) + int(card_width* 1.5 )
        y = 0
        if player.p_num == 0:
            x = zone_image.width - card_width - x
            y = zone_image.height - card_height - y
        zone_image.paste(cur_card, (x, y))
    
    #Set up deck
    if len(player.deck) > 0:
        if player.p_num == 0:
            zone_image.paste(card_back, (0,0))
        else:
            zone_image.paste(card_back, (zone_image.width - card_width, zone_image.height - card_height))
    
    #Set up active pokemon
    if player.active:
        x = zone_image.width//2 - card_width
        y = 0
        if player.p_num == 0:
            y = zone_image.height - card_height
        if not game_data.active and not player.com == "SetupComplete":
            zone_image.paste(card_back, (x, y))
        else:
            zone_image.paste(Image.open(f"data/pokemon_images/{player.active['set']}/{player.active['id']}.png"), (x, y))
    
    img_bytes = BytesIO()
    zone_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes