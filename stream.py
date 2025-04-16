import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")
OVERLAY = os.path.abspath("overlay.png")
RETRY_DELAY = 60
DEBUG = True  # Set to False to suppress FFmpeg logs

# ✅ Check if RTMP_URL is set
if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is NOT set!")
    exit(1)

# ✅ Ensure required files exist
if not os.path.exists(PLAY_FILE):
    print(f"❌ ERROR: {PLAY_FILE} not found!")
    exit(1)

if not os.path.exists(OVERLAY):
    print(f"❌ ERROR: Overlay image '{OVERLAY}' not found!")
    exit(1)

def load_movies():
    try:
        with open(PLAY_FILE, "r") as f:
            movies = json.load(f)
        if not movies:
            print("❌ ERROR: No movies found in play.json!")
            return []
        return movies
    except Exception as e:
        print(f"❌ ERROR: Failed to load {PLAY_FILE} - {str(e)}")
        return []

def escape_drawtext(text):
    return text.replace('\\', '\\\\\\\\').replace(':', '\\:').replace("'", "\\'")

def stream_movie(movie):
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ ERROR: Missing URL for movie '{title}'")
        return

    overlay_text = escape_drawtext(title)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    filter_complex = (
        f"[0:v][1:v]scale2ref[v0][v1];"
        f"[v0][v1]overlay=0:0,"
        f"drawtext=fontfile={font_path}:text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30"
    )

    command = [
        "ffmpeg", "-re", "-i", url, "-i", OVERLAY, "-filter_complex", filter_complex,
        "-c:v", "libx264", "-profile:v", "main", "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", "2800k", "-maxrate", "2800k", "-bufsize", "4000k", "-pix_fmt", "yuv420p", "-g", "50", "-vsync", "cfr",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-f", "flv", "-rtmp_live", "live", RTMP_URL
    ]

    print(f"\n🎬 Now Streaming: {title}")
    print(f"▶️ URL: {url}")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            if DEBUG:
                print(line, end="")

        process.wait()

        if process.returncode != 0:
            print(f"⚠️ FFmpeg exited with code {process.returncode}")

    except Exception as e:
        print(f"❌ ERROR: Streaming failed for '{title}' - {str(e)}")

def main():
    while True:
        movies = load_movies()

        if not movies:
            print(f"⏳ Waiting for valid movie list... retrying in {RETRY_DELAY} sec.")
            time.sleep(RETRY_DELAY)
            continue

        for movie in movies:
            stream_movie(movie)
            print("🔁 Movie ended or failed. Moving to next...\n")
            time.sleep(2)  # Optional: brief pause between streams

if __name__ == "__main__":
    main()
