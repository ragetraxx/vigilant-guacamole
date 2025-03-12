import json
import random
import subprocess
import shlex
import time

MOVIE_FILE = "movies.json"
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY = "overlay.png"

def load_movies():
    with open(MOVIE_FILE, "r") as f:
        return json.load(f)

def stream_movie(movie):
    title = movie["title"]
    url = movie["url"]

    # Escape paths to prevent issues
    video_url_escaped = shlex.quote(url)
    overlay_path_escaped = shlex.quote(OVERLAY)
    overlay_text = shlex.quote(title)

    command = f"""
    ffmpeg -re -fflags nobuffer -rtbufsize 128M -probesize 10M -analyzeduration 1000000 \
    -threads 2 -i {video_url_escaped} -i {overlay_path_escaped} \
    -filter_complex "[1:v]scale2ref=w=main_w:h=main_h:force_original_aspect_ratio=1[ovr][base];[base][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
    -c:v libx264 -preset fast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 192k -ar 48000 -f flv {shlex.quote(RTMP_URL)}
    """

    subprocess.run(command, shell=True)

if __name__ == "__main__":
    movies = load_movies()
    while True:
        movie = random.choice(movies)
        print(f"Streaming: {movie['title']}")
        stream_movie(movie)
        time.sleep(5)  # Small delay before playing the next movie
