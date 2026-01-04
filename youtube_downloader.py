import yt_dlp
import os
import subprocess
import json

class YoutubeSegmentDownloader:
    SEGMENT_DURATION = 30 * 60  # 30 minutes in seconds

    def __init__(self, config_path="config.json"):
        """Initialize the downloader."""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            self.download_path = config.get("download_path", "./downloads")
            print(f"Download path selected: {self.download_path}")
        else:
            raise RuntimeError("Error: config.json not found. Re-run the setup.py script and ensure you enter a valid path which has read/write/execute permissions.")

    def get_download_path(self):
        return self.download_path

    def get_video_duration(self, video_url):
        """Retrieve the video duration in seconds."""
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            result = ydl.extract_info(video_url, download=False)
            return result['duration']  # Returns duration in seconds

    def download_video(self, video_url, segment_filename):
        """Download a mobile-friendly test video: H.264 + AAC in MP4."""
        # Ensure download path exists
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        video_filepath = os.path.join(self.download_path, f"{segment_filename}.mp4")

        ydl_opts = {
            'format': '18',  # format 18 = 360p H.264 + AAC MP4 (guaranteed iOS-friendly)
            'outtmpl': video_filepath,
            'noplaylist': True,
            'quiet': False,
            'merge_output_format': 'mp4'
        }

        try:
            print(f"Downloading test video to: {video_filepath}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print("Download complete!")
            return video_filepath
        except Exception as e:
            print(f"Download failed: {e}")
            return None
        
    
    def clip_existing_video(self, input_path, clip_name, start_time, end_time):
        """Create a new video clip from an existing MP4 file.
        
        Parameters:
            input_path (str): Path to the source MP4 file
            clip_name (str): Name for the output clip (without .mp4)
            start_time (float or str): Start time in seconds or "HH:MM:SS"
            end_time (float or str): End time in seconds or "HH:MM:SS"
        
        Returns:
            str: Path to the created clip
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        # Ensure download path exists
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        output_path = os.path.join(self.download_path, f"{clip_name}.mp4")

        # ffmpeg command: -ss before -i is faster but less accurate for non-keyframe start
        command = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",  # avoid re-encoding for speed
            "-y",          # overwrite if exists
            output_path
        ]

        try:
            print(f"Creating clip: {output_path}")
            subprocess.run(command, check=True)
            print(f"Clip created successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error creating clip: {e}")
            return None
        

    def combine_videos(self, video_filepaths, output_filename, delete_sources=False):
        if not video_filepaths:
            print("No video files provided.")
            return None

        for path in video_filepaths:
            if not os.path.exists(path):
                print(f"File not found: {path}")
                return None

        output_filepath = os.path.join(self.download_path, f"{output_filename}.mp4")
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        # Build input args
        inputs = []
        for path in video_filepaths:
            inputs.extend(["-i", path])

        # Build filter_complex dynamically
        filter_parts = []
        for i in range(len(video_filepaths)):
            filter_parts.append(f"[{i}:v]fps=25,scale=640:360[v{i}];")
        video_labels = "".join(f"[v{i}][{i}:a]" for i in range(len(video_filepaths)))
        filter_complex = "".join(filter_parts) + f"{video_labels}concat=n={len(video_filepaths)}:v=1:a=1[v][a]"

        command = [
            "ffmpeg",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            output_filepath
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Combined video saved as: {output_filepath}")

            if delete_sources:
                for path in video_filepaths:
                    try:
                        os.remove(path)
                        print(f"Deleted source file: {path}")
                    except Exception as e:
                        print(f"Failed to delete {path}: {e}")

            return output_filepath

        except subprocess.CalledProcessError as e:
            print(f"Error combining videos: {e}")
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

    # downloader.combine_videos(["D:\\Music\\Departure - Moody Blues.mp4", "D:\\Music\\Ride my seesaw - Moody Blues.mp4"], "Departure and Ride my seesaw - Moody Blues", delete_sources=True)
    # downloader.clip_existing_video(input_path="D:\\Music\\Legend of A Mind - Moody Blues.mp4", clip_name="Flute solo - Legend of A Mind - Moody Blues", start_time="00:02:42", end_time="00:04:36")

    # Prompt user for YouTube link and file name
    video_url = input("Enter the YouTube link: ").strip()
    segment_filename = input("Enter a base name for the segment files (e.g., 'myVideo'): ").strip()

    # Download and split the video into segments
    downloader.download_video(video_url, segment_filename)
