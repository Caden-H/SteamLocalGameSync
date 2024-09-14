# Steam Non-Steam Game Shortcut Automator

This Python script automatically adds games from multiple directories to your Steam library as non-Steam games, ensuring the correct executable is chosen and adding images from SteamGridDB.

## Features
- **Automatic Game Detection**: Scans multiple directories for games.
- **Executable Prioritization**: Chooses the right executable based on name match, size, and desktop shortcuts.
- **Image Fetching**: Fetches images from SteamGridDB for grid view, hero images, and logos.
- **Configurable**: Paths and API key are configurable in `config.ini`.
- **Selective Mode**: Lets you manually choose the executable if needed.

## How the Executable is Chosen
1. **Desktop Shortcut Priority**: If a `.lnk` file exists on your desktop for the game, that executable is prioritized.
2. **Name and Size Matching**: Executables are prioritized by size, and those containing the game name are given higher priority.
3. **Selective Mode**: If multiple valid executables are found, run in selective mode (`-s`) to choose manually.

## Setup
### Prerequisites
- **Python 3** and **pip** installed.
- **SteamGridDB API Key**: Get it from [SteamGridDB](https://www.steamgriddb.com/profile/preferences/api).

### Installation
1. **Clone or Download the Script**.
2. **Install Dependencies**:
   `pip install -r requirements.txt`
3. **Configure `config.ini`**:
   - Update the paths to your Steam and game directories.
   - Add your SteamGridDB API key.

### Running the Script
You can double click either `.bat` file or run the script if everything is set up correctly.
- **Default Mode**: Automatically detects games and executables.
   `python steam_auto_shortcuts.py`
- **Selective Mode**: Prompts you to choose executables if multiple are found.
   `python steam_auto_shortcuts.py -s`

## Configuration (`config.ini`)
- **Paths**: 
  - `steam_user_data_path`: Path to your Steam `userdata` directory.
  - `game_installation_paths`: Comma-separated list of game installation directories.
  - `desktop_path`: Path to your Desktop.
- **SteamGridDB API**: 
  - `api_key`: Your SteamGridDB API key.

### Automating with Task Scheduler
1. **Create a `.bat` file** to run the script:
   `@echo off`
   `python "C:\path\to\your\steam_auto_shortcuts.py"`
2. **Use Windows Task Scheduler** to run this daily.

### Cache File (`cache.txt`)
- Saves the user’s executable choice for future runs.
- Format: `game_name=exe_path`.

## Troubleshooting
- **Python Not Found**: Ensure Python is installed and added to your PATH.
- **Missing API Key**: Get your SteamGridDB API key and add it to `config.ini`.

## License
This project is licensed under the MIT License.
