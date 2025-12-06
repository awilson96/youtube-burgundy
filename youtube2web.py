from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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
    # List videos in the downloads folder
    files = [
        f for f in os.listdir(DOWNLOAD_FOLDER)
        if f.endswith(".mp4") and (query.lower() in f.lower())
    ]
    return templates.TemplateResponse("index.html", {"request": request, "files": files, "query": query, "message": ""})


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


from urllib.parse import unquote

@app.get("/video/{filename}")
def serve_video(filename: str):
    # Decode URL-encoded filename
    decoded_filename = unquote(filename)
    path = os.path.join(DOWNLOAD_FOLDER, decoded_filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=decoded_filename)
    return HTMLResponse(f"<p>File not found</p>")

