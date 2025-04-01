import os
import json
import subprocess
import time

PLAY_FILE = "play.json"
RTMP_URL = os.getenv("RTMP_URL")
OVERLAY = os.path.abspath("overlay.png")
MAX_RETRIES, RETRY_DELAY = 3, 60

if not RTMP_URL:
    exit("❌ ERROR: RTMP_URL not set!")
if not all(map(os.path.exists, [PLAY_FILE, OVERLAY])):
    exit(f"❌ ERROR: Missing required files!")

def load_movies():
    try:
        with open(PLAY_FILE) as f:
            movies = json.load(f)
            return movies if movies else exit("❌ ERROR: play.json is empty!")
    except json.JSONDecodeError:
        exit("❌ ERROR: Failed to parse play.json!")

def stream_movie(movie):
    url, title = movie.get("url"), movie.get("title", "Unknown")
    if not url:
        return print(f"❌ ERROR: Missing URL for '{title}'")
    
    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')
    command = [
        "ffmpeg", "-re", "-fflags", "+genpts", "-rtbufsize", "4M", "-probesize", "16M", "-analyzeduration", "16M",
        "-i", url, "-i", OVERLAY, "-filter_complex", 
        f"[0:v][1:v]scale2ref[v0][v1];[v0][v1]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=20:x=30:y=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-crf", "18", "-maxrate", "5000k", "-bufsize", "4000k",
        "-pix_fmt", "yuv420p", "-g", "60", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", "-f", "flv", RTMP_URL,
        "-loglevel", "error"
    ]
    print(f"🎬 Streaming: {title}")
    subprocess.run(command, text=True, stderr=subprocess.PIPE)

def main():
    retries = 0
    while retries < MAX_RETRIES:
        movies = load_movies()
        if not movies:
            retries += 1
            print(f"❌ ERROR: No movies! Retrying ({retries}/{MAX_RETRIES}) in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            continue
        retries = 0
        while True:
            for movie in movies:
                stream_movie(movie)
                print("🔄 Next movie...")
            print("🔄 Restarting playlist...")
    print("❌ ERROR: Max retries reached. Exiting.")

if __name__ == "__main__":
    main()
