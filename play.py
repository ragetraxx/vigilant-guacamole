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
    """Save selected movies to play.json"""
    with open(PLAY_FILE, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=4)

def update_play_json():
    """Randomly select 5 movies not in play.json and update play.json"""
    all_movies = load_movies(MOVIE_FILE)  # All available movies
    played_movies = load_movies(PLAY_FILE)  # Already played movies

    # Filter out played movies
    available_movies = [movie for movie in all_movies if movie not in played_movies]

    # If all movies have been played, reset play.json (Optional)
    if len(available_movies) < 5:
        print("All movies have been played. Resetting play.json.")
        save_play_movies([])  # Reset the file
        available_movies = all_movies  # Refill from original movies.json

    # Randomly pick 5 movies from the available ones
    selected_movies = random.sample(available_movies, 5)
    
    # Save to play.json
    save_play_movies(played_movies + selected_movies)
    print("Updated play.json with 5 new movies.")

if __name__ == "__main__":
    update_play_json()
