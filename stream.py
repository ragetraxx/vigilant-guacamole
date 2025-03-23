import os
import json
import subprocess
import time

PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")  # ✅ Get RTMP_URL from GitHub Secret
OVERLAY = "overlay.png"
MAX_RETRIES = 3  # Retry attempts if no movies are found

# ✅ Check if RTMP_URL is set
if not RTMP_URL:
    print("❌ ERROR: RTMP_URL environment variable is NOT set! Check GitHub Secrets.")
    exit(1)

# ✅ Ensure required files exist
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
        print("❌ ERROR: Failed to parse play.json! Check for syntax errors.")
        return []

def stream_movie(movie):
    """Stream a single movie using FFmpeg and wait for it to finish."""
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
        "-rtbufsize", "8M",  # ✅ Increased buffer to reduce stalling
        "-probesize", "64M",
        "-analyzeduration", "64M",
        "-i", url,
        "-i", OVERLAY,
        "-filter_complex",
        f"[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=28:x=20:y=20",
        "-c:v", "libx264",
        "-preset", "ultrafast",  # ✅ Faster encoding to avoid delays
        "-tune", "zerolatency",  # ✅ Reduces delay & lag
        "-crf", "23",  # ✅ Balanced quality & performance
        "-maxrate", "4000k",  # ✅ Lower max bitrate for stable stream
        "-bufsize", "8000k",  # ✅ Increased buffer to prevent stalling
        "-pix_fmt", "yuv420p",
        "-g", "60",  # ✅ Better keyframe spacing
        "-r", "30",  # ✅ Force constant frame rate for stability
        "-c:a", "aac",
        "-b:a", "128k",  # ✅ Lower audio bitrate for stable stream
        "-ar", "44100",  # ✅ Ensures compatibility
        "-movflags", "+faststart",
        "-f", "flv",
        RTMP_URL,
        "-loglevel", "debug",  # ✅ Show all logs for debugging
        "-report",  # ✅ Saves logs to a file for troubleshooting
    ]

    print(f"🎬 Now Streaming: {title}")
    print("Executing FFmpeg command:", " ".join(command))

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # ✅ Wait for FFmpeg to finish before playing the next movie
        for line in process.stderr:
            print(line, end="")

        process.wait()

    except Exception as e:
        print(f"❌ ERROR: FFmpeg failed for '{title}' - {str(e)}")

def main():
    """Main function to stream all movies in sequence."""
    retry_attempts = 0

    while retry_attempts < MAX_RETRIES:
        movies = load_movies()

        if not movies:
            retry_attempts += 1
            print(f"❌ ERROR: No movies available! Retrying ({retry_attempts}/{MAX_RETRIES})...")
            time.sleep(60)
            continue

        retry_attempts = 0  # Reset retry counter on success

        while True:
            for movie in movies:
                stream_movie(movie)  # ✅ This will now wait for each movie to finish before starting the next one
                print("🔄 Movie ended. Playing next movie...")

            print("🔄 All movies played, restarting from the beginning...")

    print("❌ ERROR: Maximum retry attempts reached. Exiting.")

if __name__ == "__main__":
    main()
