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
    # Get all playlist names
    playlists = [f.replace(".json", "") for f in os.listdir("playlists") if f.endswith(".json")]
    
    return templates.TemplateResponse("video_detail.html", {
        "request": request,
        "filename": filename,
        "playlists": playlists
    })

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
