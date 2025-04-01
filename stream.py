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

def get_video_properties(url):
    """Get video properties like frame rate, codec, and bitrate using FFmpeg."""
    command = [
        "ffmpeg",
        "-i", url,
        "-hide_banner"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # Parsing output to find video information
        output = result.stderr
        frame_rate = None
        codec = None
        bitrate = None

        # Extract frame rate (e.g., 23.976)
        if "fps" in output:
            frame_rate_line = next(line for line in output.splitlines() if "fps" in line)
            frame_rate = float(frame_rate_line.split()[1])

        # Extract codec (e.g., h264)
        if "Video:" in output:
            codec_line = next(line for line in output.splitlines() if "Video:" in line)
            codec = codec_line.split()[2]

        # Extract bitrate (if available)
        if "bitrate:" in output:
            bitrate_line = next(line for line in output.splitlines() if "bitrate:" in line)
            bitrate = int(bitrate_line.split()[1].replace('k', '000'))  # Convert k to proper value

        return frame_rate, codec, bitrate

    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to retrieve video properties: {e}")
        return None, None, None

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

    # Get video properties (frame rate, codec, bitrate)
    frame_rate, codec, bitrate = get_video_properties(url)

    if not frame_rate or not codec:
        print(f"❌ ERROR: Could not retrieve valid video properties for '{title}'")
        return None

    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    # Dynamic GOP size based on frame rate
    gop_size = int(frame_rate * 2)

    # Default buffer size and bitrate handling for dynamic sources
    max_rate = bitrate if bitrate else 3000 * 1000  # Use bitrate from source if available, else fallback
    buffer_size = max_rate * 2  # Typically double the maxrate for buffer size

    command = [
        "ffmpeg",
        "-re",
        "-fflags", "+genpts",
        "-rtbufsize", "2M",  # ✅ Smaller buffer to minimize latency
        "-probesize", "1M",  # ✅ Reduced for faster startup
        "-analyzeduration", "2M",
        "-i", url,
        "-i", OVERLAY,
        "-filter_complex",
        "[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,"
        f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30",
        "-c:v", "libx264",
        "-preset", "superfast",  # ✅ Lower latency than ultrafast
        "-tune", "zerolatency",
        "-crf", "22",  # ✅ Slightly lower quality for stability
        "-maxrate", f"{max_rate}",  # ✅ Dynamic bitrate based on source
        "-bufsize", f"{buffer_size}",  # ✅ Buffer size adjusted based on bitrate
        "-pix_fmt", "yuv420p",
        "-g", f"{gop_size}",  # ✅ GOP size dynamically set based on frame rate
        "-r", f"{frame_rate}",  # ✅ Use the detected frame rate from the video
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
