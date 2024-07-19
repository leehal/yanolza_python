import logging
import schedule
import time
import json
import re
import requests
from bs4 import BeautifulSoup

def perform_web_crawling():
    url = "https://korean.visitkorea.or.kr/kfes/list/wntyFstvlList.do"
# 축제 하나하나 다 눌러보기
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        def extract_text(selector, attribute=None, regex=False):
            try:
                if regex:
                    return soup.find('a', href=re.compile(attribute)).text.strip()
                return soup.find(selector, class_=attribute).text.strip() if attribute else soup.find(selector).text.strip()
            except AttributeError:
                return None
        festivals = []
        festival_data = {
            "guide": extract_text('span', 'sub_title'),
            "tname": soup.find('h2', id='festival_head').text.strip(),
            "info": extract_text('div', 'slide_content fst'),
            "timage": soup.find('img', alt='2024 양화진 근대사 뱃길탐방 포스터')['src'],
            "season": soup.find('span', class_='blind', string='축제 기간').find_next_sibling('span').text.strip(),
            "tcategory": "축제",
            "taddr": extract_text('p', 'info_content'),
            "tprice": soup.find('div', class_='info_ico price').find_next_sibling('p').text.strip().replace('<br>', ' / '),
            "phone": extract_text('a', r'tel:', regex=True),
            "homepage": soup.find('a', class_='homepage_link_btn')['href']
        }
# 데이터를 예쁘게 출력하기 위해 JSON 형식으로 변환
        festivals.append(festival_data)
        print(json.dumps(festivals, ensure_ascii=False, indent=4))
# DB 전송
        # url1 = 'http://localhost:8222/api/travel'
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(url1, data=json.dumps(festivals), headers=headers)
        # if response.status_code == 200:  # 응답 확인
        #     print('데이터 전송 성공')
        # else:
        #     logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')

def job():
    print("웹 크롤링을 수행합니다.")
    perform_web_crawling()

# 매일 정해진 시간에 동작하도록 구현
schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()  # 대기 중인 작업을 수행하는 함수
    time.sleep(60)  # 1초 동안 대기, CPU 사용량을 줄이기 위해서 사용