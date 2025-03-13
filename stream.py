import json
import os
import subprocess
import shlex
import time
import random

MOVIE_FILE = "movies.json"
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY = "overlay.png"
MAX_RETRIES = 3  # Maximum retry attempts if no movies are found

def load_movies():
    """Load movies from JSON file."""
    if not os.path.exists(MOVIE_FILE):
        print(f"❌ ERROR: {MOVIE_FILE} not found!")
        return []

    with open(MOVIE_FILE, "r") as f:
        try:
            movies = json.load(f)
            if not movies:
                print("❌ ERROR: movies.json is empty!")
            return movies
        except json.JSONDecodeError:
            print("❌ ERROR: Failed to parse movies.json!")
            return []

def stream_movie(movie):
    """Stream a single movie using FFmpeg."""
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ ERROR: Missing URL for movie '{title}'")
        return

    video_url_escaped = shlex.quote(url)
    overlay_path_escaped = shlex.quote(OVERLAY)
    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    command = [
        "ffmpeg",
        "-re",
        "-fflags", "+genpts",
        "-rtbufsize", "32M",  # Reduced buffer size for faster start
        "-probesize", "1M",  # Faster stream analysis
        "-analyzeduration", "500000",
        "-i", video_url_escaped,
        "-i", overlay_path_escaped,
        "-filter_complex",
        f"[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20",
        "-c:v", "libx264",
        "-preset", "fast",  # Better quality than "ultrafast"
        "-tune", "film",  # Improves sharpness
        "-b:v", "4000k",  # Increased bitrate for less blur
        "-crf", "23",  # Controls quality, lower = better
        "-maxrate", "4500k",
        "-bufsize", "6000k",
        "-pix_fmt", "yuv420p",
        "-g", "50",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-f", "flv",
        RTMP_URL
    ]

    print(f"🎬 Now Streaming: {title}")
    subprocess.run(command)

def main():
    """Main function to continuously stream random movies."""
    retry_attempts = 0

    while retry_attempts < MAX_RETRIES:
        movies = load_movies()

        if not movies:
            retry_attempts += 1
            print(f"❌ ERROR: No movies available! Retrying ({retry_attempts}/{MAX_RETRIES})...")
            time.sleep(60)
            continue

        retry_attempts = 0  # Reset retry counter on success

        # Stream movies in **random** order (loop forever)
        while True:
            random.shuffle(movies)  # Shuffle movie list before playing
            for movie in movies:
                stream_movie(movie)

            print("🔄 Restarting random movie playlist...")

    print("❌ ERROR: Maximum retry attempts reached. Exiting.")

if __name__ == "__main__":
    main()
