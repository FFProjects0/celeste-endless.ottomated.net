#!/usr/bin/env python3
import os
import json
import re
import requests
import logging
from pathlib import Path

# Set up logging for detailed debugging.
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

API_RANDOM_URL = 'https://celeste-endless.ottomated.net/api/random'

def sanitize_filename(name):
    """Return a safe filename by removing illegal characters."""
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    logging.debug("Sanitized filename: '%s' -> '%s'", name, safe_name)
    return safe_name

def download_image(image_url, dest_path):
    """Download an image and save it to dest_path."""
    try:
        logging.debug("Downloading image from URL: %s", image_url)
        response = requests.get(image_url)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
            f.flush()  # Force flush to disk
        logging.info("Downloaded image to %s", dest_path)
    except requests.RequestException as e:
        logging.error("Failed to download image from %s. Error: %s", image_url, e)

def load_maps_json(json_path='Maps.json'):
    """Load Maps.json if it exists; otherwise return a new dict."""
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.debug("Loaded existing Maps.json with content: %s", data)
                return data
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from %s: %s", json_path, e)
            return {"Maps": {}}
    else:
        logging.debug("Maps.json not found. Initializing new JSON structure.")
        return {"Maps": {}}

def save_maps_json(data, json_path='Maps.json'):
    """Save maps data to the JSON file with flush."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    logging.info("Maps data saved to %s", json_path)

def get_random_map():
    """Fetch a random map from the API and return its JSON data."""
    try:
        logging.debug("Requesting random map from API: %s", API_RANDOM_URL)
        response = requests.get(API_RANDOM_URL)
        response.raise_for_status()
        map_data = response.json()
        logging.debug("Received random map data: %s", map_data)
        return map_data
    except requests.RequestException as e:
        logging.error("Error fetching random map: %s", e)
        return None

def main():
    # Log current working directory so you know where the file is being written.
    cwd = os.getcwd()
    logging.debug("Current working directory: %s", cwd)
    
    # Ensure the images folder exists.
    images_folder = Path("./images")
    images_folder.mkdir(exist_ok=True)
    
    # Load the existing maps from JSON.
    maps_data = load_maps_json()

    # Log current JSON content before processing.
    logging.debug("JSON content before processing: %s", maps_data)
    
    # Set the number of random maps to attempt to add.
    number_of_maps = 500

    for i in range(number_of_maps):
        logging.info("Fetching random map #%d", i + 1)
        map_entry = get_random_map()
        if not map_entry:
            logging.warning("No map data received on iteration #%d", i + 1)
            continue

        title = map_entry.get('name')
        if not title:
            logging.warning("Map data without a title received. Skipping iteration #%d", i + 1)
            continue

        logging.debug("Random map title received: '%s'", title)
        
        # Duplicate-check: normalize title.
        normalized_title = title.strip().lower()
        duplicate_found = False
        for existing_title in maps_data["Maps"]:
            if existing_title.strip().lower() == normalized_title:
                duplicate_found = True
                logging.info("Map '%s' already exists. Skipping.", title)
                break
        if duplicate_found:
            continue

        # Process fields.
        creators = map_entry.get('authors')
        if isinstance(creators, list):
            creators = ", ".join(creators)
        link = map_entry.get('url')
        thumbnail = map_entry.get('thumbnail')

        safe_title = sanitize_filename(title)
        image_path = images_folder / f"{safe_title}.jpg"
        if thumbnail:
            download_image(thumbnail, image_path)
        else:
            logging.warning("No thumbnail provided for map '%s'.", title)

        # Add new map entry.
        maps_data["Maps"][title] = {
            "title": title,
            "creator": creators,
            "image": str(image_path),
            "link": link
        }
        logging.info("Added new map: %s", title)

        # Save updated JSON data.
        save_maps_json(maps_data)
        with open('Maps.json', 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        logging.debug("Final JSON contents: %s", final_data)
        print("JSON file updated:", final_data)

if __name__ == '__main__':
    main()
