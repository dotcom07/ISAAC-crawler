# crawler

```markdown
# Yonsei 웹 크롤러

이 크롤러는 연세대학교 웹사이트에서 다양한 데이터를 크롤링하고, 텍스트, 이미지, 파일 및 테이블 데이터를 수집하여 JSON 형식으로 저장합니다.
공지사항의 경우 실시간 크롤링이 가능하며, 중복 크롤링을 방지하고 상태 저장을 통해 중단 후 재개가 가능합니다.

## 설치 및 실행 방법

1. Python 3.8 이상이 설치된 환경에서 다음과 같이 패키지를 설치합니다:

   ```bash
   pip install -r requirements.txt
   ```

2. 다음 명령어로 크롤러를 실행할 수 있습니다:

   ```bash
   python main.py --start_url "https://www.yonsei.ac.kr/sc/" --fetch_threads 3 --parse_threads 5 --save_interval 10
   ```

### 주요 실행 옵션

- `--start_url`: 크롤링을 시작할 URL을 지정합니다.
- `--fetch_threads`: URL을 가져오는 스레드 수를 설정합니다.
- `--parse_threads`: 페이지를 파싱하는 스레드 수를 설정합니다.
- `--save_interval`: 상태 저장 주기(초)를 지정합니다.

## 크롤링 대상

### 메인 공지사항

다음 URL은 기본적으로 크롤링이 진행됩니다:

- [연세대학교 메인 사이트](https://www.yonsei.ac.kr/sc/)

### 추가 예정 URL

아래 사이트는 로그인이나 실시간 추가 작업이 필요할 때 크롤링에 추가될 수 있습니다:

- [연세대 도서관](https://library.yonsei.ac.kr/bbs/list/1) (로그인 필요)
- [장학 공지사항](https://www.yonsei.ac.kr/sc/support/scholarship.jsp) (대부분 마감됨)
- [기숙사 공지사항](https://yicdorm.yonsei.ac.kr/board.asp?mid=m05_07)

## 크롤링 상태 저장 및 재개

크롤링 작업 중 상태를 정기적으로 `crawler_state.json` 파일에 저장하며, 이를 통해 중단된 위치부터 크롤링을 재개할 수 있습니다.

## 프로젝트 구조

- `crawler.py`: 크롤러의 핵심 로직을 담고 있는 파일입니다.
- `fetcher.py`: 웹페이지를 가져오는 클래스입니다.
- `parser.py`: HTML을 파싱하여 텍스트, 이미지, 파일, 테이블 등의 데이터를 추출합니다.
- `saver.py`: 추출한 데이터를 저장하는 클래스입니다.
- `state_manager.py`: 크롤링 상태를 관리하고 저장합니다.
- `announcement_crawler/`: 공지사항 전용 크롤러 모듈이 포함된 폴더입니다.

## 사용 예시

연세대학교 메인 사이트의 공지사항을 크롤링하는 예시입니다:

```bash
python main.py --start_url "https://www.yonsei.ac.kr/sc/support/notice.jsp" --fetch_threads 3 --parse_threads 5 --save_interval 10
```

## 주의사항

- 일부 사이트는 로그인 세션이 필요하거나, 특정 URL 패턴은 제외하여야 합니다.
- 크롤링할 때는 웹사이트의 규정을 준수하세요.
