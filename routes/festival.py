import requests
from bs4 import BeautifulSoup
import logging
from requests.adapters import HTTPAdapter
import ssl
import re
import json
import html
from flask import Flask, jsonify, request, render_template_string, Response, Blueprint
from datetime import datetime, timedelta, date
import xml.etree.ElementTree as ET
import xmltodict
import pandas as pd
import urllib.parse

# 울산시 SSL 오류 대처용. 보안상 안전하지 않으니 개발 환경에서만 사용
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

# 경상남도 진주시_축제정보 (https://www.data.go.kr/data/15068865/openapi.do)
# 데이터 포맷 : JSON
festival_jjs_bp = Blueprint('festival_jjs', __name__)
def extract_date_from_unspecified(date_str):
# undecided에서 날짜 추출
    match = re.search(r'\d{4}년 .*', date_str)
    if match:
        return match.group(0)
    return None
def is_past_date(date_str):
# 주어진 날짜가 오늘 날짜 이전인지 확인
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_obj < date.today()
    except ValueError:
        return False
@festival_jjs_bp.route('/api/festival-jjs', methods=['GET'])
def get_festival_jjs():
    url = "https://www.jinju.go.kr/openapi/tour/festival.do"
# URL 잘 나오고 있음
    try:
    # HTTP GET 요청
        response = requests.get(url)
        data = response.json()
        festivals = data.get('results', [])
        festival_data = []
        for item in festivals:
            logging.info("Processing item: %s", item)
            sdate = item.get("sdate", "").strip()
            edate = item.get("edate", "").strip()
            undecided = item.get("undecided", "").strip()
            season = None
# sdate, edate 둘 다 비어 있는 경우
            if not sdate and not edate:
                if undecided:
                    season = extract_date_from_unspecified(undecided)
# sdate, edate가 모두 '2024-'로 시작하는 경우
            if sdate.startswith('2024-') and edate.startswith('2024-'):
                if is_past_date(sdate) and is_past_date(edate):
                    continue # 어제 이전의 축제라면 출력하지 않음
            timage = item.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = item.get("address", "")
            if not taddr.startswith("경상남도 진주시"):
                taddr = "경상남도 진주시 " + taddr
# 축제 데이터 추가
            festival = {
                "tname": item.get("name"),
                "tcategory": "축제",
                "taddr": taddr,
                "season": season,
                "homepage": item.get("homepage"),
                "phone": item.get("phone"),
                "tprice": item.get("fee"),
                "vehicle": item.get("parking"),
                "info": item.get("content"),
                "timage": timage
            }
            festival_data.append(festival)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(festival_data), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        template = """
        <!doctype html>
        <html lang="ko">
          <head>
            <meta charset="utf-8">
          </head>
          <body>
            <h4>진주 축제 정보</h4>
            {% for festival in festivals %}
              <p>tname : {{ festival.tname }}</h2>
              <p>tcategory : 축제</p>
              <p>taddr : {{ festival.taddr }}</p>
              <p>season : {{ festival.season }}</p>
              <p>homepage : {{ festival.homepage }}</p>
              <p>phone : {{ festival.phone }}</p>
              <p>tprice : {{ festival.tprice }}</p>
              <p>vehicle : {{ festival.vehicle }}</p>
              <p>info : {{ festival.info }}</p>
              <p>timage : <img src="{{ festival.timage }}" alt="축제 이미지"></p><hr>
            {% endfor %}
          </body>
        </html>
        """
        return render_template_string(template, festivals=festival_data)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500
# 성공!

# 울산광역시_문화축제 (https://www.data.go.kr/data/15098030/openapi.do)
# 데이터 포맷 : XML
festival_wss_bp = Blueprint('festival_wss', __name__)
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
def decode_html_entities(text):
    decoded_text = html.unescape(text)
    return decoded_text
def extract_phrase(text, start, end):
    """
       Extract phrase that starts with `start` and ends with `end`.
       Args:
           text (str): The text to search within.
           start (str): The starting substring.
           end (str): The ending substring.
       Returns:
           str: Extracted phrase.
       """
    try:
        start_idx = text.index(start)
        end_idx = text.index(end, start_idx) + len(end)
        return text[start_idx:end_idx].strip()
    except ValueError:
        return ""
@festival_wss_bp.route('/api/festival-wss', methods=['GET'])
def get_festival_wss():
    url = "https://apis.data.go.kr/6310000/ulsanfestival/getUlsanfestivalList?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&pageNo=1&numOfRows=16&searchDvsn1=1"
# URL 잘 나오고 있음
    today = datetime.now().date() # 오늘 날짜
    try:
        s = requests.Session() # requests 세션 생성
        s.mount('https://', SSLAdapter())
        response = s.get(url) # API 호출
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        festivals = soup.find_all('list')
        festival_data = []
        for item in festivals:
            raw_info = item.find('cn').text.strip() if item.find('cn') else 'N/A'
            cleaned_info = remove_html_tags(raw_info)
            decoded_info = decode_html_entities(cleaned_info)
            sdate_str = item.find('fstvlBgngYmd').text.strip() if item.find('fstvlBgngYmd') else ''
            edate_str = item.find('fstvlEndYmd').text.strip() if item.find('fstvlEndYmd') else ''
            season = f"{sdate_str} ~ {edate_str}" if sdate_str and edate_str else ''
            if sdate_str and edate_str:
                sdate = datetime.strptime(sdate_str, "%Y-%m-%d").date()
                edate = datetime.strptime(edate_str, "%Y-%m-%d").date()
                if edate < today: # 날짜가 모두 오늘 이전인지 확인
                    # 조건에 맞는 문구를 추출하여 season 값으로 설정
                    season_extracted = False
                    if "매년" in decoded_info:
                        if "월경" in decoded_info:
                            season = extract_phrase(decoded_info, "매년", "월경")
                            season_extracted = True
                        elif " 개최" in decoded_info:
                            season = extract_phrase(decoded_info, "매년", " 개최")
                            season_extracted = True
                        elif "월" in decoded_info:
                            season = extract_phrase(decoded_info, "매년", "월, ")
                            season_extracted = True
# 조건에 맞는 문구가 없는 경우 해당 축제를 출력하지 않음
                    if not season_extracted:
                        continue
                    else:
                        if not season or "매년 개최" in season:
                            season = "매년 5월경 개최"
# taddr의 "울산 "을 "울산광역시 "로 변경
            taddr = item.find('roadNmAddr').text.strip() if item.find('roadNmAddr') else 'N/A'
            if taddr.startswith("울산 "):
                taddr = taddr.replace("울산 ", "울산광역시 ", 1)
            festival = {
                'tname': item.find('title').text.strip() if item.find('title') else 'N/A',
                'taddr': taddr,
                'tcategory': '축제',
                'homepage': item.find('hmpgAddr').text.strip() if item.find('hmpgAddr') else 'N/A',
                'phone': item.find('rprsTelno').text.strip() if item.find('rprsTelno') else 'N/A',
                'season': season,
                'info': decoded_info,
            }
            festival_data.append(festival)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(festival_data), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error('데이터 전송 실패 : {response.status_code}, {response.text}')
        return jsonify(festival_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

# 대전광역시 문화축제 정보 (https://www.data.go.kr/data/15006969/openapi.do)
# 데이터 포맷 : JSON
# 최신 정보가 2023년 축제
def get_festival_djs():
# GET Param 방식 요청
    url = f"https://apis.data.go.kr/6300000/openapi2022/festv/getfestv?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&pageNo=1&numOfRows=13"
# HTTP GET 요청
    response = requests.get(url)
    if response.status_code != 200:
        return Response("Failed to retrieve data from API", status=500)
    # 응답 데이터 출력 (디버깅 목적)
    print(response.text)
    # XML 파싱
    soup = BeautifulSoup(response.text, "json")
    output = ""
    for loc in soup.select("item"):
        festvNm = loc.select_one('festvNm')
        festvPrid = loc.select_one('festvPrid')
        festvAddr = loc.select_one('festvAddr')
        festvDtlAddr = loc.select_one('festvDtlAddr')
        festvSumm = loc.select_one('festvSumm')
        refadNo = loc.select_one('refadNo')
        if festvNm and festvPrid and festvDtlAddr and festvSumm:
            output += f"<h3>tname : {festvNm.string}</h3>"
            output += f"season : {festvPrid.string}</br>"
            output += f"taddr : {festvAddr.string} {festvDtlAddr.string}</br>"
            output += f"info : {festvSumm.string}</br>"
            output += f"phone : {refadNo.string}</br>"
    if not output:
        return Response("No data found", status=204)
    # HTML 응답 생성
    return Response(output, mimetype='text/html')

# 경상남도 김해시_축제정보 (https://www.data.go.kr/data/15060348/openapi.do)
# 데이터 포맷 : JSON
URL = 'http://www.gimhae.go.kr/openapi/tour/festival.do'
festival_ghs_bp = Blueprint('festival_ghs', __name__)
def extract_date_from_info(info):
# 정규 표현식을 사용하여 info에서 '○ 개최시기 : ' 이후 '○ 장소 : ' 사이의 텍스트 추출
    match = re.search(r'○ 개최시기\s*:\s*(.*?)\s*○ 장소\s*:', info)
    if match:
        return match.group(1).strip()
    return '정보 없음'
@festival_ghs_bp.route('/api/festival-ghs', methods=['GET'])
def get_festival_ghs():
    try:
# JSON 데이터 가져오기
        response = requests.get(URL)
        data = response.json()
# 필요한 데이터 추출하여 festivals 리스트에 저장
        festivals = data['results']
        festivals_data = []
        for item in festivals:
            sdate = item.get('sdate', '').strip()
            edate = item.get('edate', '').strip()
            undecided = item.get('undecided', '').strip()
            info = item.get('content', 'N/A')
# sdate와 edate가 비어 있는 경우
            if not sdate and not edate:
                if undecided:
                    season = undecided
                else:
                    date_info = extract_date_from_info(info)
                    if date_info:
                        season = date_info
# sdate와 edate가 '2023-'로 시작하는 경우
            if sdate.startswith('2023-') and edate.startswith('2023-'):
                date_info = extract_date_from_info(info)
                if date_info:
                    season = date_info
                else:
# '○ 개최시기 : '와 ' ○ 장소 : ' 사이의 값이 없는 경우, 해당 축제 자체를 출력하지 않음
                    continue
            if season == '정보 없음':
                continue
            timage = item.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = item.get("address", "").replace('경남', '경상남도')
            festival = {
                'tname': item.get('name', 'N/A'),
                'taddr': taddr,
                'tcategory': '축제',
                'vehicle': item.get('parking', 'N/A'),
                'timage': timage,
                'homepage': item.get('homepage', 'N/A'),
                'phone': item.get('phone', 'N/A'),
                'tprice': item.get('fee', 'N/A'),
                'season': season,
                'info': info
            }
            festivals_data.append(festival)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(festivals_data), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
# HTML 템플릿을 사용하여 결과를 반환
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            {% for festival in festivals %}
                <h4>tname : {{ festival.tname }}</h2>
                <p>tcategory : 축제</p>
                <p>taddr : {{ festival.taddr }}</p>
                <p>homepage : {{ festival.homepage }}</p>
                <p>info : {{ festival.info }}</p>
                <p>phone : {{ festival.phone }}</p>            
                <p>season : {{ festival.season }}</p>
                <p>vehicle : {{ festival.vehicle }}</p>
                <p>tprice : {{ festival.tprice }}</p>
                <p>timage : 
                    {% if festival.timage %}
                        <img src="{{ festival.timage }}" alt="축제 이미지">
                    {% else %}
                        이미지 없음
                    {% endif %}
                </p><hr>
            {% endfor %}
        </body>
        </html>
        """
        return render_template_string(html_template, festivals=festivals_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

# 충청남도_축제 (https://www.data.go.kr/data/15063871/openapi.do)
# 데이터 포맷 : XML
# 잘 출력되지만 2018 이미지 많아서 안 되겠음
festival_ccnd_bp = Blueprint('festival_ccnd', __name__)
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
def decode_html_entities(text):
    return html.unescape(text)
@festival_ccnd_bp.route('/api/festival-ccnd', methods=['GET'])
def get_festival_ccnd():
    url = 'https://tour.chungnam.go.kr/_prog/openapi/?func=festival&start=1&end=34'
# URL 잘 나오고 있음
    try:
        # HTTP GET 요청
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        festivals = soup.find_all('item')
        festival_data = []
        for item in festivals:
            timage = item.find('list_img').text if item.find('list_img') else ""
            raw_info = item.find('desc').text.strip() if item.find('desc') else 'N/A'
            cleaned_info = remove_html_tags(raw_info)
            decoded_info = decode_html_entities(cleaned_info)
            festival = {
                'tname': item.find('nm').text.strip() if item.find('nm') else 'N/A',
                'taddr': item.find('addr').text.strip() if item.find('addr') else 'N/A',
                'tcategory': '축제',
                'timage': timage,
                'homepage': item.find('h_url').text.strip() if item.find('h_url') else 'N/A',
                'phone': item.find('tel').text.strip() if item.find('tel') else 'N/A',
                'season': item.find('festiavlDate').text.strip() if item.find('festiavlDate') else 'N/A',
                'info': decoded_info,
            }
            festival_data.append(festival)
        template = """
        <!doctype html>
        <html lang="ko">
          <head>
            <meta charset="utf-8">
          </head>
          <body>
            <h4>충남 축제 정보</h4>
            {% for festival in festivals %}
              <p>tname : {{ festival.tname }}</h2>
              <p>tcategory : 축제</p>
              <p>taddr : {{ festival.taddr }}</p>
              <p>season : {{ festival.season }}</p>
              <p>homepage : {{ festival.homepage }}</p>
              <p>phone : {{ festival.phone }}</p>
              <p>info : {{ festival.info }}</p>
              <p>timage : <img src="{{ festival.timage }}" alt="축제 이미지"></p><hr>
            {% endfor %}
          </body>
        </html>
        """
        return render_template_string(template, festivals=festival_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

def get_festival_ic():
    # API_KEY = '20240624O6FG0WG8YMO1EAQWJ4JO23EW'
# url 안 나오는 중
    url = 'http://iq.ifac.or.kr/openAPI/real/search.do?svID=culture&apiKey=20240624TXG4KFF0ZZ3653ZO21AJ5FN9&resultType=xml&pSize=15'
    try:
        response = requests.get(url)
        response.raise_for_status()
        xml_data = response.content
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    try:
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
    except ET.ParseError as e:
        return jsonify({"error": "Error parsing XML", "details": str(e)}), 500
    festival_data_list = []
    for item in items:
        festival_data = {
            "tname": item.get("title", ""),
            "homepage": item.get("link", ""),
            "season": item.get("period", ""),
            "phone": item.get("tel", ""),
            "info": item.get("description", "")
        }
        festival_data_list.append(festival_data)
    return jsonify(festival_data_list)