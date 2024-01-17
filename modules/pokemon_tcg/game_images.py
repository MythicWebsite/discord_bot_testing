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

def generate_mid_image(game_data: PokeGame):
    for player in range(len(game_data.players)):
        pass
    
def generate_player_image(player: PokePlayer):
    card_back = Image.open("data/pokemon_data/card_back.png")
    player_image = Image.open("data/background.jpg").convert("RGBA")
    card_width = 240
    card_height = 330
    for i, _ in enumerate(player.prize):
        x = (i % 2) * (card_width//2)
        y = (i // 2) * (card_height//2)
        if player.p_num == 0:
            x = player_image.width - card_width - x
        player_image.paste(card_back, (x, y))
    
    if player.p_num == 0:
        player_image.paste(card_back, (0,0))
    else:
        player_image.paste(card_back, (player_image.width - card_width, player_image.height - card_height))
    
    img_bytes = BytesIO()
    player_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes