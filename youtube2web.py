from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from youtube2mp3 import YoutubeSegmentDownloader
import os
import json
import random

app = FastAPI()

# Initialize downloader
downloader = YoutubeSegmentDownloader()

# Set paths
DOWNLOAD_FOLDER = downloader.get_download_path()
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


@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    """Render the main menu page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/download", response_class=HTMLResponse)
def download_page(request: Request, message: str = ""):
    """Render download page with optional message."""
    playlists = [f[:-5] for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]
    return templates.TemplateResponse("download.html", {
        "request": request,
        "message": message,
        "playlists": playlists
    })


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


@app.post("/api/download")
async def download_video_api(link: str = Form(...), filename: str = Form(...)):
    try:
        downloaded_file = downloader.download_video(link, filename)
        if downloaded_file:
            return JSONResponse({"success": True, "filename": os.path.basename(downloaded_file)})
        else:
            return JSONResponse({"success": False, "message": "Download failed."})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})


@app.post("/api/delete_file")
async def delete_file(request: Request):
    data = await request.json()
    filename = data.get("filename")
    if not filename:
        return JSONResponse({"success": False, "message": "No filename provided"})

    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return JSONResponse({"success": False, "message": "File does not exist"})

    try:
        os.remove(file_path)
        return JSONResponse({"success": True, "message": f"{filename} deleted"})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})


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


@app.get("/playlists", response_class=HTMLResponse)
def playlist_viewer(request: Request):
    """Render playlist viewer page with list of playlists."""
    playlists = [f[:-5] for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]
    return templates.TemplateResponse("playlist_viewer.html", {
        "request": request,
        "playlists": playlists
    })


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


@app.post("/playlist/delete")
async def delete_playlist(request: Request):
    """
    Deletes a playlist JSON file.
    Expects JSON: { "name": "playlist_name" }
    """
    data = await request.json()
    playlist_name = data.get("name")

    if not playlist_name:
        return JSONResponse({"success": False, "message": "No playlist name provided"}, status_code=400)

    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")
    if not os.path.exists(playlist_path):
        return JSONResponse({"success": False, "message": f"Playlist '{playlist_name}' does not exist"}, status_code=404)

    try:
        os.remove(playlist_path)
        return JSONResponse({"success": True, "message": f"Playlist '{playlist_name}' deleted"})
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error deleting playlist: {e}"}, status_code=500)

   
@app.get("/playlist/details", response_class=HTMLResponse)
def playlist_details(request: Request, name: str):
    """Render playlist details page for a single playlist"""
    return templates.TemplateResponse("playlist_details.html", {
        "request": request,
        "playlist_name": name
    })


@app.post("/playlist/play_all")
async def play_all(request: Request):
    data = await request.json()
    playlist_name = data.get("playlist")
    if not playlist_name:
        return JSONResponse({"success": False, "message": "Playlist name required"}, status_code=400)
    
    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")
    if not os.path.exists(playlist_path):
        return JSONResponse({"success": False, "message": "Playlist not found"}, status_code=404)
    
    with open(playlist_path, "r", encoding="utf-8") as f:
        songs = json.load(f).get("songs", [])
    

    for song in songs:
        print("Play:", song)
    
    return {"success": True}


@app.post("/playlist/shuffle")
async def shuffle_playlist(request: Request):
    data = await request.json()
    playlist_name = data.get("playlist")
    if not playlist_name:
        return JSONResponse({"success": False, "message": "Playlist name required"}, status_code=400)
    
    playlist_path = os.path.join(PLAYLIST_FOLDER, f"{playlist_name}.json")
    if not os.path.exists(playlist_path):
        return JSONResponse({"success": False, "message": "Playlist not found"}, status_code=404)
    
    with open(playlist_path, "r", encoding="utf-8") as f:
        songs = json.load(f).get("songs", [])
    
    random.shuffle(songs)
    

    for song in songs:
        print("Play (shuffled):", song)
    
    return {"success": True}