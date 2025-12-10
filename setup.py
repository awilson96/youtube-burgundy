import os
import json
import tkinter as tk
from tkinter import filedialog
import re

CONFIG_FILE = "config.json"
NGINX_CONF = "nginx.conf"

def choose_folder():
    print("Select your download directory...")
    folder = filedialog.askdirectory()
    if not folder:
        raise Exception("No folder selected.")
    return folder

def normalize_for_nginx(path):
    """Convert OS path to nginx-friendly format:
    - Always use forward slashes
    - Ensure trailing slash
    """
    path = os.path.abspath(path)
    path = path.replace("\\", "/")
    if not path.endswith("/"):
        path += "/"
    return path

def write_config(download_path):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

    config["download_path"] = download_path

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print(f"Updated {CONFIG_FILE}: download_path = {download_path}")

def update_nginx_conf(alias_path):
    if not os.path.exists(NGINX_CONF):
        raise Exception(f"{NGINX_CONF} not found.")

    with open(NGINX_CONF, "r") as f:
        nginx = f.read()

    new_alias_line = f"alias {alias_path};"

    nginx_updated = re.sub(
        r"location\s+/video/\s*\{[^}]*?alias\s+.*?;",
        lambda m: re.sub(r"alias\s+.*?;", new_alias_line, m.group(0)),
        nginx,
        flags=re.DOTALL
    )

    with open(NGINX_CONF, "w") as f:
        f.write(nginx_updated)

    print(f"Updated {NGINX_CONF}: alias set to {alias_path}")

def main():
    folder = choose_folder()
    nginx_path = normalize_for_nginx(folder)

    write_config(folder)
    update_nginx_conf(nginx_path)

    print("\nSetup complete!")

if __name__ == "__main__":
    main()
