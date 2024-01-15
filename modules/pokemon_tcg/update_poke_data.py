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

def update_poke_images():
    "Check for new card images and download them. Does not redownload existing images."
    images_dir = 'data/pokemon_images'
    for set_file in os.listdir('data/pokemon_sets'):
        if set_file.endswith('.json'):
            with open(f'data/pokemon_sets/{set_file}',encoding="utf-8") as file:
                set_data = json.loads(file.read())
            for card in set_data:
                if "images" in card:
                    image_url = card['images']['small']
                    set_dir = os.path.join(images_dir, set_file.replace('.json', ''))
                    image_path = os.path.join(set_dir, f"{card['id'].replace('?','QM')}.png")
                    if not os.path.exists(image_path):
                        print(f"Downloading {image_url} to {image_path}")
                        # Download the image
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))

                        # Crop the image
                        width, height = img.size
                        if width < 240 or height < 330:
                            img = img.resize((240, 330))
                        else:
                            left = (width - 240)/2
                            top = (height - 330)/2
                            right = (width + 240)/2
                            bottom = (height + 330)/2
                            img = img.crop((left, top, right, bottom))

                        # Save the image
                        os.makedirs(set_dir, exist_ok=True)
                        img.save(image_path)

def update_poke_data():
    "Updates card data to newest data from the pokemon-tcg-data repository."
    # Define the repository and directories
    repo_url = 'https://github.com/PokemonTCG/pokemon-tcg-data.git'
    cards_git_dir = 'pokemon-tcg-data/cards/en'
    cards_dst_dir = 'data/pokemon_sets'
    decks_git_dir = 'pokemon-tcg-data/decks/en'
    decks_dst_dir = 'data/pokemon_decks'
    sets_git = 'pokemon-tcg-data/sets/en.json'
    sets_dst = 'data/set_data.json'
    commit_file = 'data/poke_hash.txt'

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
        
        # Create destination directory if it doesn't exist
        os.makedirs(cards_dst_dir, exist_ok=True)
        os.makedirs(decks_dst_dir, exist_ok=True)

        # Copy the directories
        shutil.copytree(cards_git_dir, cards_dst_dir, dirs_exist_ok=True)
        shutil.copytree(decks_git_dir, decks_dst_dir, dirs_exist_ok=True)
        shutil.copy2(sets_git, sets_dst)

        # Save the new commit hash
        with open(commit_file, 'w') as f:
            f.write(remote_commit)

        sleep(5)
        
        # Delete the cloned repository
        shutil.rmtree('pokemon-tcg-data', onerror=remove_readonly)
        return True
    else:
        return False