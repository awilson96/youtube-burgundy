from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from youtube2mp3 import YoutubeSegmentDownloader
import os
import json

app = FastAPI()

# Initialize downloader
downloader = YoutubeSegmentDownloader()

# Set paths
DOWNLOAD_FOLDER = r"D:\Music"
PLAYLIST_FOLDER = "playlists"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(PLAYLIST_FOLDER, exist_ok=True)

# Make sure the downloader also uses this folder
downloader.download_path = DOWNLOAD_FOLDER

# Templates folder
templates = Jinja2Templates(directory="html")

def get_playlists_containing(filename: str):
    matches = []

    for f in os.listdir(PLAYLIST_FOLDER):
        if not f.endswith(".json"):
            continue

        path = os.path.join(PLAYLIST_FOLDER, f)
        try:
            with open(path, "r") as fd:
                data = json.load(fd)

            songs = data.get("songs", [])
            name = data.get("name", f[:-5])

            if filename in songs:
                matches.append(name)

        except Exception as e:
            print("Playlist read error:", e)

    return matches

# -----------------------------
# Index / Menu page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    """Render the main menu page."""
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------
# Download page (GET)
# -----------------------------
@app.get("/download", response_class=HTMLResponse)
def download_page(request: Request, message: str = ""):
    """Render download page with optional message."""
    return templates.TemplateResponse("download.html", {
        "request": request,
        "message": message
    })


# -----------------------------
# Download action (POST)
# -----------------------------
@app.post("/download", response_class=HTMLResponse)
def download_video(request: Request, link: str = Form(...), filename: str = Form(...)):
    try:
        downloaded_file = downloader.download_video(link, filename)
        if downloaded_file:
            message = f"Downloaded and ready to play: {os.path.basename(downloaded_file)}"
        else:
            message = "Download failed."

        # After download, show the download page again
        return templates.TemplateResponse("download.html", {
            "request": request,
            "message": message
        })

    except Exception as e:
        return templates.TemplateResponse("download.html", {
            "request": request,
            "message": f"Error: {e}"
        })


# -----------------------------
# Files/Search page
# -----------------------------
@app.get("/files", response_class=HTMLResponse)
def files_page(request: Request, query: str = ""):
    """Render files page with search + playback functionality."""
    all_files = os.listdir(DOWNLOAD_FOLDER)

    # Optional search filter
    if query:
        all_files = [f for f in all_files if query.lower() in f.lower()]

    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": all_files,
        "query": query
    })

@app.get("/video/{filename}", response_class=HTMLResponse)
def video_page(request: Request, filename: str):

    # All playlist names
    playlists = [f[:-5] for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]

    # Playlists this file belongs to
    file_playlists = get_playlists_containing(filename)

    return templates.TemplateResponse("video_detail.html", {
        "request": request,
        "filename": filename,
        "playlists": playlists,          # For dropdown
        "file_playlists": file_playlists # For Belongs-to list
    })

# -----------------------------
# Playlist Viewer Page
# -----------------------------
@app.get("/playlists", response_class=HTMLResponse)
def playlist_viewer(request: Request):
    """Render playlist viewer page with list of playlists."""
    playlists = [f[:-5] for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]
    return templates.TemplateResponse("playlist_viewer.html", {
        "request": request,
        "playlists": playlists
    })

# -----------------------------
# Return files in a playlist (filtered by actual files)
# -----------------------------
@app.get("/playlist/files")
def get_playlist_files(name: str):
    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{name}.json")
    if not os.path.exists(playlist_path):
        return JSONResponse({"songs": []})

    # Load playlist JSON
    with open(playlist_path, "r", encoding="utf-8") as f:
        playlist_data = json.load(f)

    # Get all files in download folder
    all_files = os.listdir(DOWNLOAD_FOLDER)

    # Filter: only include files that exist in download folder
    filtered_files = [f for f in all_files if f in playlist_data.get("songs", [])]

    return JSONResponse({"songs": filtered_files})

# -----------------------------
# Add file to playlist
# -----------------------------
@app.post("/playlist/add")
async def add_to_playlist(request: Request):
    data = await request.json()
    playlist_name = data.get("playlist")
    file_name = data.get("file")

    if not playlist_name or not file_name:
        return JSONResponse({"success": False, "message": "Missing playlist or file"}, status_code=400)

    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")

    # Load or create playlist
    if os.path.exists(playlist_path):
        with open(playlist_path, "r", encoding="utf-8") as f:
            playlist_data = json.load(f)
    else:
        playlist_data = {"name": playlist_name, "songs": []}

    # Check if file is already in playlist
    if file_name in playlist_data["songs"]:
        return JSONResponse({"success": False, "message": "File already in playlist"})

    # Add file and save
    playlist_data["songs"].append(file_name)
    with open(playlist_path, "w", encoding="utf-8") as f:
        json.dump(playlist_data, f, indent=4)

    return JSONResponse({"success": True, "message": f"Added {file_name} to {playlist_name}"})

@app.post("/playlist/remove")
async def remove_from_playlist(request: Request):
    data = await request.json()
    playlist_name = data.get("playlist")
    file_name = data.get("file")

    if not playlist_name or not file_name:
        return JSONResponse({"success": False, "message": "Missing playlist or file"}, status_code=400)

    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")

    if not os.path.exists(playlist_path):
        return JSONResponse({"success": False, "message": "Playlist not found"}, status_code=404)

    with open(playlist_path, "r", encoding="utf-8") as f:
        playlist_data = json.load(f)

    if file_name not in playlist_data.get("songs", []):
        return JSONResponse({"success": False, "message": "File not in playlist"}, status_code=404)

    playlist_data["songs"].remove(file_name)

    with open(playlist_path, "w", encoding="utf-8") as f:
        json.dump(playlist_data, f, indent=4)

    return JSONResponse({"success": True, "message": f"Removed {file_name} from {playlist_name}"})

@app.post("/playlist/create")
async def create_playlist(request: Request):
    data = await request.json()
    playlist_name = data.get("name")

    if not playlist_name:
        return JSONResponse({"success": False, "message": "Playlist name required"}, status_code=400)

    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")
    if os.path.exists(playlist_path):
        return JSONResponse({"success": False, "message": "Playlist already exists"}, status_code=400)

    # Create empty playlist
    playlist_data = {"name": playlist_name, "songs": []}
    with open(playlist_path, "w", encoding="utf-8") as f:
        json.dump(playlist_data, f, indent=4)

    return JSONResponse({"success": True, "message": f"Playlist {playlist_name} created"})
