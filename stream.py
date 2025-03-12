import os
import json
import random
import time
import subprocess

# RTMP server details
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY_PATH = "overlay.png"
MOVIES_FILE = "movies.json"
PLAYED_MOVIES_FILE = "played_movies.txt"

# Load available movies
def load_movies():
    try:
        with open(MOVIES_FILE, "r") as file:
            movies = json.load(file)
        return [m for m in movies if "url" in m and "title" in m]
    except Exception as e:
        print(f"Error loading movies.json: {e}")
        return []

# Get list of already played movies
def get_played_movies():
    return set(open(PLAYED_MOVIES_FILE).read().splitlines()) if os.path.exists(PLAYED_MOVIES_FILE) else set()

# Save played movie to file
def save_played_movie(title):
    with open(PLAYED_MOVIES_FILE, "a") as file:
        file.write(title + "\n")

# Load movies
movies = load_movies()

# Infinite streaming loop
while True:
    played_movies = get_played_movies()
    available_movies = [m for m in movies if m["title"] not in played_movies]

    if not available_movies:
        print("All movies played. Resetting list...")
        open(PLAYED_MOVIES_FILE, "w").close()  # Reset played list
        available_movies = movies

    # Pick a random movie
    movie = random.choice(available_movies)
    video_url = movie["url"]
    overlay_text = movie["title"].replace(":", "\\:").replace("'", "\\'")

    # FFmpeg command to stream the movie
    ffmpeg_command = f"""
    ffmpeg -re -i "{video_url}" -i "{OVERLAY_PATH}" \
    -filter_complex "[1:v]scale=main_w:main_h[ovr];[0:v][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
    -c:v libx264 -preset fast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 192k -ar 48000 -f flv "{RTMP_URL}"
    """

    print(f"🎬 Now Streaming: {movie['title']} ({video_url})")
    save_played_movie(movie["title"])

    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠ FFmpeg crashed: {e}. Restarting...")

    print("⏳ Waiting 30 seconds before playing next movie...")
    time.sleep(30)  # Short pause before selecting the next movie
