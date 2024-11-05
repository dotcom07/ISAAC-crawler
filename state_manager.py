import os
import threading
import json
import base64
from collections import deque
import logging
import shutil

class StateManager:
    def __init__(self, state_file, logger):
        self.state_file = state_file
        self.logger = logger
        self.lock = threading.Lock()

    def save_state(self, fetch_queue, parse_queue, visited, parsed_set, seen_texts, visited_identifiers):
        with self.lock:
            state = {
                'fetching_queue': list(fetch_queue),
                'parsing_queue': [
                    [url, base64.b64encode(content).decode('utf-8'), depth] 
                    for (url, content, depth) in parse_queue
                ],
                'visited': list(visited),
                'parsed': list(parsed_set),
                'seen_texts': list(seen_texts),
                'visited_identifiers': list(visited_identifiers)  # visited_identifiers 추가
            }
            temp_state_file = self.state_file + '.tmp'
            try:
                with open(temp_state_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False, indent=4)
                # 원자적 파일 교체
                shutil.move(temp_state_file, self.state_file)
                self.logger.info("상태 저장 완료.")
            except Exception as e:
                self.logger.error(f"상태 저장 실패: {e}")
                if os.path.exists(temp_state_file):
                    os.remove(temp_state_file)

    def load_state(self, start_url):
        if os.path.exists(self.state_file):
            self.logger.info("기존 상태를 불러오는 중...")
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    fetch_queue = deque(state.get('fetching_queue', []))
                    parse_queue = deque([
                        (url, base64.b64decode(content.encode('utf-8')), depth) 
                        for (url, content, depth) in state.get('parsing_queue', [])
                    ])
                    visited = set(state.get('visited', []))
                    parsed_set = set(state.get('parsed', []))
                    seen_texts = set(state.get('seen_texts', []))
                    visited_identifiers = set(state.get('visited_identifiers', []))  # visited_identifiers 로드
                    self.logger.info(f"불러온 상태: {len(fetch_queue)}개의 URL이 Fetch 큐에, {len(parse_queue)}개의 페이지가 Parse 큐에 있습니다. 방문한 URL 수: {len(visited)}, 파싱된 URL 수: {len(parsed_set)}, seen_texts 수: {len(seen_texts)}, visited_identifiers 수: {len(visited_identifiers)}.")
            except json.JSONDecodeError:
                self.logger.error("상태 파일이 손상되었습니다. 초기화합니다.")
                fetch_queue = deque()
                parse_queue = deque()
                visited = set()
                parsed_set = set()
                seen_texts = set()
                visited_identifiers = set()
        else:
            fetch_queue = deque()
            parse_queue = deque()
            visited = set()
            parsed_set = set()
            seen_texts = set()
            visited_identifiers = set()
            self.logger.info("새로운 크롤링 세션을 시작합니다.")

        return fetch_queue, parse_queue, visited, parsed_set, seen_texts, visited_identifiers
