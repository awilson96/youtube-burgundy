from google.colab import drive
import yt_dlp as youtube_dl
import os
import subprocess

class Youtube2Mp3:
    def __init__(self):
        # Mount Google Drive
        drive.mount('/content/drive')
        self.drive_path = "/content/drive/MyDrive/"  # Path to save files in Google Drive

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
                'outtmpl': os.path.join(self.drive_path, '%(title)s.%(ext)s'),  # Save to Google Drive
            }
        elif choice == "2":
            format_type = "mp4"
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(self.drive_path, '%(title)s.%(ext)s'),  # Save to Google Drive
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

            # Rename the file before splitting and get the new filename
            new_filename = self.rename_most_recent_file(format_type)

            # Check if the downloaded video is larger than 500 MB and split if necessary
            # self.split_video_if_large(new_filename)

        except Exception as e:
            print(f"An error occurred: {e}")

    def rename_most_recent_file(self, format_type):
        """Find the most recent file and rename it with the user's input, then return the new file name"""
        # List all files in the Google Drive folder
        files = [f for f in os.listdir(self.drive_path) if f.endswith(('.mp4', '.mp3'))]

        if files:
            # Get the most recently modified file
            most_recent_file = max(files, key=lambda f: os.path.getmtime(os.path.join(self.drive_path, f)))

            # Prompt user for the new name (without extension)
            print(f"The most recent file is: {most_recent_file}")
            new_name = input("Enter a new name for the file (without extension): ").strip()

            # Construct the new file name with the correct extension
            new_filename = f"{new_name}.{format_type}"
            old_path = os.path.join(self.drive_path, most_recent_file)
            new_path = os.path.join(self.drive_path, new_filename)

            # Rename the most recent file to the new filename
            os.rename(old_path, new_path)
            print(f"File renamed to: {new_filename}")

            return new_filename
        else:
            print("No files found to rename.")
            return None

    def split_video_if_large(self, new_filename):
        """Split the video into parts if the file size is larger than 500 MB"""
        if new_filename:
            file_path = os.path.join(self.drive_path, new_filename)
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            print(f"File: {new_filename}, Size: {file_size_mb:.2f} MB")

            if file_size_mb > 500:
                print(f"Splitting {new_filename} into parts of 500 MB...")

                # Calculate segment duration in seconds
                total_duration = self.get_video_duration(file_path)
                segment_duration = int(total_duration / (file_size_mb / 500))

                base_name = new_filename.rsplit('.', 1)[0]
                output_pattern = os.path.join(self.drive_path, f"{base_name}_%03d.mp4")

                # Use FFmpeg to split the video
                command = [
                    'ffmpeg', '-i', file_path,
                    '-c', 'copy', '-map', '0',
                    '-segment_time', str(segment_duration),
                    '-f', 'segment', output_pattern
                ]
                subprocess.run(command, check=True)

                os.remove(file_path)  # Remove the original large file

                # Print the names of the split files
                split_files = [f for f in os.listdir(self.drive_path) if f.startswith(base_name) and f.endswith(".mp4")]
                split_files.sort()  # Ensure files are in order
                for idx, split_file in enumerate(split_files, 1):
                    print(f"Part {idx}: {split_file}")

            else:
                print(f"File {new_filename} is small enough and doesn't need to be split.")
        else:
            print("No file to split.")

    def get_video_duration(self, file_path):
        """Get the duration of a video file in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error getting video duration: {e}")
            return 0

if __name__ == "__main__":
    yt = Youtube2Mp3()
    yt.youtube_download()
