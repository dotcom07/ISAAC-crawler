# announcement_crawler.py

import time
import os
from bs4 import BeautifulSoup
from crawler import Crawler
from urllib.parse import urljoin
from announcement_crawler.json_manager import JsonManager
from announcement_crawler.announcement_parser import AnnouncementParser
from announcement_crawler.json_manager import JsonManager
from fetcher import Fetcher
import requests

class AnnouncementCrawler(Crawler):
    def __init__(self, start_url, logger):
        super().__init__(
            start_url=start_url,
            max_depth=None,  # 필요에 따라 설정
            fetch_threads=5,
            parse_threads=5,
            save_interval=60,
            user_agents=["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"],
            original_file="original_data.jsonl",
            state_file="state.json",
            logger=logger
        )
        self.base_url = "https://www.yonsei.ac.kr/sc/support/notice.jsp"
        self.last_article_no = None
        self.last_page_url = None
        self.new_post_exists = False
        self.parser = AnnouncementParser(self.base_url, logger)  # AnnouncementParser 사용
        self.fetcher = Fetcher(self.user_agents, self.logger)

    def start_crawling_with_interval(self):
        try:
            self.crawl_notices(self.start_url)
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")

    def crawl_notices(self, start_url):
        url = start_url
        with requests.Session() as session:  # 세션 생성
            while url:
                self.logger.info(f"Crawling notice at: {url}")
                content = self.fetcher.fetch_page_content(session, url)  # session과 url 모두 전달
                if not content:
                    self.logger.warning(f"Failed to fetch content from: {url}")
                    break

                soup = BeautifulSoup(content, 'html.parser')
                notice_date = soup.select_one(".date").get_text(strip=True)
                parsed_date = time.strptime(notice_date, "%Y.%m.%d")
                notice_year = parsed_date.tm_year

                # AnnouncementParser를 사용하여 JSON 데이터 생성
                json_data = self.parser.parse_notice(soup, url)
                file_path = os.path.join('notices', f'notices_{notice_year}.jsonl')
                JsonManager.save_to_jsonl(json_data, file_path)

                self.last_article_no = self.get_article_no_from_url(url)
                self.last_page_url = url
                self.logger.info(f"Last crawled article_no: {self.last_article_no} (URL: {url})")

                url = self.get_next_notice_url(soup)

                if not url:
                    self.logger.info(f"No more notices to crawl for year {notice_year}. Checking for new posts...")
                    while not self.new_post_exists:
                        self.logger.info("Waiting for a new post...")
                        time.sleep(60)  # 1분 대기
                        content = self.fetcher.fetch_page_content(session, self.last_page_url)  # session과 url 모두 전달
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            url = self.get_next_notice_url(soup)
                            if url and self.is_new_post(url, self.last_article_no):
                                self.logger.info("New post found! Resuming crawl...")
                                self.new_post_exists = True
                                break
                        else:
                            self.logger.warning(f"Failed to fetch content from: {self.last_page_url}")
                    self.new_post_exists = False
        self.logger.info("Crawling completed.")

    def get_next_notice_url(self, soup):
        next_notice_link = soup.select_one("#jwxe_main_content > div.jwxe_board > div > ul > li:nth-child(1) > a")
        if next_notice_link:
            relative_url = next_notice_link.get('href')
            if "javascript" not in relative_url:
                # Java 코드에서는 base_url + relative_url의 query 부분을 사용
                # Python에서는 urljoin을 사용하여 절대 URL을 생성
                return urljoin(self.base_url, relative_url)
        return None

    def get_article_no_from_url(self, url):
        # URL에서 article_no 추출
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
