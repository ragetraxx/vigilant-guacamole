import os
import json
import random
import shlex

# RTMP server details
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"
OVERLAY_PATH = "overlay.png"
MOVIES_FILE = "movies.json"
PLAYED_MOVIES_FILE = "played_movies.txt"

# Load movie list
def load_movies():
    try:
        with open(MOVIES_FILE, "r") as file:
            movies = json.load(file)
        return [m for m in movies if "url" in m and "title" in m]
    except Exception as e:
        print(f"Error: Failed to load {MOVIES_FILE} - {e}")
        return []

# Load already played movies
def get_played_movies():
    if os.path.exists(PLAYED_MOVIES_FILE):
        with open(PLAYED_MOVIES_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

# Save the played movie title
def save_played_movie(title):
    with open(PLAYED_MOVIES_FILE, "a") as file:
        file.write(title + "\n")

# Select the next movie to stream
def pick_movie(movies, played_movies):
    available_movies = [m for m in movies if m["title"] not in played_movies]
    
    if not available_movies:
        print("All movies played. Resetting the list...")
        open(PLAYED_MOVIES_FILE, "w").close()  # Clear the played movies file
        available_movies = movies
    
    return random.choice(available_movies) if available_movies else None

# Check if overlay exists
def check_overlay():
    if not os.path.exists(OVERLAY_PATH):
        print(f"Warning: Overlay file '{OVERLAY_PATH}' not found. Skipping overlay.")
        return False
    return True

# Main execution
def main():
    movies = load_movies()
    if not movies:
        print("No movies available. Exiting...")
        return

    played_movies = get_played_movies()
    movie = pick_movie(movies, played_movies)

    if not movie:
        print("No valid movie found. Exiting...")
        return

    video_url = movie["url"]
    overlay_text = movie["title"].replace(":", "\\:").replace("'", "\\'")

    # Escape URLs & paths for FFmpeg
    video_url_escaped = shlex.quote(video_url)
    overlay_path_escaped = shlex.quote(OVERLAY_PATH)

    # Check if overlay file exists
    use_overlay = check_overlay()

    # FFmpeg streaming command
    ffmpeg_command = f"""
    ffmpeg -re -fflags nobuffer -rtbufsize 128M -probesize 10M -analyzeduration 1000000 \
    -threads 2 -i {video_url_escaped} {'-i ' + overlay_path_escaped if use_overlay else ''} \
    -filter_complex "{'[1:v]scale=main_w:main_h[ovr];[0:v][ovr]overlay=0:0,' if use_overlay else ''}drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20,fps=30" \
    -c:v libx264 -preset fast -tune zerolatency -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 192k -ar 48000 -f flv {shlex.quote(RTMP_URL)}
    """

    print(f"Streaming: {movie['title']} ({video_url})")
    save_played_movie(movie["title"])

    # Execute FFmpeg command
    os.system(ffmpeg_command)

if __name__ == "__main__":
    main()
