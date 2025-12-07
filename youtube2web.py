from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from youtube2mp3 import YoutubeSegmentDownloader
import os

app = FastAPI()

# Initialize downloader
downloader = YoutubeSegmentDownloader()

# Set download path to D:\Music\
DOWNLOAD_FOLDER = r"D:\Music"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
