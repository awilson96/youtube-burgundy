import yt_dlp
import os
import subprocess

class YoutubeSegmentDownloader:
    SEGMENT_DURATION = 30 * 60  # 30 minutes in seconds

    def __init__(self):
        """Initialize the downloader."""
        self.download_path = "./downloads"  # Folder to save downloaded videos

    def get_video_duration(self, video_url):
        """Retrieve the video duration in seconds."""
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            result = ydl.extract_info(video_url, download=False)
            return result['duration']  # Returns duration in seconds

    def download_video(self, video_url, segment_filename):
        """Download the whole video."""
        # Get video info to determine video title
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            video_info = ydl.extract_info(video_url, download=False)
            video_title = video_info['title']
        
        video_filename = f"{segment_filename}.mp4"
        video_filepath = os.path.join(self.download_path, video_filename)

        # Ensure download path exists
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        # yt-dlp options for downloading the video
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': video_filepath,
            'quiet': False,
            'noplaylist': True  # Avoid downloading playlists
        }

        # Download the full video
        try:
            print(f"Downloading the entire video: {video_title}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"Video downloaded successfully: {video_filename}")
            return video_filepath
        except Exception as e:
            print(f"Failed to download the video: {e}")
            return None

    def split_video_into_segments(self, video_filepath, segment_filename, duration):
        """Split the video into 30-minute segments using ffmpeg."""
        num_segments = (duration // self.SEGMENT_DURATION) + (1 if duration % self.SEGMENT_DURATION > 0 else 0)
        print(f"Video Duration: {duration} seconds")
        print(f"Total Segments: {num_segments}")
        print(f"Segments will be saved in {self.download_path} with the base name '{segment_filename}'.")

        # Split the video into segments
        for i in range(num_segments):
            start_time = i * self.SEGMENT_DURATION
            end_time = min((i + 1) * self.SEGMENT_DURATION, duration)
            segment_name = f"{segment_filename}_{i+1}.mp4"
            segment_filepath = os.path.join(self.download_path, segment_name)

            print(f"Splitting Segment {i+1}: {start_time}s to {end_time}s")

            # Use ffmpeg to split the video into segments
            command = [
                "ffmpeg", "-i", video_filepath, "-ss", str(start_time), "-to", str(end_time),
                "-c", "copy", "-copyts", segment_filepath
            ]

            
            try:
                subprocess.run(command, check=True)
                print(f"Segment {i+1} saved as {segment_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error splitting segment {i+1}: {e}")

    def download_and_split(self, video_url, segment_filename):
        """Download the video and then split it into segments."""
        # Step 1: Download the entire video
        video_filepath = self.download_video(video_url, segment_filename)
        if video_filepath is None:
            return

        # Step 2: Get video duration
        duration = self.get_video_duration(video_url)

        # Step 3: Split the video into segments
        self.split_video_into_segments(video_filepath, segment_filename, duration)

if __name__ == "__main__":
    # Initialize the downloader class
    downloader = YoutubeSegmentDownloader()

    # Prompt user for YouTube link and file name
    video_url = input("Enter the YouTube link: ").strip()
    segment_filename = input("Enter a base name for the segment files (e.g., 'myVideo'): ").strip()

    # Download and split the video into segments
    downloader.download_and_split(video_url, segment_filename)
