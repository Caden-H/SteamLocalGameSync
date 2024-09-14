import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import subprocess
import configparser
import sys
import webbrowser  # Imported webbrowser module to open URLs

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


def open_api_key_page():
    """Open the SteamGridDB API key page in the default web browser."""
    api_key_url = 'https://www.steamgriddb.com/profile/preferences/api'
    webbrowser.open(api_key_url)


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
    """Run the Python script and display real-time logs in the text box, handling interactive input."""

    def read_process_output(process):
        """Read the output from the process and display it in the log box."""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Update the log text box
                log_text.insert(tk.END, output)
                log_text.see(tk.END)  # Auto-scroll to the bottom

                # Check if the script is asking for input
                if "Please choose one:" in output or "Enter your choice:" in output:
                    # Prompt the user for input on the main thread
                    root.after(0, get_user_input, process)

        # Process finished
        return process.poll()

    def get_user_input(process):
        """Prompt the user for input and send it to the process."""
        user_input = simpledialog.askstring("Input Required", "Multiple executables found. Please enter your choice:", parent=root)
        if user_input is not None:
            # Send the user input to the process
            process.stdin.write(user_input + '\n')
            process.stdin.flush()
        else:
            # User canceled; terminate the process
            process.terminate()
            log_text.insert(tk.END, "Process terminated by user.\n")
            log_text.see(tk.END)

    # Save the current config before running the script
    save_config()

    # Clear the log box
    log_text.delete(1.0, tk.END)

    # Prepare the command
    cmd = [sys.executable, 'GameSync_Main.py']
    if selective:
        cmd.append('-s')

    # Run the command as a subprocess and capture stdout and stderr
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   stdin=subprocess.PIPE, text=True, bufsize=1)

        # Read output in a separate thread so the GUI remains responsive
        threading.Thread(target=read_process_output, args=(process,), daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"Error executing script: {e}")


def install_requirements():
    """Install required Python packages via pip with spinner feedback."""
    install_status.config(text="🕑", foreground="orange")  # Display spinner during installation

    def install_thread():
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
            if result.returncode == 0:
                install_status.config(text="✔", foreground="green")
                log_text.insert(tk.END, "Requirements installed successfully.\n")
            else:
                install_status.config(text="✖", foreground="red")
                log_text.insert(tk.END, f"Failed to install requirements:\n{result.stderr}\n")
        except Exception as e:
            install_status.config(text="✖", foreground="red")
            log_text.insert(tk.END, f"Error installing requirements: {e}\n")
        finally:
            log_text.see(tk.END)

    # Run the installation in a separate thread to avoid blocking the UI
    threading.Thread(target=install_thread).start()


# Create the main window
root = tk.Tk()
root.title("Non-Steam Game Shortcut Automator")

# Set window icon (Steam logo)
try:
    # Load the icon image (ensure 'steam_icon.ico' or 'steam_icon.png' is in the same directory)
    if os.name == 'nt':
        root.iconbitmap('steam_icon.ico')
    else:
        steam_icon = tk.PhotoImage(file='steam_icon.png')
        root.iconphoto(False, steam_icon)
except Exception as e:
    print(f"Could not load icon: {e}")

# Use ttk for modern widgets
style = ttk.Style(root)
style.theme_use('clam')  # Use a light theme

# Set custom styles
style.configure("TButton", padding=6, relief="flat")
style.configure("TLabel", foreground="#333333", background="#f0f0f0")
style.configure("TFrame", background="#f0f0f0")
style.configure("TEntry", fieldbackground="#ffffff", background="#f0f0f0")
style.configure("TSeparator", background="#f0f0f0")
style.configure("TScrollbar", background="#f0f0f0")
style.configure("InstallFrame.TFrame", background="#e0e0e0")
style.configure("InstallFrame.TLabel", background="#e0e0e0")
style.configure("InstallFrame.TButton", background="#e0e0e0")
style.configure("LogFrame.TFrame", background="#f0f0f0")
style.configure("LogFrame.TLabel", background="#f0f0f0")

entry_widgets = {}

# Set the background color of the root window
root.configure(background="#f0f0f0")

# Add a label for "Configuration (config.ini):"
header_label = ttk.Label(root, text="Configuration (config.ini):", font=("Arial", 12, "bold"), style="TLabel")
header_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky=tk.W)

# Create a frame for the configuration inputs
config_frame = ttk.Frame(root, style="TFrame")
config_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky=tk.EW)
config_frame.columnconfigure(1, weight=1)

# Create input fields for each configuration option inside the config_frame
fields = [
    ("Steam User Data Path", 'steam_user_data_path'),
    ("Game Installation Paths (comma-separated)", 'game_installation_paths'),
    ("Steam Directory Path", 'steamdir_path'),
    ("Desktop Path", 'desktop_path'),
    ("SteamGridDB API Key", 'api_key')
]

for i, (label_text, key) in enumerate(fields):
    ttk.Label(config_frame, text=label_text, style="TLabel").grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
    entry = ttk.Entry(config_frame, width=80, style="TEntry")
    entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
    entry.insert(0, config.get('Paths' if key != 'api_key' else 'SteamGridDB', key))
    entry_widgets[key] = entry
    if key == 'api_key':
        # Add 'Get Key' button next to the API Key entry field
        ttk.Button(config_frame, text="Get Key", width=18, command=open_api_key_page).grid(row=i, column=2, padx=5, pady=5, sticky=tk.W)
    elif key != 'game_installation_paths':
        # Allow browsing for directories (except for game paths)
        ttk.Button(config_frame, text="Browse", width=18, command=lambda k=key: select_directory(label_text, k)).grid(row=i, column=2, padx=5, pady=5, sticky=tk.W)

# Adjust the width of "Add Game Directory" button to ensure full text is visible
add_game_button = ttk.Button(config_frame, text="Add Game Directory", width=18, command=add_game_directory)
add_game_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

# Add a spacer line after config.ini input fields
ttk.Separator(root, orient='horizontal').grid(row=2, column=0, columnspan=4, pady=10, sticky="ew")

# Create a frame for the Install Requirements section
install_frame = ttk.Frame(root, style='InstallFrame.TFrame')
install_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky=tk.EW)

# Add the "Install Requirements" button inside install_frame
ttk.Button(install_frame, text="Install Requirements", command=install_requirements, style="InstallFrame.TButton").grid(row=0, column=0, pady=10, padx=5, sticky=tk.E)
install_status = ttk.Label(install_frame, text="", font=("Arial", 12), style="InstallFrame.TLabel")
install_status.grid(row=0, column=1, padx=5, sticky=tk.W)

# Add a spacer line after the Install Requirements section
ttk.Separator(root, orient='horizontal').grid(row=4, column=0, columnspan=4, pady=10, sticky="ew")

# Add explanation text about automatic vs selective mode
ttk.Label(root, text="Modes:", font=("Arial", 12, "bold"), style="TLabel").grid(row=5, column=0, columnspan=4, padx=10, sticky=tk.W)

ttk.Label(root, text="Automatic Mode: Runs the script with default settings without prompting for .exe selection.\n"
                     "Selective Mode: Allows you to manually choose the executable if multiple are found.",
          wraplength=600, style="TLabel").grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky=tk.W)

# Add buttons for running the script, centered
button_frame = ttk.Frame(root, style="TFrame")
button_frame.grid(row=7, column=0, columnspan=4, pady=10)
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

ttk.Button(button_frame, text="Run in Automatic Mode", command=lambda: run_script(selective=False)).grid(row=0, column=0, padx=10)
ttk.Button(button_frame, text="Run in Selective Mode", command=lambda: run_script(selective=True)).grid(row=0, column=1, padx=10)

# Add a scrollable text box to display logs
log_frame = ttk.Frame(root, style="LogFrame.TFrame")
log_frame.grid(row=8, column=0, columnspan=4, padx=10, pady=5, sticky=tk.EW)
log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, state="normal", font=("Arial", 10), background="#ffffff")
log_text.grid(row=0, column=0, sticky=tk.EW)
log_frame.columnconfigure(0, weight=1)

# Start the GUI loop
root.mainloop()
