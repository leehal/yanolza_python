import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import urllib.parse

# 예술의전당(seoul arts center)_종합 공연정보
# https://www.culture.go.kr/data/openapi/openapiView.do?id=610&category=A&gubun=A#/default/%EC%9A%94%EC%B2%AD%EB%A9%94%EC%8B%9C%EC%A7%80_Get
def clean_text(text):
    # Remove unwanted tags
    unwanted_tags = [
        "<!--[if !supportEmptyParas]--><!--[endif]-->", "<o:p></o:p>", "\n", "amp;",
        "<span 맑은=\"\" 고딕\";\"=\"\" style=\"font-weight: 400; font-size: 14px;\">",
        "<span 맑은=\"\" 고딕\";=\"\" font-size:=\"\" 12px;=\"\" background-color:=\"\" var(--white);=\"\" letter-spacing:=\"\" -0.02rem;\"=\"\" style=\"font-family: sans-serif; font-size: 12.25px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; background-color: var(--white); letter-spacing: -0.175px;\">",
        "<span data-contrast=\"auto\" xml:lang=\"KO-KR\" lang=\"KO-KR\" class=\"TextRun SCXW34213708 BCX8\" style=\"background-color: transparent; color: windowtext; font-style: normal; font-weight: normal; text-align: justify; white-space-collapse: preserve; letter-spacing: normal; -webkit-user-drag: none; -webkit-tap-highlight-color: transparent; user-select: text; font-size: 10pt; line-height: 19.425px; font-family: &quot;맑은 고딕&quot;, &quot;맑은 고딕_EmbeddedFont&quot;, sans-serif; font-variant-ligatures: none !important;\">",
    ]
    for tag in unwanted_tags:
        text = text.replace(tag, '')
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('\u003C', '<').replace('\u003E', '>').replace('=======================================================', ' / ')
    return text
def get_play_sac():
# url 잘 나오는 중
    url = 'http://api.kcisa.kr/openapi/API_CCA_148/request?serviceKey=8d673c13-7889-434a-abf7-56d0712c8ea4'
    params = {
            'numOfRows': '4242', # 8485, 4242
            'pageNo': '1'        # 1~2,  1~4
    } # totalCount : 16970
    try:
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.content, 'xml')
        plays = soup.find_all('item')
        play_data = []
        today = datetime.now().date()
        for item in plays:
            sac = item.find('CNTC_INSTT_NM').text.strip() if item.find('CNTC_INSTT_NM') else ''
            taddr = f"서울특별시 서초구 남부순환로 2406 {sac}"
            genre = item.find('GENRE').text.strip() if item.find('GENRE') else ''
            audience = item.find('AUDIENCE').text.strip() if item.find('AUDIENCE') else ''
            if genre and audience:
                guide = f"장르 : {genre} / 대상 : {audience}"
            elif genre:
                guide = f"장르 : {genre}"
            elif audience:
                guide = f"대상 : {audience}"
            else:
                guide = ''
            period = item.find('PERIOD').text.strip() if item.find('PERIOD') else ''
            if period != '':
                start_date, end_date = period.split('~')
                end_date = datetime.strptime(end_date.strip(), '%Y-%m-%d').date()
                if end_date <= today:
                    continue
                play = {
                    'tname': item.find('TITLE').text.strip() if item.find('TITLE') else '',
                    'taddr': taddr,
                    'tcategory': '관광',
                    'timage': item.find('IMAGE_OBJECT').text.strip() if item.find('IMAGE_OBJECT') else '',
                    'homepage': item.find('URL').text.strip() if item.find('URL') else '',
                    'phone': item.find('CONTACT_POINT').text.strip() if item.find('CONTACT_POINT') else '',
                    'season': period,
                    'time': item.find('EVENT_PERIOD').text.strip() if item.find('EVENT_PERIOD') else '',
                    'guide': guide,
                    'info': clean_text(item.find('DESCRIPTION').text.strip()) if item.find('DESCRIPTION') else ''
                }
                play_data.append(play)
# 스프링 부트 RestController 엔드포인트 URL
#             url1 = 'http://localhost:8222/api/travel'
#             headers = {"Content-Type": "application/json"}
#             try:
#                 response = requests.post(url1, data=json.dumps(play_data), headers=headers)
#                 if response.status_code == 200:  # 응답 확인
#                     print('데이터 전송 성공')
#                 else:
#                     logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
#             except Exception as e:
#                 logging.error(f'API 전송 중 오류 발생: {str(e)}')
        template = """
        <!doctype html>
        <html lang="ko">
          <head>
            <meta charset="utf-8">
          </head>
          <body>
            <h4>예술의 전당 공연 정보</h4>
            {% for play in play_data %}
                <p>tname : {{ play.tname }}</p>
                <p>tcategory : 관광</p>
                <p>taddr : {{ play.taddr }}</p>
                <p>season : {{ play.season }}</p>
                <p>homepage : <a href="{{ play.homepage }}" target="_blank">{{ play.homepage }}</a></p>
                <p>phone : {{ play.phone }}</p>
                <p>time : {{ play.time }}</p>
                <p>guide : {{ play.guide }}</p>
                <p>info : {{ play.info }}</p>
                <p>timage : <img src="{{ play.timage }}" alt="공연 이미지"></p>
            {% endfor %}
          </body>
        </html>
        """
        return render_template_string(template, play_data=play_data)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

# 문화체육관광부_문화예술공연(통합)
# https://www.culture.go.kr/data/openapi/openapiView.do?id=580&category=A&gubun=A
def get_play_mcst():
    url = 'http://api.kcisa.kr/openapi/CNV_060/request?serviceKey=69beb262-e4f8-458c-ac7e-341d493d15cb'
    params = {
        'numOfRows': '17688',  # 17688, 8844
        'pageNo': '1'         # 1~2,   1~4
    }  # totalCount : 35376
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, 'xml')
    plays = soup.find_all('item')
    play_data = []
    today = datetime.now().date()
    for item in plays:
        play = {
            'tname': item.find('title').text.strip() if item.find('title') else '',
            'taddr': item.find('eventSite').text.strip() if item.find('eventSite') else '',
            'tcategory': '관광',
            'timage': item.find('imageObject').text.strip() if item.find('imageObject') else '',
            'homepage': item.find('url').text.strip() if item.find('url') else '',
            'phone': item.find('contactPoint').text.strip() if item.find('contactPoint') else '',
            'season': item.find('period').text.strip() if item.find('period') else '',
            'time': item.find('eventPeriod').text.strip() if item.find('eventPeriod') else '',
            'info': clean_text(item.find('description').text.strip()) if item.find('description') else ''
        }
        play_data.append(play)
    return play_data