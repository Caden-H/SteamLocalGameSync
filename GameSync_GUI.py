import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import configparser
from ttkthemes import ThemedTk

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
            messagebox.showinfo("Success", "Script executed.")
        else:
            # Show the error output from the script if the return code is not 0
            messagebox.showerror("Error", f"Script encountered an error:\n{result.stderr}")

    except Exception as e:
        # Handle any other exceptions that might occur
        messagebox.showerror("Error", f"Error executing script: {e}")


def install_requirements():
    """Install required Python packages via pip with spinner feedback."""
    install_status.config(text="🕑", foreground="yellow")  # Display spinner during installation

    def install_thread():
        try:
            result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
            if result.returncode == 0:
                install_status.config(text="✔", foreground="green")
            else:
                install_status.config(text="✖", foreground="red")
        except Exception as e:
            install_status.config(text="✖", foreground="red")
            messagebox.showerror("Error", f"Error installing requirements: {e}")

    # Run the installation in a separate thread to avoid blocking the UI
    threading.Thread(target=install_thread).start()


# Create the main window with a dark theme
root = ThemedTk(theme="equilux")  # ThemedTk from ttkthemes for material/dark mode
root.title("Steam Non-Steam Game Shortcut Automator")
root.configure(bg="#2e2e2e")

# Create modern-style widgets using ttk with a dark mode theme
style = ttk.Style(root)
style.theme_use("equilux")  # Using dark mode theme

# Set custom button style for rounded corners
style.configure("TButton", padding=6, relief="flat", borderwidth=0)

entry_widgets = {}

# Add a label for "config.ini:"
ttk.Label(root, text="Configuration (config.ini):", foreground="#dcdcdc", background="#2e2e2e", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky=tk.W)

# Create a frame for the configuration inputs
config_frame = ttk.Frame(root)
config_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)

# Make the columns in config_frame expand equally
config_frame.columnconfigure(1, weight=1)

# Create input fields for each configuration option inside the config_frame
fields = [
    ("Steam User Data Path", 'steam_user_data_path'),
    ("Game Installation Paths (comma-separated)", 'game_installation_paths'),
    ("Steam Directory Path", 'steamdir_path'),
    ("Desktop Path", 'desktop_path'),
    ("SteamGridDB API Key", 'api_key')
]

for i, (label, key) in enumerate(fields):
    ttk.Label(config_frame, text=label, foreground="#dcdcdc", background="#464646").grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
    entry = ttk.Entry(config_frame, width=50)
    entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
    entry.insert(0, config.get('Paths' if key != 'api_key' else 'SteamGridDB', key))
    entry_widgets[key] = entry
    if key != 'game_installation_paths' and key != 'api_key':  # Allow browsing for directories (except for game paths)
        ttk.Button(config_frame, text="Browse", width=19, command=lambda k=key: select_directory(label, k)).grid(row=i, column=2, padx=5, pady=5, sticky=tk.W)

# Add "Add Game Directory" button next to the game installation path entry
ttk.Button(config_frame, text="Add Game Directory", width=19, command=add_game_directory).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

# Add a spacer line after config.ini input fields
ttk.Separator(root, orient='horizontal').grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

# Create a frame for the Install Requirements section
install_frame = ttk.Frame(root)
install_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)

# Set background color for install_frame to distinguish it
install_frame.configure(style='InstallFrame.TFrame')
style.configure('InstallFrame.TFrame', background="#3a3a3a")

# Add the "Install Requirements" button inside install_frame
ttk.Button(install_frame, text="Install Requirements", command=install_requirements).grid(row=0, column=0, pady=10, padx=5, sticky=tk.E)
install_status = ttk.Label(install_frame, text="", font=("Arial", 12), background="#3a3a3a", foreground="white")
install_status.grid(row=0, column=1, padx=5, sticky=tk.W)

# Add a spacer line after the Install Requirements section
ttk.Separator(root, orient='horizontal').grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")

# Add explanation text about automatic vs selective mode
ttk.Label(root, text="Modes:", foreground="#dcdcdc", background="#2e2e2e", font=("Arial", 12, "bold")).grid(row=5, column=0, columnspan=3, padx=10, sticky=tk.W)

ttk.Label(root, text="Automatic Mode: Runs the script with default settings without prompting for .exe selection.\n"
                     "Selective Mode: Allows you to manually choose the executable if multiple are found.",
          foreground="#dcdcdc", background="#2e2e2e", wraplength=600).grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

# Add buttons for running the script, centered
button_frame = ttk.Frame(root)
button_frame.grid(row=7, column=0, columnspan=3, pady=10)

ttk.Button(button_frame, text="Run in Automatic Mode", command=lambda: run_script(selective=False)).grid(row=0, column=0, padx=10)
ttk.Button(button_frame, text="Run in Selective Mode", command=lambda: run_script(selective=True)).grid(row=0, column=1, padx=10)

# Center the buttons
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

# Start the GUI loop
root.mainloop()
