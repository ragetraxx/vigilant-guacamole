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

    video_url_escaped = shlex.quote(url)
    overlay_path_escaped = shlex.quote(OVERLAY)

    # Ensure text is safely formatted for drawtext
    overlay_text = title.replace(":", r"\:").replace("'", r"\'").replace('"', r'\"')

    command = f"""
    ffmpeg -re -stream_loop -1 -fflags +genpts -rtbufsize 256M -probesize 50M -analyzeduration 2000000 \
    -i {video_url_escaped} -i {overlay_path_escaped} \
    -filter_complex "[1:v]scale='if(gt(a,main_w/main_h),main_w,-1)':'if(gt(a,main_w/main_h),-1,main_h)'[ovr]; \
                     [0:v][ovr]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2, \
                     drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -r 30 \
    -c:a aac -b:a 192k -ar 48000 -strict experimental \
    -f flv {shlex.quote(RTMP_URL)}
    """

    try:
        process = subprocess.run(command, shell=True)
        if process.returncode != 0:
            print(f"Warning: FFmpeg exited with code {process.returncode}")
    except Exception as e:
        print(f"Error streaming {title}: {e}")

if __name__ == "__main__":
    movies = load_movies()
    
    while True:
        movie = random.choice(movies)
        print(f"Streaming: {movie['title']}")
        start_time = time.time()
        stream_movie(movie)

        # Ensure a minimum duration before switching
        elapsed_time = time.time() - start_time
        if elapsed_time < 10:
            time.sleep(10 - elapsed_time)  # Ensures at least 10 seconds before switching
