import json
import random
import subprocess
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

    command = [
        "ffmpeg",
        "-re", "-i", url,  # Input: Movie URL
        "-i", OVERLAY, "-filter_complex",
        f"[1:v]scale=iw:ih[ovrl];[0:v][ovrl]overlay=0:0,"
        f"drawtext=text='{title}':font='Arial':x=10:y=10:fontsize=24:fontcolor=white",
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "3000k",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv", RTMP_URL  # Output: RTMP Server
    ]

    subprocess.run(command)

if __name__ == "__main__":
    movies = load_movies()
    while True:
        movie = random.choice(movies)
        print(f"Streaming: {movie['title']}")
        stream_movie(movie)
        time.sleep(5)  # Small delay before playing the next movie
