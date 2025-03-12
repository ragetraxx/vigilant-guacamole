import os
import json
import random
import shlex

# RTMP Server Details
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY_PATH = "overlay.png"

# Movie Tracking Files
MOVIE_FILE = "movies.json"
PLAYED_FILE = "played_movies.txt"

# Load Movies
def load_movies():
    try:
        with open(MOVIE_FILE, "r") as file:
            movies = json.load(file)
        return [m for m in movies if "url" in m and "title" in m]
    except Exception as e:
        print(f"Failed to load movies.json: {e}")
        return []

# Get Played Movies
def get_played_movies():
    return set(open(PLAYED_FILE).read().splitlines()) if os.path.exists(PLAYED_FILE) else set()

# Save Played Movie
def save_played_movie(title):
    with open(PLAYED_FILE, "a") as file:
        file.write(title + "\n")

# Select a Movie
movies = load_movies()
played_movies = get_played_movies()

# Choose a new movie
available_movies = [m for m in movies if m["title"] not in played_movies]
if not available_movies:
    print("All movies played. Resetting list...")
    open(PLAYED_FILE, "w").close()  # Clear file
    available_movies = movies

selected_movie = random.choice(available_movies)
video_url = selected_movie["url"]
overlay_text = selected_movie["title"].replace(":", "\\:").replace("'", "\\'")

# Save the movie as played
save_played_movie(selected_movie["title"])

# FFmpeg Streaming Command (Low Latency)
ffmpeg_command = f"""
ffmpeg -re -fflags nobuffer -rtbufsize 64M -probesize 10M -analyzeduration 500000 \
-i "{video_url}" -i "{OVERLAY_PATH}" \
-filter_complex "[1:v]scale=main_w:main_h[ovr];[0:v][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
-c:v libx264 -preset ultrafast -tune zerolatency -b:v 1200k -maxrate 1500k -bufsize 2000k -pix_fmt yuv420p -g 50 \
-c:a aac -b:a 128k -ar 44100 -f flv "{RTMP_URL}"
"""

print(f"Now Streaming: {selected_movie['title']} ({video_url})")

# Start the Stream
os.system(ffmpeg_command)
