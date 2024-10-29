# announcement_parser.py

from parser import Parser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logging

class AnnouncementParser(Parser):
    def __init__(self, base_domain, logger):
        super().__init__(base_domain, logger)
    
    def parse_notice(self, soup, url):
        """
        기존 Parser의 parse_notice 메서드를 오버라이딩하여 
        merged_text 형식으로 데이터를 구성합니다.
        """
        merged_text = []
        images = []
        files = []
        tables = []

        # 제목, 날짜, 카테고리 추출
        title = soup.select_one("dl.board_view dt strong").get_text(strip=True)
        date = soup.select_one(".date").get_text(strip=True)
        category = soup.select_one(".title_area .title").get_text(strip=True)

        # merged_text 구성: "[카테고리] 제목 날짜"
        merged_text.append(f"category: [{category}] title: '{title}' date: {date} \n")

        # 본문 텍스트, 이미지, 테이블 추출
        content_elements = soup.select(".fr-view > *")
        for element in content_elements:
            if element.name in ['p', 'div']:
                # 이미지 추출
                img_elements = element.find_all('img')
                for img in img_elements:
                    img_url = img.get('src')
                    if img_url and not img_url.startswith("http"):
                        img_url = urljoin(self.base_domain, img_url)
                    if img_url:
                        images.append(img_url)
                # 텍스트 추가
                text_content = element.get_text(strip=True)
                if text_content:
                    merged_text.append(text_content)
            elif element.name == 'table':
                # 테이블 파싱
                table_object = self.parse_table(element, self.base_domain)
                tables.append(table_object)
            elif element.name == 'img':
                img_url = element.get('src')
                if img_url and not img_url.startswith("http"):
                    img_url = urljoin(self.base_domain, img_url)
                if img_url:
                    images.append(img_url)

        # 파일 링크 추출
        extracted_files = self.extract_file_links(soup, self.base_domain)
        files.extend(extracted_files)

        # merged_text 문자열로 결합
        merged_text_str = " - ".join(merged_text)

        # JSON 객체 생성
        json_object = {
            "url": url,
            "merged_text": merged_text_str,
            "images": images,
            "files": files,
            "tables": tables
        }

        return json_object
