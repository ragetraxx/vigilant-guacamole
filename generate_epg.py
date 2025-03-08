import json
import datetime
import os

# Check if current_movie.json exists and is not empty
if not os.path.exists("current_movie.json") or os.stat("current_movie.json").st_size == 0:
    print("Error: No current movie found. Run stream.py first.")
    exit(1)

# Load the currently streaming movie
try:
    with open("current_movie.json", "r") as file:
        movie = json.load(file)
except json.JSONDecodeError:
    print("Error: current_movie.json is corrupted or empty.")
    exit(1)

# Get movie details
title = movie.get("title", "Unknown Movie")
url = movie.get("url", "")
category = movie.get("category", "General")
image = movie.get("image", "")

# Define start time (current UTC) and duration (2 hours)
start_time = datetime.datetime.utcnow()
end_time = start_time + datetime.timedelta(hours=2)

# Format times in EPG format
start_str = start_time.strftime("%Y%m%d%H%M%S +0000")
end_str = end_time.strftime("%Y%m%d%H%M%S +0000")

# Create XML structure
epg = f'''<?xml version="1.0" encoding="UTF-8"?>
<tv>
    <channel id="RageTV">
        <display-name>RageTV</display-name>
    </channel>
    <programme start="{start_str}" stop="{end_str}" channel="RageTV">
        <title lang="en">{title}</title>
        <desc>Streaming on RageTV</desc>
        <category>{category}</category>
        <icon src="{image}" />
        <url>{url}</url>
    </programme>
</tv>
'''

# Save to epg.xml
with open("epg.xml", "w") as file:
    file.write(epg)

print("EPG updated: epg.xml")
