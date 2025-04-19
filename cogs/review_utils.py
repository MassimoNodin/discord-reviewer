import re
import json
import os

DATA_FILE = 'reviews.json'

def is_valid_url(url):
    url_regex = re.compile(
        r'^(https?://)'
        r'([A-Za-z0-9-]+\.)+[A-Za-z]{2,63}'
        r'(/[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*)?'
        r'$'
    )
    if not isinstance(url, str) or len(url) > 2048:
        return False
    if not url_regex.match(url):
        return False
    return True

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        print("Error: Could not save data to reviews.json")

async def setup(bot):
    pass
