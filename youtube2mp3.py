from __future__ import unicode_literals
import yt_dlp as youtube_dl
import os
import shutil

class Youtube2Mp3:

    def __init__(self):
        pass

    def youtube_download(self):
        """Download a file as mp3 or mp4 by providing the Youtube link"""
        print("Select format: \n1 for MP3 \n2 for MP4")
        choice = input("").strip()

        if choice == "1":
            format_type = "mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'outtmpl': '%(title)s.%(ext)s',  # Ensures proper file naming
            }
        elif choice == "2":
            format_type = "mp4"
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'outtmpl': '%(title)s.%(ext)s',  # Ensures proper file naming
            }
        else:
            print("Invalid input. Aborting.")
            return

        print("Insert the link")
        link = input("").strip()

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            
            print(f"Download as {format_type} complete.")

            # Clean up non-MP4 files
            self.cleanup_files()

            # Check the size of the downloaded MP4 file
            filename = self.get_latest_downloaded_file()

            # If the file is larger than 500MB, split it
            if os.path.getsize(filename) > 500 * 1024 * 1024:  # 500MB in bytes
                self.split_video(filename)

        except Exception as e:
            print(f"An error occurred: {e}")

    def get_latest_downloaded_file(self):
        """Get the most recently downloaded file in the current directory"""
        files = os.listdir()
        files = [f for f in files if f.endswith('.mp4') or f.endswith('.m4a')]
        latest_file = max(files, key=os.path.getctime)
        return latest_file

    def cleanup_files(self):
        """Remove non-MP4 files and intermediate files"""
        for filename in os.listdir():
            if filename.endswith(".m4a") or filename.endswith(".f401") or filename.endswith(".f140"):
                try:
                    os.remove(filename)
                    print(f"Removed file: {filename}")
                except Exception as e:
                    print(f"Error removing file {filename}: {e}")

    def split_video(self, filename):
        """Split the video into smaller parts if it exceeds 500MB"""
        import subprocess

        # Get the base name (without extension)
        base_filename = os.path.splitext(filename)[0]

        # Split the video into 500MB segments using ffmpeg
        output_pattern = f"{base_filename}_part_%03d.mp4"
        command = [
            "ffmpeg", "-i", filename, "-c", "copy", "-map", "0",
            "-f", "segment", "-segment_size", str(500 * 1024 * 1024),  # 500MB
            output_pattern
        ]
        
        try:
            subprocess.run(command, check=True)
            print(f"Video split into smaller parts: {base_filename}_part_001.mp4, etc.")
            # Remove the original large file after splitting
            os.remove(filename)
            print(f"Original file {filename} removed.")
        except subprocess.CalledProcessError as e:
            print(f"Error splitting video: {e}")

    def calculate_total_music_duration(self, directory):
        """Calculate total duration of all mp3 files in a directory and print in hours, minutes, and seconds"""
        total_duration = 0  # total duration in seconds

        # Iterate over all files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".mp3"):
                file_path = os.path.join(directory, filename)
                
                # Use mutagen to get the duration of the mp3 file
                audio = MP3(file_path)
                total_duration += audio.info.length

        # Convert total seconds to hours, minutes, and seconds
        hours, remainder = divmod(total_duration, 3600)
        minutes, seconds = divmod(remainder, 60)

        print(f"Total music duration in {directory}: \t\t{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")
        return total_duration


if __name__ == "__main__":
    yt = Youtube2Mp3()
    yt.youtube_download()