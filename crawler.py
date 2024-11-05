import threading
import time
import requests
import os
import json
from collections import deque
from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import re
from fetcher import Fetcher
from parser import Parser
from saver import Saver
from state_manager import StateManager
import logging

from utils import normalize_url, load_jsonl, extract_unique_identifier

class Crawler:
    def __init__(self, start_url, max_depth, fetch_threads, parse_threads, save_interval, user_agents,
                 original_file, state_file, logger):
        self.start_url = start_url
        self.max_depth = max_depth
        self.fetch_threads = fetch_threads
        self.parse_threads = parse_threads
        self.save_interval = save_interval
        self.user_agents = user_agents
        self.logger = logger

        # 시작 URL의 netloc을 추출하여 base_domain으로 설정
        parsed_start_url = urlparse(start_url)
        self.base_domain = parsed_start_url.netloc.lower()

        # 큐 및 집합 초기화
        self.fetch_queue = deque()
        self.fetch_queue_lock = threading.Lock()  # fetch_queue 접근을 위한 Lock
        self.parse_queue = deque()
        self.parse_queue_lock = threading.Lock()  # parse_queue 접근을 위한 Lock
        self.visited = set()
        self.visited_lock = threading.Lock()  # visited 접근을 위한 Lock
        self.parsed_set = set()
        self.parsed_set_lock = threading.Lock()  # parsed_set 접근을 위한 Lock

        # 중복된 merged_text를 추적하기 위한 집합과 락 추가
        self.seen_texts = set()
        self.seen_texts_lock = threading.Lock()

        # 링크 파일 설정 
        self.links_file = os.path.join('crawler_state', 'links.jsonl')
        self.links_lock = threading.Lock()  # 파일 쓰기 동기화를 위한 락

        # Fetcher 객체 초기화
        self.fetcher = Fetcher(self.user_agents, self.logger)

        # Parser 객체 초기화
        self.parser = Parser(self.base_domain, self.logger)

        # Saver 객체 초기화
        self.saver = Saver(original_file, self.logger)

        # StateManager 객체 초기화
        self.state_manager = StateManager(state_file, self.logger)

        # 상태 로드 (seen_texts 포함)
        state = self.state_manager.load_state(self.start_url)
        self.fetch_queue, self.parse_queue, self.visited, self.parsed_set, self.seen_texts, self.visited_identifiers = state

        self.stop_crawling_event = threading.Event()


        self.visited_identifiers = set()
        self.visited_identifiers_lock = threading.Lock()

        # 이미 제외된 URL을 저장하는 캐시 추가
        self.excluded_cache = set()

        # 제외할 경로 패턴 정의
        self.excluded_paths = [
            '/wj/',
            '/en_sc/',
            '/en_wj/',
            '/ocx/',
            '/ocx_en/',
            '/cn_wj/',
            '/wj',
            '/en_sc',
            '/en_wj/',
            '/ocx',
            '/ocx_en/',
            '/cn_wj'
        ]
        
        # 제외할 정확한 URL 정의
        self.excluded_urls = [
            'https://www.yonsei.ac.kr/sc/support/notice.jsp',
            'https://yonsei.ac.kr/sc/support/notice.jsp',
            'https://yicrc.yonsei.ac.kr/news.asp',
            'https://yicrc.yonsei.ac.kr/program.asp',
            'https://yicrc.yonsei.ac.kr/newsletter.asp',
            'https://yicrc.yonsei.ac.kr/rc.asp',
            'https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_02',
            'https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_05',
            'https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_03',
            'https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_04',
            'https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_07',
            'https://dorm.yonsei.ac.kr/en',
            'https://computing.yonsei.ac.kr/eng',
            'https://library.yonsei.ac.kr/en',
            'https://library.yonsei.ac.kr/SSOLegacy.do',
            'https://library.yonsei.ac.kr/login',
            'https://yonsei.ac.kr/sc/intro/promotionvideo.jsp',
            'https://yonsei.ac.kr/sc/intro/promotionvideo-for-sns.jsp',
            'https://yonsei.ac.kr/sc/intro/pressrel.jsp',
            'https://yonsei.ac.kr/sc/intro/media1.jsp',
            'https://oia.yonsei.ac.kr/intro/photo.asp',
            'https://oia.yonsei.ac.kr/upload_file/',
            'https://yicrc.yonsei.ac.kr/main/downloadfile.asp?',
            'https://yonsei.ac.kr/sc/support/scholarship.jsp',
            'https://yonsei.ac.kr/sc/support/lost_found.jsp',
            'https://yonsei.ac.kr/sc/campus/yonseibean.jsp',
            'https://yonsei.ac.kr/sc/intro/sympathy.jsp',
            'https://yicdorm.yonsei.ac.kr/downloadfile.asp',
            'https://yicdorm.yonsei.ac.kr/board.asp?act=view&bid=2',
            'https://yicdorm.yonsei.ac.kr/board.asp?act=view&bid=3',
            'https://yicdorm.yonsei.ac.kr/board.asp?act=view&bid=4',
            'https://yicdorm.yonsei.ac.kr/board.asp?act=view&bid=5',
            'https://yicdorm.yonsei.ac.kr/board.asp?act=view&bid=7'
        ]


    def is_excluded(self, url):
        """
        URL이 제외 패턴에 맞는지 확인하는 메서드
        """
        parsed = urlparse(url)
        
        # 정확히 제외할 URL인지 확인 (접두사 일치 확인)
        for excluded_url in self.excluded_urls:
            if url.startswith(excluded_url):
                return True
        
        # 제외할 경로 패턴인지 확인
        for path in self.excluded_paths:
            if parsed.path.startswith(path):
                return True
        
        # 쿼리 문자열에 'mid=n' 포함 여부 확인
        query_params = parse_qs(parsed.query)
        if 'mid' in query_params and query_params['mid'][0].startswith('n'):
            return True

        return False

    def add_url_to_queue(self, url, depth):
        normalized_url = normalize_url(url)
        
        # URL이 절대 경로인지 확인
        parsed_url = urlparse(normalized_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            self.logger.warning(f"절대 경로가 아닌 URL을 건너뜁니다: {normalized_url}")
            return  # 절대 경로가 아니면 추가하지 않음
        
        unique_id = extract_unique_identifier(normalized_url)
        
        with self.visited_identifiers_lock:
            if unique_id in self.visited_identifiers:
                self.logger.debug(f"제외하거나 처리된 콘텐츠입니다: {unique_id}")
                return  # 이미 처리된 콘텐츠이므로 추가하지 않음
            else:
                self.visited_identifiers.add(unique_id)
        
        with self.visited_lock:
            if normalized_url not in self.visited and normalized_url not in self.parsed_set:
                if self.max_depth is None or depth <= self.max_depth:
                    # 캐시 확인: 이미 제외된 URL인지 확인
                    if normalized_url in self.excluded_cache or self.is_excluded(normalized_url):
                        self.excluded_cache.add(normalized_url)  # 제외된 URL 캐시에 추가
                        return  # 제외된 URL이므로 큐에 추가하지 않음

                    # 중복이 아니면 fetch_queue에 추가
                    with self.fetch_queue_lock:
                        self.fetch_queue.append((normalized_url, depth))
                        self.logger.debug(f"URL 큐에 추가됨: {normalized_url} (Depth: {depth})")
                    self.visited.add(normalized_url)
                    
                    # links.jsonl에 추가
                    summarized_link = {
                        "url": normalized_url,
                        "depth": depth
                    }
                    with self.links_lock:
                        try:
                            with open(self.links_file, 'a', encoding='utf-8') as f_links:
                                json.dump(summarized_link, f_links, ensure_ascii=False)
                                f_links.write('\n')
                        except Exception as e:
                            self.logger.error(f"links.jsonl에 URL 저장 실패: {e}")


    def load_additional_links(self, links_file):
        """links.jsonl에서 URL을 큐에 추가"""
        if os.path.exists(links_file):
            self.logger.info("links.jsonl에서 추가 URL을 큐에 추가 중...")
            links = load_jsonl(links_file)
            added_count = 0
            for entry in links:
                url = normalize_url(entry.get('url', ''))
                depth = entry.get('depth', 0)
                with self.visited_lock:
                    if url and url not in self.visited and url not in self.parsed_set:
                        if self.max_depth is None or depth <= self.max_depth:
                            with self.fetch_queue_lock:
                                self.fetch_queue.append((url, depth))
                                self.logger.debug(f"URL 큐에 추가됨: {url} (Depth: {depth})")  # 추가된 로그
                            self.visited.add(url)
                            added_count += 1
            self.logger.info(f"links.jsonl에서 {added_count}개의 URL을 큐에 추가했습니다.")
            # 링크를 로드한 후 links.jsonl 파일을 비워서 중복 로딩 방지
            with open(links_file, 'w', encoding='utf-8') as f_links:
                pass

    def start_threads(self):
        """각 스레드 그룹 시작"""
        # Fetcher 스레드 시작
        self.fetch_threads_list = []
        for i in range(self.fetch_threads):
            t = threading.Thread(target=self.fetch_worker, name=f"Fetcher-{i+1}")
            t.start()
            self.logger.info(f"{t.name} 시작")
            self.fetch_threads_list.append(t)

        # Parser 스레드 시작
        self.parse_threads_list = []
        for i in range(self.parse_threads):
            t = threading.Thread(target=self.parse_worker, name=f"Parser-{i+1}")
            t.start()
            self.logger.info(f"{t.name} 시작")
            self.parse_threads_list.append(t)

        # 상태 저장 스레드 시작
        self.state_thread = threading.Thread(target=self.periodic_state_save, name="StateSaver")
        self.state_thread.start()
        self.logger.info(f"{self.state_thread.name} 시작")

    def fetch_worker(self):
        thread_name = threading.current_thread().name
        with requests.Session() as session:
            # Session의 내부 재시도 비활성화
            retry_strategy = Retry(total=0)
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            while not self.stop_crawling_event.is_set():
                with self.fetch_queue_lock:
                    if self.fetch_queue:
                        url, depth = self.fetch_queue.popleft()
                    else:
                        url, depth = None, None

                if url is None:
                    self.stop_crawling_event.wait(timeout=0.3) # 큐가 비어있으면 잠시 대기
                    continue

                content = self.fetcher.fetch_page_content(session, url)
                if content:
                    # Parse 큐에 추가
                    with self.parse_queue_lock:
                        self.parse_queue.append((url, content, depth))
                else:
                    # 크롤링 실패 시 로깅
                    self.logger.warning(f"[{thread_name}] 크롤링 실패: {url}")

    def normalize_text(self, text):
        # 모든 공백을 단일 공백으로 변환하고 양쪽 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        # 소문자 변환
        text = text.lower()
        # 불필요한 특수 문자 제거 (필요에 따라 조정)
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def parse_worker(self):
        thread_name = threading.current_thread().name
        while not self.stop_crawling_event.is_set():
            with self.parse_queue_lock:
                if self.parse_queue:
                    url, content, depth = self.parse_queue.popleft()
                else:
                    url, content, depth = None, None, None

            if url is None:
                time.sleep(1)
                continue

            try:
                merged_text = self.parser.extract_and_merge_text(content, url)
            except Exception as e:
                self.logger.error(f"[{thread_name}] 텍스트 추출 오류 ({url}): {e}")
                merged_text = ""

            # merged_text가 비어있으면 저장하지 않음
            if not merged_text.strip():
                self.logger.info(f"[{thread_name}] 빈 merged_text로 인해 저장을 건너뜁니다: {url}")
                continue

            # merged_text 정규화
            normalized_text = self.normalize_text(merged_text)

            # 정규화된 텍스트가 비어있으면 저장하지 않음
            if not normalized_text:
                self.logger.info(f"[{thread_name}] 정규화 후 빈 텍스트로 인해 저장을 건너뜁니다: {url}")
                continue

            # merged_text의 해시값 생성 (SHA-256 사용)
            text_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

            # 중복 체크
            with self.seen_texts_lock:
                if text_hash in self.seen_texts:
                    self.logger.info(f"[{thread_name}] 중복된 merged_text를 발견하여 저장을 건너뜁니다: {url}")
                    continue  # 중복되면 저장하지 않고 건너뜀
                self.seen_texts.add(text_hash)  # 중복되지 않으면 해시값을 추가

            soup = BeautifulSoup(content, 'html.parser')

            # 이미지, 파일, 테이블 추출
            images = self.parser.extract_image_links(soup, url)
            files = self.parser.extract_file_links(soup, url)
            tables = self.parser.extract_tables(soup, url)

            # 원본 데이터 저장 (merged_text, images, files, tables)
            original_data = {
                "url": url,
                "merged_text": merged_text,
                "images": images,
                "files": files,
                "tables": tables
            }
            self.saver.save_original_data(original_data)
            self.logger.info(f"[{thread_name}] 원본 데이터 저장 완료: {url}")

            # 파싱된 URL 집합에 추가
            with self.parsed_set_lock:
                self.parsed_set.add(url)

            # 하위 링크 추출
            links = self.parser.extract_links(content, url)
            for link in links:
                self.add_url_to_queue(link, depth + 1)  # 중복 체크하며 큐에 추가

    def periodic_state_save(self):
        thread_name = threading.current_thread().name
        while not self.stop_crawling_event.is_set():
            with self.parse_queue_lock:  # parse_queue를 안전하게 잠그고 복사본 생성
                parse_queue_copy = list(self.parse_queue)

            self.state_manager.save_state(
                self.fetch_queue, 
                parse_queue_copy,  # 복사본 사용
                self.visited, 
                self.parsed_set,
                self.seen_texts,
                self.visited_identifiers
            )
            self.logger.info(f"[{thread_name}] 상태 저장 완료.")
            # 파일 크기 확인 및 로테이션
            self.saver.check_file_size_and_rotate(self.saver.original_file)
            time.sleep(self.save_interval)
        # 크롤링이 완료되면 최종 저장
        self.state_manager.save_state(
            self.fetch_queue, 
            parse_queue_copy,  # 복사본 사용
            self.visited, 
            self.parsed_set,
            self.seen_texts,
            self.visited_identifiers
        )
        self.logger.info(f"[{thread_name}] 최종 상태 저장 완료.")


    def run(self):
        # 시작 URL을 큐에 추가
        self.add_url_to_queue(self.start_url, 0)

        # 스레드 시작
        self.start_threads()

        # 원본 파일 미리 생성
        if not os.path.exists(self.saver.original_file):
            with open(self.saver.original_file, 'w', encoding='utf-8') as f:
                pass  # 빈 파일 생성
            self.logger.info(f"파일 생성됨: {self.saver.original_file}")

        # 링크 파일에서 추가 링크를 로드
        self.load_additional_links('links.jsonl')

        # 크롤링 완료를 판단하기 위한 타이머 설정
        idle_time = 0
        idle_threshold = 120  # 크롤링이 idle 상태로 120초 이상 유지되면 종료

        try:
            while not self.stop_crawling_event.is_set():
                # 작업 진행 중인지 확인
                with self.fetch_queue_lock, self.parse_queue_lock:
                    if not self.fetch_queue and not self.parse_queue:
                        idle_time += 1
                        if idle_time >= idle_threshold:
                            self.logger.info("큐가 비어있고 일정 시간 동안 추가 작업이 없어 크롤링을 종료합니다.")
                            self.stop_crawling_event.set()
                            break
                    else:
                        idle_time = 0  # 큐에 작업이 있으면 idle_time 초기화
                        self.logger.debug("큐에 작업이 존재하여 idle_time 초기화.")
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("사용자에 의해 크롤링이 중단되었습니다.")
            self.stop_crawling_event.set()
        finally:
            # 크롤링 중단 신호 전송
            self.stop_crawling_event.set()

            # 모든 스레드가 작업을 완료할 때까지 대기
            for t in self.fetch_threads_list + self.parse_threads_list:
                t.join()

            # 상태 저장 스레드 종료
            self.state_thread.join()

            # 남아있는 데이터를 최종 저장
            self.saver.final_save()

            # 상태 저장 (seen_texts 포함)
            self.state_manager.save_state(self.fetch_queue, self.parse_queue, self.visited, self.parsed_set, self.seen_texts, self.visited_identifiers)

            self.logger.info("크롤링 및 파싱 작업이 종료되었습니다.")
