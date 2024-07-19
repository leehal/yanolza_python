import logging
import schedule
import time
import json
import re
import requests
from bs4 import BeautifulSoup
import mysql.connector
import pymysql

def perform_web_crawling():
    address_replacements = { "세종시 세종특별자치시": "세종특별자치시" }
    url = "https://www.mcst.go.kr/kor/s_culture/festival/festivalList.jsp?pMenuCD=&pCurrentPage=19&pSearchType=&pSearchWord=&pSeq=&pSido=&pOrder=&pPeriod=&fromDt=&toDt="
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        festivals = []
        festival_items = soup.find_all('li') # li 태그로 감싸진 각 축제 아이템들을 찾음
        for item in festival_items:
            timage_tag = item.find('div', class_='img').img if item.find('div', class_='img') else None
            timage = f"https://www.mcst.go.kr{timage_tag['src']}" if timage_tag else ''
            tname = item.find('p', class_='title').text.strip() if item.find('p', class_='title') else ''
            info = item.find('div', class_='ny').text.strip() if item.find('div', class_='ny') else ''
            info = info.replace('\r\n\r\n', ' ')
            details = item.find('ul', class_='detail_info')
            season, time, taddr, phone = '', '', '', ''
            if details:
                detail_items = details.find_all('li')
                if len(detail_items) > 0:
                    season_text = detail_items[0].text.strip()
                    if '기간:' in season_text:
                        period_text = season_text.split('기간:')[1].strip()
                        if '|' in period_text:
                            season, time = map(str.strip, period_text.split('|'))
                        else:
                            season = period_text
                if len(detail_items) > 1:
                    taddr_match = re.search(r'장소:\s*(.*)', detail_items[1].text.strip())
                    if taddr_match:
                        taddr = taddr_match.group(1).strip()
                if len(detail_items) > 2:
                    phone_match = re.search(r'문의:\s*(.*)', detail_items[2].text.strip())
                    if phone_match:
                        phone = phone_match.group(1).strip()
            homepage_tag = item.find('a', class_='go')
            homepage = f"https://www.mcst.go.kr/kor/s_culture/festival/{homepage_tag['href']}" if homepage_tag else ''
            for old_addr, new_addr in address_replacements.items(): # 주소 치환
                if old_addr in taddr:
                    taddr = taddr.replace(old_addr, new_addr)
            festival_data = {
                    "timage": timage,
                    "tname": tname,
                    "info": info,
                    "season": season,
                    "tcategory": "축제",
                    "time": time,
                    "taddr": taddr,
                    "phone": phone,
                    "homepage": homepage
            }
            if any(value for key, value in festival_data.items() if key != "tcategory"): # 내용이 없는 경우는 제외 (tcategory 제외)
                festivals.append(festival_data)
# 데이터를 예쁘게 출력하기 위해 JSON 형식으로 변환
        print(json.dumps(festivals, ensure_ascii=False, indent=4))
# DB 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(festivals), headers=headers)
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
    schedule.run_pending() # 대기 중인 작업을 수행하는 함수
    # time.sleep(60) # 1초 동안 대기, CPU 사용량을 줄이기 위해서 사용

# def message():
#     print("스케줄 실행 중")
# job1 = schedule.every(5).seconds.do(message)
# count = 0
# while True:
#     schedule.run_pending()
#     time.sleep(1)
#     count += 1
#     if count > 5:
#         schedule.cancel_job(job1)