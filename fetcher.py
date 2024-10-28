# fetcher.py

import requests
import random
import time
import urllib3
from urllib.parse import urlparse, urljoin
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class Fetcher:
    def __init__(self, user_agents, logger):
        self.USER_AGENTS = user_agents
        self.logger = logger

    def fetch_page_content(self, session, url, retries=10, backoff_factor=2, max_backoff=100, initial_timeout=30, max_total_timeout=200):
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS)
        }
        attempt = 0
        backoff = backoff_factor  # 초기 대기 시간 (초)
        timeout = initial_timeout  # 타임아웃 시간
        total_time_spent = 0  # 총 소요 시간

        while attempt < retries and total_time_spent < max_total_timeout:
            try:
                start_time = time.time()
                response = session.get(url, headers=headers, verify=False, allow_redirects=True, timeout=timeout)
                elapsed_time = time.time() - start_time
                total_time_spent += elapsed_time
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'text/html' in content_type:
                        time.sleep(random.uniform(0.1, 0.5))  # 짧은 지연 시간 추가
                        return response.content
                    else:
                        self.logger.warning(f"비HTML 컨텐츠 ({content_type}) for URL: {url}. 스킵합니다.")
                        return None
                elif 500 <= response.status_code < 600:
                    # 서버 오류 시 재시도
                    attempt += 1
                    self.logger.warning(f"서버 오류 {response.status_code} for URL: {url}. 재시도 중... (Attempt {attempt}/{retries})")
                    if attempt >= retries:
                        break
                    time.sleep(backoff)
                    backoff = min(backoff * 2, max_backoff)  # 지수 백오프 적용
                else:
                    # 클라이언트 오류: 로깅 후 재시도하지 않음
                    self.logger.error(f"클라이언트 오류 {response.status_code} for URL: {url}. 재시도하지 않음.")
                    break
            except requests.exceptions.Timeout as e:
                # 타임아웃 예외 처리
                attempt += 1
                elapsed_time = time.time() - start_time
                total_time_spent += elapsed_time
                self.logger.warning(f"타임아웃 발생 (Attempt {attempt}/{retries}): {url} - {e}")
                if attempt >= retries or total_time_spent >= max_total_timeout:
                    break
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
            except requests.exceptions.RequestException as e:
                # 기타 예외 처리
                attempt += 1
                elapsed_time = time.time() - start_time
                total_time_spent += elapsed_time
                self.logger.warning(f"URL 요청 실패 (Attempt {attempt}/{retries}): {url} - {e}")
                if attempt >= retries or total_time_spent >= max_total_timeout:
                    break
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
        self.logger.error(f"{retries}번의 시도 또는 최대 대기 시간 {max_total_timeout}초 후에도 가져오지 못함: {url}")
        return None

