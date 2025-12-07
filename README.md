# youtube2mp3
Convert youtube videos to mp3 to extract audio for creating offline playlists

## Running the Web Server

Development mode: `uvicorn youtube2web:app --host 0.0.0.0 --port 8000 --reload`
Deployment mode: `uvicorn youtube2web:app --host 0.0.0.0 --port 8000`

Note that you will need to close the terminal completely to stop the process as control+C does not work to stop the process.

## Running nginx
navigate to `D:\nginx-1.28.0\` and run `start nginx` to start the server

to stop the server run `nginx -s stop`

to edit the config the config is located at `C:\Users\awils\nginx-1.28.0\conf\nginx.conf`

