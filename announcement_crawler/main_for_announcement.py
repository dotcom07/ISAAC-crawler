# main_for_announcement.py

import logging
from announcement_crawler.announcement_crawler import AnnouncementCrawler
from announcement_crawler.announcement_parser import AnnouncementParser
from announcement_crawler.json_manager import JsonManager
def setup_logger():
    logger = logging.getLogger("AnnouncementCrawler")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main():
    logger = setup_logger()
    start_url = "https://www.yonsei.ac.kr/sc/support/notice.jsp?mode=view&article_no=178628&board_wrapper=%2Fsc%2Fsupport%2Fnotice.jsp&pager.offset=1400&board_no=15"
    crawler = AnnouncementCrawler(start_url, logger)
    crawler.start_crawling_with_interval()

if __name__ == "__main__":
    main()
