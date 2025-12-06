from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from youtube2mp3 import YoutubeSegmentDownloader
import os

app = FastAPI()

# Initialize the downloader
downloader = YoutubeSegmentDownloader()
DOWNLOAD_FOLDER = downloader.download_path
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Setup templates folder
templates = Jinja2Templates(directory="html")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": ""})


@app.post("/download", response_class=HTMLResponse)
def download(request: Request, link: str = Form(...), filename: str = Form(...)):
    try:
        print(f"Received download request for URL: {link} with filename: {filename}")

        # Call the actual download function (no splitting yet)
        video_path = downloader.download_video(link, filename)

        if video_path:
            message = f"<p>Download complete: {os.path.basename(video_path)}</p>"
        else:
            message = "<p style='color:red'>Download failed. Check console for errors.</p>"

        return templates.TemplateResponse("index.html", {"request": request, "message": message})

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "message": f"<p style='color:red'>Error: {str(e)}</p>"}
        )
