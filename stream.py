import os
import json
import random
import time
import shlex

# RTMP server
rtmp_url = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
overlay_path = "overlay.png"

# Tracking files
index_file = "last_movie_index.txt"
played_movies_file = "played_movies.txt"

def load_movies():
    try:
        with open("movies.json", "r") as file:
            movies = json.load(file)
        return [m for m in movies if "url" in m and "title" in m]
    except Exception as e:
        print(f"Failed to load movies.json: {e}")
        return []

def get_played_movies():
    return set(open(played_movies_file).read().splitlines()) if os.path.exists(played_movies_file) else set()

def save_played_movie(title):
    with open(played_movies_file, "a") as file:
        file.write(title + "\n")

movies = load_movies()

# First-time check: Start with a random movie
if not os.path.exists(played_movies_file) or os.stat(played_movies_file).st_size == 0:
    print("First time running, picking a random movie...")
    movie = random.choice(movies)
else:
    played_movies = get_played_movies()
    available_movies = [m for m in movies if m["title"] not in played_movies]
    if not available_movies:
        print("All movies played. Resetting list...")
        open(played_movies_file, "w").close()  # Clear file
        available_movies = movies
    movie = random.choice(available_movies)

video_url = movie["url"]
overlay_text = movie["title"].replace(":", "\\:").replace("'", "\\'")

# Escape paths
video_url_escaped = shlex.quote(video_url)
overlay_path_escaped = shlex.quote(overlay_path)

# Low-latency FFmpeg command
command = f"""
ffmpeg -re -fflags nobuffer -rtbufsize 128M -probesize 10M -analyzeduration 1000000 \
-threads 2 -i {video_url_escaped} -i {overlay_path_escaped} \
-filter_complex "[1:v]scale2ref=w=main_w:h=main_h:force_original_aspect_ratio=decrease[ovr][base];[base][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20,fps=30" \
-c:v libx264 -preset fast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 \
-c:a aac -b:a 192k -ar 48000 -f flv {shlex.quote(rtmp_url)}
"""

print(f"Streaming: {movie['title']} ({video_url})")
save_played_movie(movie["title"])

# Start streaming
os.system(command)
