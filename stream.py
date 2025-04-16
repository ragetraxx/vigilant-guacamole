import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
OVERLAY = os.path.abspath("overlay.png")
RETRY_DELAY = 60
DEBUG = True

# ✅ Load stream URL from GitHub secret or local env
STREAM_URL = os.getenv("STREAM_URL")

if not STREAM_URL:
    print("❌ ERROR: STREAM_URL environment variable not set!")
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
        return movies if movies else []
    except Exception as e:
        print(f"❌ Failed to load {PLAY_FILE}: {e}")
        return []

def escape_drawtext(text):
    return text.replace('\\', '\\\\\\\\').replace(':', '\\:').replace("'", "\\'")

def detect_format(url):
    return "mpegts" if url.startswith("srt://") else "flv"

def stream_movie(movie):
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ Missing URL for '{title}'")
        return

    overlay_text = escape_drawtext(title)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    output_format = detect_format(STREAM_URL)

    filter_complex = (
        f"[0:v][1:v]scale2ref[v0][v1];"
        f"[v0][v1]overlay=0:0,"
        f"drawtext=fontfile={font_path}:text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30"
    )

    command = [
        "ffmpeg", "-re", "-i", url, "-i", OVERLAY, "-filter_complex", filter_complex,
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", "2800k", "-bufsize", "4000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", output_format, STREAM_URL
    ]

    print(f"\n🎬 Now Streaming: {title}\n▶️ Source URL: {url}\n📡 Output: {STREAM_URL} ({output_format})")

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
