import logging
import schedule
import time
import json
import requests
from bs4 import BeautifulSoup

def perform_web_crawling():
    url = "https://korean.visitkorea.or.kr/kfes/detail/fstvlDetail.do?fstvlCntntsId=e4351add-7b59-4842-b3b5-c38062b47c7c&cntntsNm=%EC%96%91%ED%99%94%EC%A7%84%EA%B7%BC%EB%8C%80%EC%82%AC%EB%B1%83%EA%B8%B8%ED%83%90%EB%B0%A9"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        festivals = []
# 필요한 정보 추출
        guide = soup.find('span', class_='sub_title').text.strip()
        tname = soup.find('h2', id='festival_head').text.strip()
        info = soup.find('div', class_='slide_content.fst').text.strip().replace('\n', ' ')
        timage = soup.find('img', alt='2024 양화진 근대사 뱃길탐방 포스터').text.strip()
        season = soup.find('span', class_='blind', text='축제 기간').text.strip().text.strip()
        taddr = soup.find('div', {'@type': 'PostalAddress'}).text.strip()
        tprice = soup.find('div', class_='info_ico price').text.strip().replace('<br>', ' / ')
        phone = soup.find('a', href=re.compile(r'tel:')).text.strip()
        homepage = soup.find('a', class_='homepage_link_btn')['href']
        festival_data = {
            "guide": guide,
            "tname": tname,
            "info": info,
            "timage": timage,
            "season": season,
            "tcategory": "축제",
            "taddr": taddr,
            "tprice": tprice,
            "phone": phone,
            "homepage": homepage
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