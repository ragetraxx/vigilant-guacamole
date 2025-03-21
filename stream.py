import os
import json
import subprocess
import time
import shutil

PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")  # ✅ Get RTMP_URL from environment
OVERLAY = "overlay.png"
MAX_RETRIES = 3  # Maximum retry attempts if no movies are found
FFMPEG_LOG_FILE = "ffmpeg.log"  # Log FFmpeg output

# ✅ Ensure RTMP_URL is set
if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is NOT set! Check GitHub Secrets.")
    exit(1)

# ✅ Ensure FFmpeg is installed
if not shutil.which("ffmpeg"):
    print("❌ ERROR: FFmpeg is not installed or not in PATH!")
    exit(1)

# ✅ Ensure required files exist
if not os.path.exists(PLAY_FILE):
    print(f"❌ ERROR: {PLAY_FILE} not found!")
    exit(1)

if not os.path.exists(OVERLAY):
    print(f"❌ ERROR: Overlay image '{OVERLAY}' not found!")
    exit(1)

def load_movies():
    """Load movies from play.json in their original order."""
    try:
        with open(PLAY_FILE, "r") as f:
            movies = json.load(f)
            if not movies:
                print("❌ ERROR: play.json is empty!")
                return []
            return list(movies)  # ✅ Ensure it's a list and preserves order
    except json.JSONDecodeError:
        print("❌ ERROR: Failed to parse play.json! Check for syntax errors.")
        return []

def stream_movie(movie):
    """Stream a single movie using FFmpeg, ensuring it plays fully before continuing."""
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ ERROR: Missing URL for movie '{title}'")
        return

    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    command = [
        "ffmpeg",
        "-re",
        "-fflags", "+genpts",
        "-rtbufsize", "32M",
        "-probesize", "1M",
        "-analyzeduration", "500000",
        "-i", url,
        "-i", OVERLAY,
        "-filter_complex",
        f"[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20",
        "-c:v", "libx264",
        "-preset", "fast",
        "-tune", "film",
        "-b:v", "4000k",
        "-crf", "23",
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

    try:
        with open(FFMPEG_LOG_FILE, "w") as log_file:
            process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
        
        process.wait()  # ✅ Wait until the movie finishes before continuing

        if process.returncode == 0:
            print(f"✅ Finished streaming: {title}")
        else:
            print(f"❌ ERROR: FFmpeg exited with error code {process.returncode} for '{title}'")
            print(f"📝 Check '{FFMPEG_LOG_FILE}' for details.")

    except Exception as e:
        print(f"❌ ERROR: FFmpeg failed for '{title}' - {str(e)}")

def main():
    """Play all movies sequentially, ensuring each plays fully before continuing."""
    retry_attempts = 0

    while retry_attempts < MAX_RETRIES:
        movies = load_movies()

        if not movies:
            retry_attempts += 1
            print(f"❌ ERROR: No movies available! Retrying ({retry_attempts}/{MAX_RETRIES})...")
            time.sleep(60)
            continue

        retry_attempts = 0  # Reset retry counter

        for movie in movies:
            stream_movie(movie)  # ✅ Movie will play completely before next one starts
            print("🔄 Movie ended. Playing next movie...")
            time.sleep(10)  # Short pause before next movie

        print("🔄 All movies played. Reloading play.json...")

    print("❌ ERROR: Maximum retry attempts reached. Exiting.")

if __name__ == "__main__":
    main()
