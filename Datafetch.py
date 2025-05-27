# Step 1: Script to Fetch Images and Metadata from Unsplash
# NOTE: You need to create an Unsplash developer account and get an API access key

import requests
import os
import json
from urllib.request import urlretrieve

# --- Configuration ---
ACCESS_KEY = 'HmkoipsbzjqX9KXdXTGZ1tioG9kLTtrW56q4hLiJCn8' 
# "sports","food","games","seasons","travel""technology"
# 
SEARCH_QUERIES = ["mountains","animals","cars","flowers","space","art"]
# SEARCH_QUERIES = []
PER_QUERY_IMAGE_COUNT = 150  # Total images = 5 queries * 300 = 1500 (around 2–3 GB)
SAVE_DIR = "downloaded_images"

# --- Ensure directory exists ---
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Metadata storage ---
all_metadata = []

def fetch_images(query, count):
    page = 1
    fetched = 0

    while fetched < count:
        print(f"Fetching page {page} for '{query}'...")
        url = f"https://api.unsplash.com/search/photos?page={page}&per_page=30&query={query}&client_id={ACCESS_KEY}"
        res = requests.get(url)
        data = res.json()

        if 'results' not in data:
            print("Error fetching data:", data)
            break

        for img in data['results']:
            img_url = img['urls']['regular']
            img_id = img['id']
            tags = [tag['title'] for tag in img.get('tags', [])]
            desc = img.get('description') or img.get('alt_description') or "No description"

            file_path = os.path.join(SAVE_DIR, f"{img_id}.jpg")
            try:
                urlretrieve(img_url, file_path)
                all_metadata.append({
                    "id": img_id,
                    "file_path": file_path,
                    "description": desc,
                    "tags": tags,
                    "category": query
                })
                fetched += 1
                if fetched >= count:
                    break
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")

        page += 1

# --- Main loop ---
for query in SEARCH_QUERIES:
    fetch_images(query, PER_QUERY_IMAGE_COUNT)

# --- Save metadata to a JSON file ---
with open("image_metadata.json", "w") as f:
    json.dump(all_metadata, f, indent=2)

print("Download complete. Metadata saved to 'image_metadata.json'")
