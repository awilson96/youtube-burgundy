from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import unquote
from youtube2mp3 import YoutubeSegmentDownloader
import os

app = FastAPI()

# Initialize the downloader
downloader = YoutubeSegmentDownloader()
DOWNLOAD_FOLDER = downloader.download_path
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Templates folder
templates = Jinja2Templates(directory="html")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, query: str = ""):
    # List all video files without extensions
    all_files = [
        os.path.splitext(f)[0] for f in os.listdir(DOWNLOAD_FOLDER)
        if f.lower().endswith(".mp4")
    ]
    # Filter files by search query
    if query:
        all_files = [f for f in all_files if query.lower() in f.lower()]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": all_files,
        "query": query,
        "message": ""
    })


@app.post("/download", response_class=HTMLResponse)
def download(request: Request, link: str = Form(...), filename: str = Form(...)):
    try:
        print(f"Downloading video: {link} as {filename}")
        downloaded_file = downloader.download_video(link, filename)

        if downloaded_file:
            message = f"<p>Downloaded and ready to play: {os.path.basename(downloaded_file)}</p>"
        else:
            message = "<p style='color:red'>Download failed.</p>"

        # List videos
        files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith(".mp4")]
        return templates.TemplateResponse("index.html", {"request": request, "files": files, "query": "", "message": message})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "files": [], "query": "", "message": f"<p style='color:red'>Error: {e}</p>"})

@app.get("/video/{filename}")
def serve_video(filename: str):
    decoded_filename = unquote(filename)
    # Append .mp4 extension to serve the actual file
    path = os.path.join(DOWNLOAD_FOLDER, f"{decoded_filename}.mp4")
    if os.path.exists(path):
        # Streaming file
        return FileResponse(path, media_type="video/mp4", filename=f"{decoded_filename}.mp4")
    return HTMLResponse(f"<p>File not found</p>")

