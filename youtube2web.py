from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
import os

app = FastAPI()

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <h2>YouTube Downloader</h2>
    <form action="/download" method="post">
        YouTube URL: <input type="text" name="link" size="50">
        <input type="submit" value="Download">
    </form>
    """

@app.post("/download")
async def download(link: str = Form(...)):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        return HTMLResponse(f"""
            <p>Downloaded: {os.path.basename(filename)}</p>
            <a href="/file/{os.path.basename(filename)}">Download File</a>
            <br><a href="/">Download another</a>
        """)
    except Exception as e:
        return HTMLResponse(f"<p>Error: {str(e)}</p><a href='/'>Back</a>")

@app.get("/file/{filename}")
def serve_file(filename: str):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="application/octet-stream", filename=filename)
    return HTMLResponse(f"<p>File not found</p><a href='/'>Back</a>")
