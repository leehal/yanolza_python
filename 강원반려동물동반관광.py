import logging
import schedule
import time
import json
import requests
from bs4 import BeautifulSoup
import re

def perform_web_crawling():
    url = "https://www.pettravel.kr/petapi/data/food?contentSeq=610"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        def extract_text(element):
            return element.text.strip() if element else None
        def extract_href(element):
            return element['href'].strip() if element else None
        def extract_src(element):
            return element['src'].strip() if element else None
        def find_next_sibling_text(dt_text):
            dt_element = soup.find('dt', string=re.compile(dt_text))
            return extract_text(dt_element.find_next_sibling('dd')) if dt_element else None
        tour = []
        tname = extract_text(soup.find('h4'))
        taddr = find_next_sibling_text('주소')
        if taddr and taddr.startswith("강원"):
            taddr = "강원도" + taddr[2:]
        phone = find_next_sibling_text('문의')
        time = find_next_sibling_text('이용시간')
        homepage = extract_href(soup.find('a', href=True, title="새 창 열기"))
        guide = extract_text(soup.find('p', class_='pgraph')).replace('\r\n', ' ')
        info = extract_text(soup.find('ul', class_='listLv')).replace('\r\n\n', ', ').replace('\r\n', ' ')
        main_element = soup.find('h5', string=re.compile('이용요금')).find_next('ul')
        main_list = [li.get_text(" ", strip=True) for li in main_element.find_all('li')]
        main = ' / '.join(main_list).replace('\r\n', ' ').replace('\n', ' ')
        timage_element = soup.find('img', alt=re.compile('사진'))
        timage = "https://www.pettravel.kr" + extract_src(timage_element) if timage_element else None
        tour_data = {
            "tname": tname,
            "taddr": taddr,
            "phone": phone,
            "time": time,
            "tcategory": "맛집",
            "homepage": homepage,
            "guide": guide,
            "info": info,
            "main": main,
            "timage": timage
        }
        tour.append(tour_data)
        print(json.dumps(tour, ensure_ascii=False, indent=4))
# DB 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(tour), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')

def job():
    print("웹 크롤링을 수행합니다.")
    perform_web_crawling()

# 매일 정해진 시간에 동작하도록 구현
schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()  # 대기 중인 작업을 수행하는 함수
    time.sleep(60)  # 1초 동안 대기, CPU 사용량을 줄이기 위해서 사용