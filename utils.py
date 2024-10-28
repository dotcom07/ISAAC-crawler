# utils.py

import os
import json
from urllib.parse import urlparse

def load_jsonl(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def normalize_url(url):
    parsed = urlparse(url)
    normalized = parsed._replace(fragment='').geturl().rstrip('/')
    return normalized