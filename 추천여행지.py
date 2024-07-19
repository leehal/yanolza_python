import logging
import schedule
import time
import json
import re
import requests
from bs4 import BeautifulSoup

def perform_web_crawling(): # 웹 크롤링 작업 수행
    address_replacements = {
        "전북": "전라북도", "충남": "충청남도", "인천": "인천광역시", "강원": "강원도", "울산": "울산광역시"
    }
    url = "https://www.mcst.go.kr/kor/s_culture/tour/tourList.jsp"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        recommendations = []
        media_items = soup.find_all('li')
# season 정보는 상위 태그에서 한 번 추출하여 모든 항목에 동일하게 적용
        season_tag = soup.find('div', class_='box01').find_all('p')[0]
        season_match = re.search(r'한국관광공사가 선정한\s*(.*)\s*추천 가볼 만한 곳의 테마는', season_tag.text.strip()) if season_tag else None
        season = season_match.group(1).strip() if season_match else ''
        for item in media_items:
            timage_tag = item.find('div', class_='img').img if item.find('div', class_='img') else None
            timage_src = timage_tag['src'] if timage_tag else ''
            timage = f"https://www.mcst.go.kr{timage_src}" if timage_src else ''

            tname_full = item.find('p', class_='title').text.strip() if item.find('p', class_='title') else ''
            tname = tname_full.split(', ')[-1].split('! ')[-1]  # ', ' 또는 '! ' 뒤부터 시작
            taddr = item.find('div', class_='ny line').text.strip() if item.find('div', class_='ny line') else ''
            for short, full in address_replacements.items():
                if taddr.startswith(short):
                    taddr = taddr.replace(short, full, 1)  # 첫 번째 매칭 단어만 변경

            phone_tag = item.find('ul', class_='detail_info').find('li') if item.find('ul', class_='detail_info') else None
            phone_match = re.search(r'문의\s*:\s*(.*)', phone_tag.text.strip()) if phone_tag else None
            phone = phone_match.group(1).strip() if phone_match else ''

            homepage_tag = item.find('a', class_='go') if item.find('a', 'go') else None
            homepage_href = re.search(r"fnView\((\d+)\)", homepage_tag['onclick']).group(1) if homepage_tag else ''
            homepage = f"https://www.mcst.go.kr/kor/s_culture/tour/tourView.jsp?pDetailSeq={homepage_href}" if homepage_href else ''
            if timage or tname or taddr or phone or homepage:
                recommendation_data = {
                        "timage": timage,
                        "tname": tname,
                        "tcategory": "관광",
                        "taddr": taddr,
                        "season": season,
                        "phone": phone,
                        "homepage": homepage
                }
                recommendations.append(recommendation_data)
# 데이터를 예쁘게 출력하기 위해 JSON 형식으로 변환
        print(json.dumps(recommendations, ensure_ascii=False, indent=4))
# DB 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(recommendations), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')

def job():
    print("웹 크롤링을 수행합니다.")
    perform_web_crawling()
# 매일 정해진 시간에 동작하도록 구현
schedule.every(1).weeks.do(job)
while True:
    schedule.run_pending() # 대기 중인 작업을 수행하는 함수
    time.sleep(60) # 1분 동안 대기, CPU 사용량을 줄이기 위해서 사용

def message():
    print("스케줄 실행 중")
job1 = schedule.every(5).seconds.do(message)
count = 0
while True:
    schedule.run_pending()
    time.sleep(1)
    count += 1
    if count > 5:
        schedule.cancel_job(job1)