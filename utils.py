# utils.py

import os
import json
from urllib.parse import urlparse, urlunparse, parse_qsl
import logging

def load_jsonl(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

from urllib.parse import urlparse, urlunparse, parse_qsl

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
    
    # 쿼리 파라미터 파싱
    query_params = parse_qsl(parsed.query)
    
    # 제거할 매개변수 목록 (필요에 따라 더 추가)
    params_to_remove = ['ddx', 'hID', 'sdx', 'SFIELD', 'XT', 'lang']
    
    # 제거할 매개변수를 제외한 새로운 쿼리 파라미터 목록 생성
    filtered_params = [(k, v) for k, v in query_params if k not in params_to_remove]
    
    # 쿼리 파라미터 정렬
    filtered_params.sort()
    
    # 정규화된 쿼리 문자열 재구성
    query = '&'.join(['{}={}'.format(k, v) for k, v in filtered_params])
    
    # 프래그먼트 제거 (빈 문자열로 설정)
    fragment = ''
    
    # 정규화된 URL 재구성
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
    logging.debug(f"normalize_url - 입력: {url}, 출력: {normalized}")
    return normalized


def extract_unique_identifier(url):
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query))
    
    # 우선순위에 따라 고유 식별자를 추출
    for key in ['bidx', 'article_no', 'idx']:
        if key in query_params:
            return f"{parsed.netloc}{parsed.path}?{key}={query_params[key]}"
    
    # 식별자가 없으면 URL 전체를 사용
    return normalize_url(url)