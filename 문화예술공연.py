import re
import logging
import schedule
import time
import json
import requests
import html
from bs4 import BeautifulSoup

def perform_web_crawling():
    address_replacements = {
        "경북": "경상북도", "경남": "경상남도", "충남": "충청남도", "충북": "충청북도", "전북": "전라북도", "전남": "전라남도",
        "부산": "부산광역시", "대구": "대구광역시", "광주": "광주광역시", "대전": "대전광역시", "인천": "인천광역시", "울산": "울산광역시",
        "서울": "서울특별시", "세종": "세종특별자치시", "경기": "경기도", "강원": "강원도", "제주": "제주도", "공주": "충청남도 공주시"
    }
    url = "https://www.mcst.go.kr/kor/s_culture/culture/cultureList.jsp?pSeq=&pRo=&pCurrentPage=3&pType=&pPeriod=&fromDt=&toDt=&pArea=%EC%A0%84%EB%B6%81&pSearchType=01&pSearchWord="
# 연극, 뮤지컬, 오페라, 음악, 콘서트, 국악, 무용, 전시, 기타
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        arts = []
        art_items = soup.select('ul.mediaWrap.col2 > li')  # 각 문화 예술 아이템들을 찾음
        for item in art_items:
            timage_tag = item.find('div', class_='img').img
            timage = f"https://www.mcst.go.kr{timage_tag['src']}" if timage_tag else ''
            tname_tag = item.find('p', class_='title')
            tname = ''
            if tname_tag:
                tname_text = tname_tag.text.strip()
                tname_text = html.unescape(tname_text) # HTML 엔티티를 변환
                if ']' in tname_text:
                    tname = tname_text.split(']')[-1].strip()
                if not tname:  # tname이 공백으로 나오는 경우
                    if ']' in tname_text and '[' in tname_text:
                        tname = tname_text.split(']')[-1].split('[')[0].strip()
            details = item.find_all('li')
            season, taddr, phone = '', '', ''
            if len(details) > 0:
                period_text = details[0].text.strip().split('기간:')[1].strip() if '기간:' in details[0].text else ''
                season = period_text if period_text else ''
            if len(details) > 1:
                taddr_text = details[1].text.strip().split('장소:')[1].split('</li>')[0].strip() if '장소:' in details[1].text else ''
                taddr_parts = taddr_text.split('|')
                if len(taddr_parts) == 2:
                    region, location = taddr_parts
                    region = address_replacements.get(region.strip(), region.strip())
                    taddr = f"{region} {location.strip()}"
            if len(details) > 2:
                phone_text = details[2].text.strip().split('문의:')[1].strip() if '문의:' in details[2].text else ''
                phone = phone_text if phone_text else ''
            homepage_tag = item.find('a', class_='go')
            homepage = f"https://www.mcst.go.kr/kor/s_culture/culture/{homepage_tag['href']}" if homepage_tag else ''
            art_data = {
                    "timage": timage,
                    "tname": tname,
                    "season": season,
                    "tcategory": "관광",
                    "taddr": taddr,
                    "phone": phone,
                    "homepage": homepage
            }
            if any(value for key, value in art_data.items() if key != "tcategory"): # 내용이 없는 경우는 제외 (tcategory 제외)
                arts.append(art_data)
        print(json.dumps(arts, ensure_ascii=False, indent=4)) # 데이터를 예쁘게 출력하기 위해 JSON 형식으로 변환
# DB 전송
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(arts), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')

def job():
    print("웹 크롤링을 수행합니다.")
    perform_web_crawling()
# 매일 정해진 시간에 동작하도록 구현
schedule.every(1).minutes.do(job)
while True:
    schedule.run_pending() # 대기 중인 작업을 수행하는 함수
    time.sleep(60) # 1초 동안 대기, CPU 사용량을 줄이기 위해서 사용