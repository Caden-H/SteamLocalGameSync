import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import simpledialog
import subprocess
import configparser

# Create a new configuration file if not present
config_file = 'config.ini'

config = configparser.ConfigParser()

if not os.path.exists(config_file):
    config['Paths'] = {
        'steam_user_data_path': '',
        'game_installation_paths': '',
        'steamdir_path': '',
        'desktop_path': ''
    }
    config['SteamGridDB'] = {
        'api_key': ''
    }
    with open(config_file, 'w') as f:
        config.write(f)

config.read(config_file)


def select_directory(title, key):
    """Helper function to browse and select a directory."""
    directory = filedialog.askdirectory(title=title)
    if directory:
        entry_widgets[key].delete(0, tk.END)
        entry_widgets[key].insert(0, directory)


def save_config():
    """Save all input fields into the config file."""
    config['Paths']['steam_user_data_path'] = entry_widgets['steam_user_data_path'].get()
    config['Paths']['game_installation_paths'] = entry_widgets['game_installation_paths'].get()
    config['Paths']['steamdir_path'] = entry_widgets['steamdir_path'].get()
    config['Paths']['desktop_path'] = entry_widgets['desktop_path'].get()
    config['SteamGridDB']['api_key'] = entry_widgets['api_key'].get()

    with open(config_file, 'w') as f:
        config.write(f)

    messagebox.showinfo("Info", "Configuration saved!")


def add_game_directory():
    """Add a game installation directory."""
    directory = filedialog.askdirectory(title="Select Game Installation Directory")
    if directory:
        current_paths = entry_widgets['game_installation_paths'].get()
        if current_paths:
            entry_widgets['game_installation_paths'].insert(tk.END, f",{directory}")
        else:
            entry_widgets['game_installation_paths'].insert(tk.END, directory)


def run_script(selective=False):
    """Run the Python script."""
    save_config()  # Save the current config before running
    cmd = ['python', 'steam_auto_shortcuts.py']
    if selective:
        cmd.append('-s')
    
    try:
        subprocess.run(cmd)
        messagebox.showinfo("Success", "Script executed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error executing script: {e}")


# Create the main window
root = tk.Tk()
root.title("Steam Non-Steam Game Shortcut Automator")

entry_widgets = {}

# Create input fields for each configuration option
fields = [
    ("Steam User Data Path", 'steam_user_data_path'),
    ("Game Installation Paths (comma-separated)", 'game_installation_paths'),
    ("Steam Directory Path", 'steamdir_path'),
    ("Desktop Path", 'desktop_path'),
    ("SteamGridDB API Key", 'api_key')
]

for i, (label, key) in enumerate(fields):
    tk.Label(root, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
    entry = tk.Entry(root, width=50)
    entry.grid(row=i, column=1, padx=10, pady=5)
    entry.insert(0, config.get('Paths' if key != 'api_key' else 'SteamGridDB', key))
    entry_widgets[key] = entry
    if key != 'api_key':  # Only allow browsing for directories, not the API key
        tk.Button(root, text="Browse", command=lambda k=key: select_directory(label, k)).grid(row=i, column=2, padx=10, pady=5)

# Add "Add Game Directory" button
tk.Button(root, text="Add Game Directory", command=add_game_directory).grid(row=len(fields), column=0, columnspan=3, pady=10)

# Add buttons for running the script
tk.Button(root, text="Run Script", command=lambda: run_script(selective=False)).grid(row=len(fields) + 1, column=0, pady=10, sticky=tk.W, padx=10)
tk.Button(root, text="Run in Selective Mode", command=lambda: run_script(selective=True)).grid(row=len(fields) + 1, column=1, pady=10, sticky=tk.W)

# Start the GUI loop
root.mainloop()
