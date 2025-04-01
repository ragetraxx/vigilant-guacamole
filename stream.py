import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")  # Get RTMP_URL from GitHub Secret
OVERLAY = os.path.abspath("overlay.png")  # Absolute path for overlay
MAX_RETRIES = 3  # Retry attempts if no movies are found
RETRY_DELAY = 30  # Shorter retry delay for faster recovery

# ✅ Validate Environment
if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is NOT set! Check GitHub Secrets.")
    exit(1)

if not os.path.exists(PLAY_FILE):
    print(f"❌ ERROR: {PLAY_FILE} not found!")
    exit(1)

if not os.path.exists(OVERLAY):
    print(f"❌ ERROR: Overlay image '{OVERLAY}' not found!")
    exit(1)

def load_movies():
    """Load movies from play.json."""
    try:
        with open(PLAY_FILE, "r") as f:
            movies = json.load(f)
            return movies if movies else []
    except json.JSONDecodeError:
        print("❌ ERROR: Failed to parse play.json! Check for syntax errors.")
        return []

def stream_movie(movie):
    """Stream a movie using FFmpeg asynchronously."""
    title = movie.get("title", "Unknown Title")
    url = movie.get("url")

    if not url:
        print(f"❌ ERROR: Missing URL for movie '{title}'")
        return None

    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    command = [
        "ffmpeg",
        "-re",
        "-fflags", "+genpts",
        "-rtbufsize", "4M",  # ✅ Smaller buffer to minimize latency
        "-probesize", "16M",  # ✅ Reduced for faster startup
        "-analyzeduration", "16M",
        "-i", url,
        "-i", OVERLAY,
        "-filter_complex",
        "[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30",
        "-c:v", "libx264",
        "-preset", "superfast",  # ✅ Lower latency than ultrafast
        "-tune", "zerolatency",
        "-crf", "22",  # ✅ Slightly lower quality for stability
        "-maxrate", "4000k",
        "-bufsize", "4000k",  # ✅ Reduced to prevent long buffering
        "-pix_fmt", "yuv420p",
        "-g", "30",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-movflags", "+faststart",
        "-f", "flv",
        RTMP_URL,
        "-loglevel", "error",  # ✅ Only show errors
    ]

    print(f"🎬 Now Streaming: {title}")

    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

def main():
    """Continuously stream movies in sequence without delay."""
    retry_attempts = 0

    while retry_attempts < MAX_RETRIES:
        movies = load_movies()

        if not movies:
            retry_attempts += 1
            print(f"❌ ERROR: No movies available! Retrying ({retry_attempts}/{MAX_RETRIES}) in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            continue

        retry_attempts = 0  # Reset retry counter if movies exist

        while True:
            for movie in movies:
                process = stream_movie(movie)

                if process:
                    process.wait()  # ✅ Waits for current movie to finish

                print("🔄 Movie ended. Playing next movie...")

            print("🔄 All movies played. Restarting from the beginning...")

    print("❌ ERROR: Maximum retry attempts reached. Exiting.")

if __name__ == "__main__":
    main()
