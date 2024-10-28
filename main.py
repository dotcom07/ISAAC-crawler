import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
import urllib3

from crawler import Crawler

# 로깅 설정
logger = logging.getLogger('CrawlerLogger')
logger.setLevel(logging.INFO)  # 로깅 레벨을 INFO로 변경하여 정보 메시지 표시

# RotatingFileHandler 설정 (5MB마다 로그 파일을 교체, 최대 5개 파일 유지, UTF-8 인코딩)
file_handler = RotatingFileHandler("crawler.log", maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# 콘솔 로그 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)

# HTTPS 경고 무시 (주의: 실제 환경에서는 권장하지 않음)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    parser = argparse.ArgumentParser(description="웹 크롤러")
    parser.add_argument('--start_url', type=str, default="https://www.yonsei.ac.kr/sc/admission/dep.jsp", help='시작할 URL')
    parser.add_argument('--max_depth', type=int, default=None, help='크롤링 최대 깊이 (없으면 무한대)')
    parser.add_argument('--fetch_threads', type=int, default=1, help='URL Fetch 스레드 수')
    parser.add_argument('--parse_threads', type=int, default=3, help='페이지 파싱 스레드 수')
    parser.add_argument('--save_interval', type=int, default=10, help='상태 저장 주기 (초)')
    args = parser.parse_args()

    start_url = args.start_url
    max_depth = args.max_depth
    fetch_threads = args.fetch_threads
    parse_threads = args.parse_threads
    save_interval = args.save_interval

    # 파일 경로 설정
    original_file = 'original_data.jsonl'  # 원본 데이터를 저장할 JSONL 파일
    state_file = 'crawler_state.json'

    # 크롤러 인스턴스 생성
    crawler = Crawler(
        start_url=start_url,
        max_depth=max_depth,
        fetch_threads=fetch_threads,
        parse_threads=parse_threads,
        save_interval=save_interval,
        user_agents=[
            # User-Agent 목록
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',

            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0',

            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',

            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.818.66 Safari/537.36 Edg/90.0.818.66',

            # 기타
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        ],
        original_file=original_file,
        state_file=state_file,
        logger=logger
    )

    # 크롤링 시작
    crawler.run()

if __name__ == "__main__":
    # Jupyter Notebook 환경에서 argparse 충돌 방지
    if 'ipykernel' in sys.modules:
        # Jupyter Notebook에서는 명령줄 인자를 무시하고 기본값을 사용
        sys.argv = [sys.argv[0]]
    main()