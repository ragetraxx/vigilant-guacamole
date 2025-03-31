import os
import json
import subprocess
import time

# ✅ Configuration
PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")
OVERLAY = os.path.abspath("overlay.png")
MAX_RETRIES = 3
RETRY_DELAY = 60

if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is NOT set!")
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
            if not movies:
                print("❌ ERROR: play.json is empty!")
                return []
            return movies
    except json.JSONDecodeError:
        print("❌ ERROR: Failed to parse play.json!")
        return []

def stream_movie(movie):
    """Stream a single movie with reduced buffering."""
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
        "-rtbufsize", "4M",  # ✅ Lower buffer for less latency
        "-probesize", "16M",  # ✅ Faster start
        "-analyzeduration", "16M",
        "-i", url,
        "-i", OVERLAY,
        "-filter_complex",
        "[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"  
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-crf", "18",
        "-maxrate", "5000k",
        "-bufsize", "4000k",  # ✅ Further reduced buffer
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-movflags", "+faststart",
        "-f", "flv",
        RTMP_URL,
        "-loglevel", "error",
    ]

    print(f"🎬 Now Streaming: {title}")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # ✅ Prevent blocking, handle output properly
        stdout, stderr = process.communicate()
        if stderr:
            print(stderr)

    except Exception as e:
        print(f"❌ ERROR: FFmpeg failed for '{title}' - {str(e)}")

def main():
    """Main function to stream all movies in sequence."""
    retry_attempts = 0

    while retry_attempts < MAX_RETRIES:
        movies = load_movies()

        if not movies:
            retry_attempts += 1
            print(f"❌ ERROR: No movies available! Retrying ({retry_attempts}/{MAX_RETRIES}) in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            continue

        retry_attempts = 0  

        while True:
            for movie in movies:
                stream_movie(movie)
                print("🔄 Movie ended. Playing next movie...")

            print("🔄 All movies played, restarting from the beginning...")

    print("❌ ERROR: Maximum retry attempts reached. Exiting.")

if __name__ == "__main__":
    main()
