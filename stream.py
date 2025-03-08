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

    # Filter out invalid entries
    valid_movies = [m for m in movies if "url" in m and "title" in m]

    if not valid_movies:
        raise ValueError("No valid movies found in JSON file.")

    # Select a random movie
    movie = random.choice(valid_movies)

    video_url = movie["url"]
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
