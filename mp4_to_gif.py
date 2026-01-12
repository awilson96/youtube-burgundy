import sys
import os
import subprocess
import tempfile

def mp4_to_gif(mp4_path):
    if not os.path.isfile(mp4_path):
        print("File not found.")
        return

    folder = os.path.dirname(mp4_path)
    name = os.path.splitext(os.path.basename(mp4_path))[0]
    gif_path = os.path.join(folder, f"{name}.gif")
    palette_path = os.path.join(tempfile.gettempdir(), f"{name}_palette.png")

    # Step 1: generate palette
    palette_cmd = [
        "ffmpeg", "-y",
        "-i", mp4_path,
        "-vf", "fps=15,scale=960:-1:flags=lanczos,palettegen",
        palette_path
    ]

    # Step 2: create gif using palette
    gif_cmd = [
        "ffmpeg", "-y",
        "-i", mp4_path,
        "-i", palette_path,
        "-lavfi", "fps=15,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse",
        gif_path
    ]

    subprocess.run(palette_cmd, check=True)
    subprocess.run(gif_cmd, check=True)

    print(f"High-quality GIF created at: {gif_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mp4_to_gif.py your_video.mp4")
    else:
        mp4_to_gif(sys.argv[1])
