import os
import json
import random
import time

# RTMP server
rtmp_url = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"

# Overlay image
overlay_path = "overlay.png"

while True:  # Infinite loop
    # Load movies from JSON
    with open("movies.json", "r") as file:
        movies = json.load(file)

    # Ensure movies is a list
    if not isinstance(movies, list):
        raise ValueError("Invalid JSON format: Expected a list of movies.")

    # Select a random movie
    movie = random.choice(movies)

    # Ensure required keys exist
    if "url" not in movie or "title" not in movie:
        raise ValueError("Invalid movie format: Each movie must have 'url' and 'title' keys.")

    video_url = movie["url"]  # Use "url" instead of "path"
    overlay_text = movie["title"].replace(":", "\\:")  # Escape special characters

    # FFmpeg command to dynamically fit overlay to video resolution
    command = f"""
    ffmpeg -re -i "{video_url}" -i "{overlay_path}" \
    -filter_complex "[1:v]scale2ref=w=iw:h=ih[ovr][base];[base][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
    -c:v libx264 -preset veryfast -b:v 4000k -maxrate 5000k -bufsize 10000k -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 192k -ar 48000 -f flv "{rtmp_url}"
    """

    print(f"Streaming: {movie['title']} ({video_url})")

    # Run streaming
    os.system(command)

    # Short delay before selecting the next video
    time.sleep(5)
