import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
    """Run the Python script and check for errors."""
    
    # Save the current config before running the script
    save_config()

    # Check if required directories exist before running the script
    steam_user_data_path = entry_widgets['steam_user_data_path'].get()
    game_installation_paths = entry_widgets['game_installation_paths'].get().split(',')

    # Check for missing directories
    missing_dirs = []
    if not os.path.exists(steam_user_data_path):
        missing_dirs.append(steam_user_data_path)
    for path in game_installation_paths:
        if not os.path.exists(path.strip()):
            missing_dirs.append(path.strip())

    if missing_dirs:
        messagebox.showerror("Error", f"Missing directories: {', '.join(missing_dirs)}")
        return  # Stop execution if directories are missing

    # Prepare the command
    cmd = ['python', 'GameSync_Main.py']
    if selective:
        cmd.append('-s')

    try:
        # Run the script and capture the result
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            messagebox.showinfo("Success", "Script executed successfully!")
        else:
            # Show the error output from the script if the return code is not 0
            messagebox.showerror("Error", f"Script encountered an error:\n{result.stderr}")

    except Exception as e:
        # Handle any other exceptions that might occur
        messagebox.showerror("Error", f"Error executing script: {e}")



def install_requirements():
    """Install required Python packages via pip."""
    try:
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
        if result.returncode == 0:
            status_label.config(text="✔ Requirements Installed", foreground="green")
        else:
            status_label.config(text="✖ Failed to Install Requirements", foreground="red")
    except Exception as e:
        status_label.config(text="✖ Error Installing Requirements", foreground="red")
        messagebox.showerror("Error", f"Error installing requirements: {e}")


# Create the main window
root = tk.Tk()
root.title("Steam Non-Steam Game Shortcut Automator")

# Use ttk for modern widgets
style = ttk.Style(root)
style.theme_use("clam")

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
    ttk.Label(root, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
    entry = ttk.Entry(root, width=50)
    entry.grid(row=i, column=1, padx=10, pady=5)
    entry.insert(0, config.get('Paths' if key != 'api_key' else 'SteamGridDB', key))
    entry_widgets[key] = entry
    if key != 'game_installation_paths' and key != 'api_key':  # Allow browsing for directories (except for game paths)
        ttk.Button(root, text="Browse", command=lambda k=key: select_directory(label, k)).grid(row=i, column=2, padx=10, pady=5)

# Add "Add Game Directory" button next to the game installation path entry
ttk.Button(root, text="Add Game Directory", command=add_game_directory).grid(row=1, column=2, padx=10, pady=5)

# Add buttons for running the script, side by side
ttk.Button(root, text="Run in Automatic Mode", command=lambda: run_script(selective=False)).grid(row=len(fields) + 1, column=0, pady=10, padx=10, sticky=tk.E)
ttk.Button(root, text="Run in Selective Mode", command=lambda: run_script(selective=True)).grid(row=len(fields) + 1, column=1, pady=10, padx=10, sticky=tk.W)

# Add a button to install requirements
ttk.Button(root, text="Install Requirements", command=install_requirements).grid(row=len(fields) + 2, column=0, columnspan=2, pady=10)

# Status label to show if requirements are installed successfully or failed
status_label = ttk.Label(root, text="")
status_label.grid(row=len(fields) + 3, column=0, columnspan=2)

# Start the GUI loop
root.mainloop()
