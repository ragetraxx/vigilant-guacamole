import json
import random

MOVIE_FILE = "movies.json"  # Permanent source JSON file
PLAY_FILE = "play.json"  # Stores selected movies

def load_movies(filename):
    """Load movies from a specified JSON file"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_play_movies(movies):
    """Overwrite play.json with new selected movies"""
    with open(PLAY_FILE, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=4)

def update_play_json():
    """Randomly select 5 movies not already played and overwrite play.json"""
    all_movies = load_movies(MOVIE_FILE)  # Load all available movies
    played_movies = load_movies(PLAY_FILE)  # Load previously played movies

    # Filter out movies that have already been played
    available_movies = [movie for movie in all_movies if movie not in played_movies]

    # If there are not enough movies left, reset the cycle
    if len(available_movies) < 5:
        print("All movies have been played. Restarting the cycle.")
        available_movies = all_movies  # Reset to all movies

    # Randomly select 5 new movies
    selected_movies = random.sample(available_movies, 5)

    # Add "channel.mp4" before each movie
    final_playlist = []
    for movie in selected_movies:
        final_playlist.append({
            "image": "https://example.com/channel.jpg",
            "category": "Channel Intro",
            "title": "Channel Intro",
            "url": "channel.mp4"
        })
        final_playlist.append(movie)

    # Overwrite play.json with the new selection
    save_play_movies(final_playlist)
    print("Updated play.json with 5 new movies, each preceded by 'channel.mp4'.")

if __name__ == "__main__":
    update_play_json()
