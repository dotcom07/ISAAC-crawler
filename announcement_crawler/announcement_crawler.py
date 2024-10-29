# announcement_crawler.py

import json
import time
from bs4 import BeautifulSoup
from crawler import Crawler
from urllib.parse import urljoin
from announcement_crawler.json_manager import JsonManager
from announcement_crawler.announcement_parser import AnnouncementParser
from fetcher import Fetcher
import requests
import os

class AnnouncementCrawler(Crawler):
    def __init__(self, start_url, logger):
        super().__init__(
            start_url=start_url,
            max_depth=None,
            fetch_threads=5,
            parse_threads=5,
            save_interval=60,
            user_agents=["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"],
            original_file= os.path.join('original_data', "original_data.jsonl"),
            state_file= os.path.join('crawler_state', 'state.json'),
            logger=logger
        )
        self.base_url = "https://www.yonsei.ac.kr/sc/support/notice.jsp"
        self.last_article_no = None
        self.last_page_url = None
        self.new_post_exists = False
        self.parser = AnnouncementParser(self.base_url, logger)
        self.fetcher = Fetcher(self.user_agents, self.logger)
        self.state_file = os.path.join('crawler_state', 'announcement_state.json')
        
        # 마지막 크롤링 상태 로드
        if self.load_last_state():
            # 이전 상태가 있다면 바로 대기 모드로 진입
            self.start_waiting_for_new_posts()
        else:
            self.logger.info("No previous state found, starting full crawl.")
            self.start_crawling_with_interval()

    def load_last_state(self):
        # 마지막 공지사항 상태 로드
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as file:
                state = json.load(file)
                self.last_article_no = state.get("last_article_no")
                self.last_page_url = state.get("last_page_url")
                self.logger.info(f"Loaded last article: {self.last_article_no}")
            return True  # 이전 상태가 있음을 표시
        return False  # 이전 상태가 없음

    def save_last_state(self, url, article_no):
        # 마지막 공지사항 상태 저장
        state = {
            "last_article_no": article_no,
            "last_page_url": url
        }
        with open(self.state_file, 'w') as file:
            json.dump(state, file)
        self.logger.info(f"Saved last article: {article_no} (URL: {url})")

    def start_crawling_with_interval(self):
        try:
            self.crawl_notices(self.start_url)
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")

    def crawl_notices(self, start_url):
        url = start_url
        with requests.Session() as session:
            while url:
                self.logger.info(f"Crawling notice at: {url}")
                content = self.fetcher.fetch_page_content(session, url)
                if not content:
                    self.logger.warning(f"Failed to fetch content from: {url}")
                    break

                soup = BeautifulSoup(content, 'html.parser')
                notice_date = soup.select_one(".date").get_text(strip=True)
                parsed_date = time.strptime(notice_date, "%Y.%m.%d")
                notice_year = parsed_date.tm_year

                # JSON 데이터 생성
                json_data = self.parser.parse_notice(soup, url)
                article_no = self.get_article_no_from_url(url)
                file_path = os.path.join('notices', f'notices_{notice_year}.jsonl')
                JsonManager.save_to_jsonl(json_data, file_path)

                # 마지막으로 크롤링한 공지 저장
                self.save_last_state(url, article_no)
                self.logger.info(f"Last crawled article_no: {article_no} (URL: {url})")

                url = self.get_next_notice_url(soup)

                if not url:
                    self.start_waiting_for_new_posts()
                    break  # 대기 모드로 진입 후 크롤링 루프 종료

    def start_waiting_for_new_posts(self):
        """이전 상태에서 이어서 새로운 공지를 기다리는 모드"""
        with requests.Session() as session:
            while True:
                self.logger.info("Waiting for a new post...")
                time.sleep(60)  # 1분 대기
                check_url = self.last_page_url if self.last_page_url else self.start_url
                content = self.fetcher.fetch_page_content(session, check_url)
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    url = self.get_next_notice_url(soup)
                    if url and self.is_new_post(url, self.last_article_no):
                        self.logger.info("New post found! Resuming crawl...")
                        self.crawl_notices(url)
                        break
                else:
                    self.logger.warning(f"Failed to fetch content from: {check_url}")

    def get_next_notice_url(self, soup):
        next_notice_link = soup.select_one("#jwxe_main_content > div.jwxe_board > div > ul > li:nth-child(1) > a")
        if next_notice_link:
            relative_url = next_notice_link.get('href')
            if "javascript" not in relative_url:
                return urljoin(self.base_url, relative_url)
        return None

    def get_article_no_from_url(self, url):
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        return query.get('article_no', [None])[0]

    def is_new_post(self, url, last_article_no):
        current_article_no = self.get_article_no_from_url(url)
        if current_article_no and last_article_no:
            try:
                return int(current_article_no) > int(last_article_no)
            except ValueError:
                self.logger.error(f"Invalid article numbers: current={current_article_no}, last={last_article_no}")
        return False
