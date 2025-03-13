import json
import random
import subprocess
import shlex
import time

MOVIE_FILE = "movies.json"
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY = "overlay.png"
LOG_FILE = "ffmpeg_log.txt"  # Log file to capture errors

def load_movies():
    with open(MOVIE_FILE, "r") as f:
        return json.load(f)

def stream_movie(movie):
    title = movie["title"]
    url = movie["url"]

    video_url_escaped = shlex.quote(url)
    overlay_path_escaped = shlex.quote(OVERLAY)

    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    command = f"""
    ffmpeg -re -i {video_url_escaped} -i {overlay_path_escaped} \
    -filter_complex "[1:v]scale=min(main_w,overlay_w):min(main_h,overlay_h)[ovr]; \
                     [0:v][ovr]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2, \
                     drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -r 30 \
    -c:a aac -b:a 192k -ar 48000 -f flv {shlex.quote(RTMP_URL)}
    """

    print("Running FFmpeg Command:\n", command)  # Print command for debugging

    with open(LOG_FILE, "w") as log:
        process = subprocess.run(command, shell=True, stderr=log, stdout=log)

    if process.returncode != 0:
        print(f"FFmpeg failed. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    movies = load_movies()
    
    while True:
        movie = random.choice(movies)
        print(f"Streaming: {movie['title']}")
        stream_movie(movie)

        time.sleep(5)  # Short delay before playing the next movie
