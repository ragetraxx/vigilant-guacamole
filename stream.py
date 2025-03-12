import os
import json
import random
import time
import shlex

# RTMP server
rtmp_url = "rtmp://ssh101.bozztv.com:1935/ssh101/ragetv"

# Overlay image
overlay_path = "overlay.png"

# Function to load movies dynamically
def load_movies():
    try:
        with open("movies.json", "r") as file:
            movies = json.load(file)

        # Filter out valid movies  
        valid_movies = [m for m in movies if "url" in m and "title" in m]  
        if not valid_movies:  
            print("No valid movies found in JSON file.")  
            return []  
        return valid_movies  

    except Exception as e:  
        print(f"Failed to load movies.json: {e}")  
        return []

while True:  # Infinite loop
    try:
        # Reload movies list each time before selecting a new movie
        movies = load_movies()

        if not movies:  
            print("No valid movies available. Retrying in 10 seconds...")  
            time.sleep(10)  
            continue  

        # Select a random movie  
        movie = random.choice(movies)  
        video_url = movie["url"]  
        overlay_text = movie["title"].replace(":", "\\:").replace("'", "\\'")  # Escape special characters  

        # Safely escape paths  
        video_url_escaped = shlex.quote(video_url)  
        overlay_path_escaped = shlex.quote(overlay_path)  

        # FFmpeg command  
        command = f"""  
        ffmpeg -re -i {video_url_escaped} -i {overlay_path_escaped} \  
        -filter_complex "[1:v]scale2ref=w=iw:h=ih[ovr][base];[base][ovr]overlay=0:0,drawtext=text='{overlay_text}':fontcolor=white:fontsize=24:x=20:y=20" \  
        -c:v libx264 -preset veryfast -b:v 2000k -maxrate 2500k -bufsize 5000k -pix_fmt yuv420p -g 50 \  
        -c:a aac -b:a 192k -ar 48000 -f flv {shlex.quote(rtmp_url)}  
        """  

        print(f"Streaming: {movie['title']} ({video_url})")  

        # Run streaming  
        os.system(command)  

        # Short delay before selecting the next video  
        time.sleep(3)  

    except Exception as e:  
        print(f"Error: {e}")  
        time.sleep(10)  # Delay before retrying
