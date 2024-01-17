import os
import shutil
import subprocess
import stat
import json
import requests
from PIL import Image
from io import BytesIO
from time import sleep

def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)

def size_image(img: Image, new_width: int, new_height: int):
    width, height = img.size
    if width < new_width or height < new_height:
        img = img.resize((new_width, new_height))
    else:
        left = (width - new_width)/2
        top = (height - new_height)/2
        right = (width + new_width)/2
        bottom = (height + new_height)/2
        img = img.crop((left, top, right, bottom))
    return img

def update_poke_images():
    "Check for new card images and download them. Does not redownload existing images."
    images_dir = 'data/pokemon_images'
    with open(f'data/pokemon_data/cards.json',encoding="utf-8") as file:
        set_data = json.loads(file.read())
    for poke_set in set_data:
        for card in set_data[poke_set]:
            if "images" in card:
                image_url = set_data[poke_set][card]['images']['small']
                set_dir = os.path.join(images_dir, poke_set)
                image_path = os.path.join(set_dir, f"{set_data[poke_set][card]['id'].replace('?','QM')}.jpg")
                if not os.path.exists(image_path):
                    print(f"Downloading {image_url} to {image_path}")
                    # Download the image
                    response = requests.get(image_url)
                    img = Image.open(BytesIO(response.content)).convert('RGB')

                    img = size_image(img, 240, 330)

                    # Save the image
                    os.makedirs(set_dir, exist_ok=True)
                    img.save(image_path)
    if not os.path.exists('data/pokemon_data/card_back.jpg'):
        print("Downloading card back")
        # Download the image
        response = requests.get('https://images.pokemontcg.io/')
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((245, 342))
        img = size_image(img, 240, 330)

        # Save the image
        img.save('data/pokemon_data/card_back.jpg')

def fix_json_files(dst_dir,git_dir,set_info=False):
    "Fixes json files being  lists instead of dictionaries"
    new_data = {}
    for set_file in os.listdir(git_dir):
        print(set_file)
        if set_file.endswith('.json'):
            with open(os.path.join(git_dir, set_file),encoding="utf-8") as file:
                set_data = json.loads(file.read())
            set_id = set_file.replace('.json', '')
            new_data[set_id] = {}
            for card in set_data:
                new_data[set_id][card['id']] = card
                if set_info:
                    new_data[set_id][card['id']]["set"] = set_id
    with open(dst_dir, 'w',encoding="utf-8") as file:
        json.dump(new_data, file, indent=4)

def update_poke_data():
    "Updates card data to newest data from the pokemon-tcg-data repository."
    # Define the repository and directories
    dst_dir = 'data/pokemon_data/'
    repo_url = 'https://github.com/PokemonTCG/pokemon-tcg-data.git'
    card_back_url = 'https://images.pokemontcg.io/'
    card_back_dst = 'card_back.jpg'
    cards_git_dir = 'pokemon-tcg-data/cards/en'
    cards_dst_dir = 'cards.json'
    decks_git_dir = 'pokemon-tcg-data/decks/en'
    decks_dst_dir = 'decks.json'
    sets_git = 'pokemon-tcg-data/sets'
    sets_dst = 'sets.json'
    commit_file = 'data/pokemon_data/poke_hash.txt'

    if os.path.exists('pokemon-tcg-data'):
        shutil.rmtree('pokemon-tcg-data', onerror=remove_readonly)
    
    # Get the latest commit hash of the remote repository
    remote_commit = subprocess.check_output(['git', 'ls-remote', repo_url, '-h', 'refs/heads/master'])
    remote_commit = str(remote_commit.split()[0])

    # Get the commit hash of the local repository
    try:
        with open(commit_file, 'r') as f:
            local_commit = f.read().strip()
    except Exception:
        local_commit = None

    # If the local repository doesn't exist or is outdated, clone/update it
    if local_commit != remote_commit:
        subprocess.check_call(['git', 'clone', repo_url])
        
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir, onerror=remove_readonly)
            
        # Create destination directory if it doesn't exist
        os.makedirs(dst_dir, exist_ok=True)

        
        print("Creating cards file")
        fix_json_files(os.path.join(dst_dir,cards_dst_dir),cards_git_dir, True)
        print("Creating deck files")
        fix_json_files(os.path.join(dst_dir,decks_dst_dir),decks_git_dir, True)
        print("Creating set file")
        fix_json_files(os.path.join(dst_dir,sets_dst),sets_git)

        # Save the new commit hash
        with open(commit_file, 'w') as f:
            f.write(remote_commit)

        sleep(5)
        
        # Delete the cloned repository
        shutil.rmtree('pokemon-tcg-data', onerror=remove_readonly)
        return True
    else:
        return False