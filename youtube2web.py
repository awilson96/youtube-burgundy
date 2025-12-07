from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
    all_files = os.listdir(DOWNLOAD_FOLDER)  # ← NO filtering
    
    # Optional: apply search filter
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
