import demucs.separate
import sys

def run_demucs():
    filename = input("Enter the audio filename: ").strip()
    sys.argv = ["demucs", "--mp3", "--mp3-bitrate", "320", filename]
    demucs.separate.main()

if __name__ == "__main__":
    run_demucs()
