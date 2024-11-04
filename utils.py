# utils.py

import os
import json
from urllib.parse import urlparse, urlunparse, parse_qsl

def load_jsonl(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def normalize_url(url):
    parsed = urlparse(url)
    
    # 스킴을 'https'로 통일
    scheme = 'https'
    
    # netloc을 소문자로 변환 및 'www.' 제거
    netloc = parsed.netloc.lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    # 경로의 끝 슬래시 제거
    path = parsed.path.rstrip('/')
    
    # 쿼리 파라미터 정렬
    query = '&'.join(['{}={}'.format(k, v) for k, v in sorted(parse_qsl(parsed.query))])
    
    # 프래그먼트 제거 (빈 문자열로 설정)
    fragment = ''
    
    # 정규화된 URL 재구성
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
    
    return normalized
