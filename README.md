# crawler

예시 :

python main.py --start_url "https://www.yonsei.ac.kr/sc/" --fetch_threads 3 --parse_threads 5 --save_interval 10

아래 링크 크롤링 해야 합니다.

https://www.yonsei.ac.kr/sc/


https://library.yonsei.ac.kr/bbs/list/1 - 로그인을 안 하면 못 보는 사이트가 많아서 추후 크롤링


메인 공지사항 실시간 크롤링

python -m announcement_crawler.main_for_announcement

진행중 
 https://yicrc.yonsei.ac.kr/ (준혁)
 https://yicdorm.yonsei.ac.kr/


완료 
https://computing.yonsei.ac.kr/
https://ysb.yonsei.ac.kr/
https://dorm.yonsei.ac.kr/
https://rc.yonsei.ac.kr/
https://oia.yonsei.ac.kr/ - 중복 추후 제거