import os
import sys
import zlib
import logging
import configparser
from pathlib import Path

import vdf
import requests
from win32com.client import Dispatch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Paths
steam_user_data_path = config.get('Paths', 'steam_user_data_path')
game_installation_paths = [
    path.strip() for path in config.get('Paths', 'game_installation_paths').split(',')
]
steamdir_path = config.get('Paths', 'steamdir_path')
desktop_path = config.get('Paths', 'desktop_path')
grid_folder = os.path.join(steam_user_data_path, 'grid')  # Folder to store grid images
cache_file = "cache.txt"  # Path to the config file in the current directory

# SteamGridDB API Key
steamgriddb_api_key = config.get('SteamGridDB', 'api_key')

# Ensure the grid folder exists
Path(grid_folder).mkdir(parents=True, exist_ok=True)

# Check for selective mode
selective_mode = '-s' in sys.argv


def read_current_games():
    """Read the current games from all the game installation directories."""
    current_games = set()

    for directory in game_installation_paths:
        try:
            # Check if the directory exists, skip if not
            if not os.path.exists(directory):
                logger.warning(
                    f"Directory {directory} does not exist. Skipping."
                )
                continue

            # Get all game folders from this directory
            game_folders = [
                folder for folder in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, folder))
            ]
            current_games.update({folder.lower() for folder in game_folders})
        except Exception as e:
            logger.error(
                f"Error reading game installation directory {directory}: {e}"
            )

    return current_games


def generate_appid(game_name, exe_path):
    """Generate a unique appid for the game based on its exe path and name."""
    unique_name = (exe_path + game_name).encode('utf-8')
    legacy_id = zlib.crc32(unique_name) | 0x80000000
    return str(legacy_id)


def fetch_steamgriddb_image(game_id, image_type):
    """Fetch a single image (first available) of specified type from SteamGridDB."""
    headers = {
        'Authorization': f'Bearer {steamgriddb_api_key}'
    }
    if image_type == 'hero':
        base_url = f'https://www.steamgriddb.com/api/v2/heroes/game/{game_id}'
    else:
        base_url = f'https://www.steamgriddb.com/api/v2/{image_type}s/game/{game_id}'

    response = requests.get(base_url, headers=headers)
    logger.info(
        f"Fetching {image_type} for game ID: {game_id}, URL: {base_url}, "
        f"Status Code: {response.status_code}"
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            return data['data'][0]['url']  # Return the URL of the first image found

    logger.error(f"Failed to fetch {image_type} for game ID: {game_id}")
    return None


def download_image(url, local_path):
    """Download an image from URL and save it locally."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded image from {url} to {local_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
    return False


def save_images(appid, game_id):
    """Save grid, hero, and logo images for the game."""
    image_types = ['grid', 'hero', 'logo']
    for image_type in image_types:
        url = fetch_steamgriddb_image(game_id, image_type)
        if url:
            extension = os.path.splitext(url)[1]

            if image_type == 'grid':
                image_path = os.path.join(grid_folder, f'{appid}p{extension}')
            elif image_type == 'hero':
                image_path = os.path.join(grid_folder, f'{appid}_hero{extension}')
            elif image_type == 'logo':
                image_path = os.path.join(grid_folder, f'{appid}_logo{extension}')
            else:
                continue

            logger.info(
                f"Saving {image_type} image for appid {appid} from {url} to {image_path}"
            )
            if not os.path.exists(image_path):
                if download_image(url, image_path):
                    logger.info(
                        f"Downloaded {image_type} image for appid {appid} from {url}"
                    )


def load_config():
    """Load config file containing selected .exe paths for each game."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return dict(line.strip().split('=', 1) for line in f if '=' in line)
    return {}


def save_config(config_data):
    """Save the selected .exe paths for each game to config file."""
    if selective_mode:  # Only save in selective mode
        with open(cache_file, 'w') as f:
            for game, exe in config_data.items():
                f.write(f"{game}={exe}\n")


def resolve_shortcut_path(lnk_path):
    """Resolve a .lnk shortcut file to its target executable."""
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(lnk_path)
    return shortcut.Targetpath


def get_desktop_shortcuts():
    """Check for .lnk files on the desktop and return a dictionary of shortcuts."""
    desktop_shortcuts = {}
    for file in os.listdir(desktop_path):
        if file.endswith(".lnk"):
            shortcut_path = os.path.join(desktop_path, file)
            try:
                target_path = resolve_shortcut_path(shortcut_path)
                desktop_shortcuts[file.replace(".lnk", "").lower()] = target_path
            except Exception as e:
                logger.error(f"Error resolving shortcut {file}: {e}")
    return desktop_shortcuts


def capitalize_game_name(game_name):
    """Convert a game name to title case (capitalize each word)."""
    return game_name.title()


def prioritize_exes(game_name, exe_files):
    """Prioritize .exe files based on size and if they contain the game name."""

    def score_exe(exe_file):
        """Score the .exe file for prioritization."""
        game_name_lower = game_name.lower().replace(' ', '')  # Normalize the game name
        exe_name = os.path.basename(exe_file).lower().replace(' ', '')

        size = os.path.getsize(exe_file)
        name_match_bonus = 1e9 if game_name_lower in exe_name else 0  # Bonus for name match

        return size + name_match_bonus

    # Sort by score (size and name match)
    return sorted(exe_files, key=score_exe, reverse=True)


def find_largest_exe(game_dir, game_name, existing_in_steam):
    """Find the best .exe file for the game, considering various factors."""
    # Load the saved config for previously selected exes
    config_data = load_config()

    # If the game already exists in Steam or has a saved exe in config, use that
    if game_name in config_data:
        saved_exe_path = config_data[game_name]
        if os.path.exists(saved_exe_path):
            logger.info(f"Using saved .exe for {game_name}: {saved_exe_path}")
            return saved_exe_path
        else:
            logger.warning(
                f"Saved .exe for {game_name} not found, proceeding with new selection."
            )

    if existing_in_steam:
        logger.info(f"Game {game_name} already exists in Steam. Skipping .exe selection.")
        return None

    exe_files = set()  # Using set to avoid duplicates

    # Check for a matching shortcut on the desktop
    desktop_shortcuts = get_desktop_shortcuts()
    if game_name.lower() in desktop_shortcuts:
        shortcut_target = desktop_shortcuts[game_name.lower()]
        if os.path.exists(shortcut_target):
            logger.info(
                f"Found desktop shortcut for {game_name}, prioritizing {shortcut_target}"
            )
            return shortcut_target

    # First, check only the base directory for .exe files
    try:
        base_dir_exes = [
            os.path.join(game_dir, f) for f in os.listdir(game_dir)
            if f.endswith(".exe") and "unins" not in f.lower()
        ]
        exe_files.update(base_dir_exes)
    except Exception as e:
        logger.error(f"Error accessing game directory {game_dir}: {e}")
        return None

    # Search subdirectories for .exe files
    for root, dirs, files in os.walk(game_dir):
        for file in files:
            if file.endswith(".exe") and "unins" not in file.lower():
                exe_files.add(os.path.join(root, file))

    # Filter out .exe files containing 'launcher' for lower priority
    non_launcher_exes = [exe for exe in exe_files if "launcher" not in exe.lower()]
    launcher_exes = [exe for exe in exe_files if "launcher" in exe.lower()]

    # Combine exes with 'launcher' files having lower priority
    all_exes = non_launcher_exes + launcher_exes

    # Prioritize based on size and whether the exe name contains the game name
    sorted_exes = prioritize_exes(game_name, all_exes)

    # If multiple .exe files are found and selective mode is on, prompt the user to choose
    if selective_mode and len(sorted_exes) > 1:
        print(f"Multiple .exe files found for {game_name}. Please choose one:")
        for i, exe_file in enumerate(sorted_exes):
            print(f"{i + 1}: {exe_file}")

        while True:
            try:
                choice = int(input("Enter the number of the .exe file to use: ")) - 1
                if 0 <= choice < len(sorted_exes):
                    chosen_exe = sorted_exes[choice]
                    break
                else:
                    print("Invalid choice, try again.")
            except ValueError:
                print("Please enter a valid number.")

        config_data[game_name] = chosen_exe  # Save the user's choice in the config
        save_config(config_data)  # Save only in selective mode
        return chosen_exe

    # Return the top prioritized exe file found (default mode)
    return sorted_exes[0] if sorted_exes else None


def update_shortcuts(current_games):
    """Update the Steam shortcuts with new games and fetch/update images."""
    shortcuts_file = os.path.join(steam_user_data_path, 'shortcuts.vdf')

    try:
        # Load existing shortcuts or create new if the file doesn't exist
        if os.path.exists(shortcuts_file):
            with open(shortcuts_file, 'rb') as f:
                shortcuts = vdf.binary_load(f)
        else:
            shortcuts = {'shortcuts': {}}

        # Collect the current shortcuts
        existing_games = {
            shortcut.get('appname', '').strip().lower(): shortcut
            for shortcut in shortcuts['shortcuts'].values()
        }
        existing_exes = {
            shortcut.get('exe', '').strip().lower()
            for shortcut in shortcuts['shortcuts'].values()
        }  # Track existing exe paths

        # Add or update games in shortcuts
        for game_name in current_games:
            game_path = None

            # Find which installation path the game is in
            for installation_path in game_installation_paths:
                potential_game_path = os.path.join(installation_path, game_name)
                if os.path.exists(potential_game_path):
                    game_path = potential_game_path
                    break

            if not game_path:
                logger.error(f"Could not find game path for {game_name}")
                continue

            # Check if the game already exists in Steam
            existing_in_steam = game_name.lower() in existing_games

            exe_file = find_largest_exe(game_path, game_name, existing_in_steam)
            if existing_in_steam or exe_file is None:
                logger.info(
                    f"Game {game_name} already exists in Steam or no exe selected. Skipping."
                )
                continue

            exe_path = exe_file.lower()

            # Check if the game is already in Steam either by name or exe path
            if game_name.lower() in existing_games or exe_path in existing_exes:
                logger.info(f"Game {game_name} already exists in Steam. Skipping.")
                continue

            # Capitalize the game name before adding to Steam
            game_name_capitalized = capitalize_game_name(game_name)

            appid = generate_appid(game_name_capitalized, exe_path)

            # Search for the game on SteamGridDB and fetch images
            headers = {
                'Authorization': f'Bearer {steamgriddb_api_key}'
            }
            search_url = f'https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name_capitalized}'
            response = requests.get(search_url, headers=headers)
            logger.info(
                f"Searching SteamGridDB for {game_name_capitalized}, URL: {search_url}, "
                f"Status Code: {response.status_code}"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    game_id = data['data'][0]['id']  # Assume first result is best match
                    save_images(appid, game_id)

            # Add shortcut entry
            new_entry = {
                "appid": appid,
                "appname": game_name_capitalized,
                "exe": f'"{exe_path}"',
                "StartDir": f'"{game_path}"',
                "LaunchOptions": "",
                "IsHidden": 0,
                "AllowDesktopConfig": 1,
                "OpenVR": 0,
                "Devkit": 0,
                "DevkitGameID": "",
                "LastPlayTime": 0,
                "tags": {}
            }
            shortcuts['shortcuts'][str(len(shortcuts['shortcuts']))] = new_entry
            logger.info(f"Added shortcut for game: {game_name_capitalized}")

        # Save the updated shortcuts file
        with open(shortcuts_file, 'wb') as f:
            vdf.binary_dump(shortcuts, f)
            logger.info("Shortcuts file updated and saved.")

    except Exception as e:
        logger.error(f"Error updating shortcuts: {e}")


def main():
    """Main function to check for new or removed games and update Steam shortcuts."""
    try:
        logger.info("Reading current games from installation directories...")
        current_games = read_current_games()
        logger.info(f"Current games: {current_games}")

        logger.info("Updating shortcuts and fetching images...")
        update_shortcuts(current_games)

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")


if __name__ == "__main__":
    main()
    print("Game sync process completed.")
