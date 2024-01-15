from PIL import Image
from io import BytesIO

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
    
    hand_image = Image.new('RGB', (image_width, image_height))
    
    for i, card in enumerate(hand):
        cur_card = Image.open(f"data/pokemon_images/{card['set']}/{card['id']}.png")
        x = (i % cards_per_row) * card_width + spacing * (i % cards_per_row)
        y = (i // cards_per_row) * card_height + spacing * (i // cards_per_row)
        hand_image.paste(cur_card, (x, y))
    img_bytes = BytesIO()
    hand_image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes