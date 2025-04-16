import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
OVERLAY = os.path.abspath("overlay.png")
RETRY_DELAY = 60
DEBUG = True

# ✅ Load SRT URL from GitHub secret or environment variable
STREAM_URL = os.getenv("SRT_URL")

if not STREAM_URL:
    print("❌ ERROR: SRT_URL environment variable is NOT set!")
    exit(1)

# ✅ Ensure required files exist
if not os.path.exists(PLAY_FILE):
    print(f"❌ ERROR: {PLAY_FILE} not found!")
    exit(1)

if not os.path.exists(OVERLAY):
    print(f"❌ ERROR: Overlay image '{OVERLAY}' not found!")
    exit(1)

def load_movies():
    """Load all movies from play.json."""
    try:
        with open(PLAY_FILE, "r") as f:
            movies = json.load(f)
        return movies if movies else []
    except Exception as e:
        print(f"❌ Failed to load {PLAY_FILE}: {e}")
        return []

def escape_drawtext(text):
    """Escape only necessary characters for FFmpeg drawtext."""
    return text.replace('\\', '\\\\\\\\').replace(':', '\\:').replace("'", "\\'")

def stream_movie(movie):
    """Stream a single movie using FFmpeg."""
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ Missing URL for '{title}'")
        return

    overlay_text = escape_drawtext(title)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    command = [
        "ffmpeg", "-re", "-i", url, "-i", OVERLAY, "-filter_complex",
        f"[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,drawtext=fontfile={font_path}:text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", "2800k", "-bufsize", "4000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "mpegts", STREAM_URL  # Using MPEG-TS for SRT streaming
    ]

    print(f"\n🎬 Now Streaming: {title}\n▶️ Source URL: {url}\n📡 Output: {STREAM_URL}")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            if DEBUG:
                print(line, end="")
        process.wait()
    except Exception as e:
        print(f"❌ FFmpeg failed for '{title}': {e}")

def main():
    while True:
        movies = load_movies()
        if not movies:
            print(f"⏳ No movies found. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            continue
        for movie in movies:
            stream_movie(movie)
            print("🔁 Stream ended. Next...\n")
            time.sleep(2)

if __name__ == "__main__":
    main()
