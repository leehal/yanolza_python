from flask import Flask, jsonify, Response, request, json, render_template_string
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import ssl
import json
import xmltodict
import re
import urllib3
import logging

# 세종시 숙박업 정보가 화면에 출력이 안 되어 SSLContext를 명시적으로 설정했으며 개발 환경에서만 사용하는 것이 좋음
# 운영 환경에서는 SSL 인증서를 제대로 검증해야 함
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

# 서울시 관광숙박업 인허가 정보 (https://data.seoul.go.kr/dataList/OA-16043/S/1/datasetView.do)
# 데이터 포맷 : XML
def get_lodge_seoul():
# url 잘 나왔음
    url = 'http://openapi.seoul.go.kr:8088/56586a6766746a6435344e6369494b/xml/LOCALDATA_031101/1/638/'
# HTTP GET 요청
    response = requests.get(url)
    # XML 파싱
    soup = BeautifulSoup(response.content, "xml")
    lodge_data = []
    for loc in soup.select("row"):
        if loc.select_one('DTLSTATENM').string != '영업중':
            continue
        info_parts = []
        if loc.select_one('STROOMCNT') and loc.select_one('STROOMCNT').text != '':
            info_parts.append(f"객실수 : {loc.select_one('STROOMCNT').text}개")
        if (loc.select_one('TOTNUMLAY') and loc.select_one('TOTNUMLAY').text != '') or \
                (loc.select_one('JISGNUMLAY') and loc.select_one('JISGNUMLAY').text != '') or \
                (loc.select_one('UNDERNUMLAY') and loc.select_one('UNDERNUMLAY').text != ''):
            floor_info = f"총 층수 : {loc.select_one('TOTNUMLAY').text}층 (지상층수 {loc.select_one('JISGNUMLAY').text}층 + 지하층수 {loc.select_one('UNDERNUMLAY').text}층)"
            info_parts.append(floor_info)
        info = ' / '.join(info_parts)
        guide_parts = []
        if loc.select_one('REGNSENM') and loc.select_one('REGNSENM').text != '':
            guide_parts.append(loc.select_one('REGNSENM').text)
        if loc.select_one('NEARENVNM') and loc.select_one('NEARENVNM').text != '':
            guide_parts.append(loc.select_one('NEARENVNM').text)
        guide = '주변환경 : ' + ', '.join(guide_parts) if guide_parts else ''
        data = {
            'tname': loc.select_one('BPLCNM').text,
            'tcategory': '숙박',
            'taddr': loc.select_one('RDNWHLADDR').text,
            'phone': loc.select_one('SITETEL').text,
            'info': info,
            'guide': guide
        }
        lodge_data.append(data)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
    url1 = 'http://localhost:8222/api/travel'
    headers = {"Content-Type": "application/json"}
    response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
    if response.status_code == 200:  # 응답 확인
        print('데이터 전송 성공')
    else:
        logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
    return lodge_data
# 성공!

# 세종특별자치시_숙박업 정보 (https://www.data.go.kr/data/15111351/openapi.do)
# 데이터 포맷 : JSON
def get_lodge_sjs():
    url = 'https://apis.data.go.kr/5690000/sejong_accommodation1/getAccommodation1?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&pageNo=1&numOfRows=80'
# 마이페이지 - 활용신청 상세기능정보 - 미리보기 확인 - 서비스 키 입력 - 미리보기 클릭 시 url인데 내용 잘 나왔음
# url = 'https://apis.data.go.kr/5690000/sejong_accommodation1/getAccommodation1'
# API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
# requests 세션 생성
    s = requests.Session()
    s.mount('https://', SSLAdapter())
# API 호출
    response = s.get(url)
    if response.status_code == 200:
        data = response.json()
        items = data['body']['items']
        lodge_data = []
        for loc in items:
            lodge = {
                'tname': loc['bplcNm'],
                'tcategory': '숙박',
                'taddr': loc['lctnAddr'],
                'phone': loc['lctnTelno']
            }
            lodge_data.append(lodge)
# 스프링 부트 RestController 엔드포인트 URL
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
#         # 응답 확인
#         if response.status_code == 200:
#             print('데이터 전송 성공')
#         else:
#             print('데이터 전송 실패')
        return jsonify(lodge_data)
    else:
        return f"Error: {response.status_code}"
# 성공!

# (경기) 관광 숙박업체 현황
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=FED08865892P12R201MY312133&infSeq=3&searchWord=%EA%B4%80%EA%B4%91+%EC%88%99%EB%B0%95%EC%97%85%EC%B2%B4+%ED%98%84%ED%99%A9
# 데이터 포맷 : XML
def get_lodge_ggd():
    url = 'https://openapi.gg.go.kr/TourismStaying?KEY=ec0338c3e3ab42939f2b7c3dd5f18a71&Type=xml&pIndex=1&pSize=352'
# url 잘 나옴
# 요청 및 응답
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')
    try:
        dict_data = xmltodict.parse(response.text)
# XML 구조 확인 후 올바르게 파싱
        if dict_data['TourismStaying']['head']['RESULT']['CODE'] != 'INFO-000':
            return Response("Error: Invalid API response", status=500, mimetype='text/plain')
        lodge_items = dict_data['TourismStaying']['row']
        lodge_data = []
        for item in lodge_items:
            if item['BSN_STATE_NM'] != '영업중':
                continue
            tname = item.get('BIZPLC_NM')
            eng_name = item.get('ENG_CMPNM_NM')
            if eng_name:
                tname += f" ({eng_name})"
# taddr : 길 주소 없으면 지번 주소
            taddr = item.get('REFINE_ROADNM_ADDR') or item.get('REFINE_LOTNO_ADDR', '')
            if not taddr: # 주소 없으면 출력 X
                continue
            info_parts = []
            if item.get('INSRNC_INST_NM'):
                info_parts.append(f"보험 : {item.get('INSRNC_INST_NM')}")
            if item.get('ROOM_CNT') and item.get('ROOM_CNT') != '0':
                info_parts.append(f"객실수 : {item.get('ROOM_CNT')}개")
            if (item.get('TOT_FLOOR_CNT') and item.get('TOT_FLOOR_CNT') != '0') or \
                (item.get('GROUND_FLOOR_CNT') and item.get('GROUND_FLOOR_CNT') != '0') or \
                (item.get('UNDGRND_FLOOR_CNT') and item.get('UNDGRND_FLOOR_CNT') != '0'):
                floor_info = f"총 층수 : {item.get('TOT_FLOOR_CNT', '0')}층 (지상층수 {item.get('GROUND_FLOOR_CNT', '0')}층 + 지하층수 {item.get('UNDGRND_FLOOR_CNT', '0')}층)"
                info_parts.append(floor_info)
            info = ' / '.join(info_parts)
            guide_parts = []
            if item.get('REGION_DIV_NM'):
                guide_parts.append(item.get('REGION_DIV_NM'))
            if item.get('CIRCUMFR_ENVRN_NM'):
                guide_parts.append(item.get('CIRCUMFR_ENVRN_NM'))
            guide = '주변환경 : ' + ', '.join(guide_parts) if guide_parts else ''
            phone = item.get('LOCPLC_FACLT_TELNO', '')
            data = {
                'tname': tname,
                'tcategory': "숙박",
                'taddr': taddr,
                'info': info,
                'guide': guide,
                'phone': phone
            }
            lodge_data.append(data)
# 스프링 부트 RestController 엔드포인트 URL
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
#         if response.status_code == 200:
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        return jsonify(lodge_data)
    except Exception as e:
        return Response(f"error: {str(e)}", status=500, mimetype='text/plain')

# 경기도 이천시_숙박정보
# 데이터 포맷 : JSON
def get_lodge_ics():
    url = 'http://www.icheon.go.kr/portal/contents.do?key=1739'
# HTTP Status : 400이 떠서 데이터 개선 요청 중

# 대구광역시_테마별 숙박시설
# 데이터 포맷 : JSON
def get_lodge_dgs():
    try:
# url 잘 나옴
        url = 'https://thegoodnight.daegu.go.kr/ajax/api/thegoodnight.html?mode=json&item_count=112'
        response = requests.get(url)
        if response.status_code != 200: # 응답 상태 코드 확인
            return Response(f"Error: Unable to fetch data, status code: {response.status_code}", status=500)
        response_text = response.text # 응답 데이터 로그 출력
        data = json.loads(response_text)
        results = []
        for loc in data['data']:
            taddr = loc.get('address', 'N/A')
            if not taddr.startswith("대구광역시"):
                taddr = "대구광역시 " + taddr
            result = {
                "tname": loc.get('shop', 'N/A'),
                "taddr": taddr,
                "phone": loc.get('tel', 'N/A'),
                "info": loc.get('offer', 'N/A'),
                "guide": loc.get('facilities', 'N/A')
            }
            results.append(result)
# 스프링 부트 RestController 엔드포인트 URL
        try:
            url1 = 'http://localhost:8222/api/travel'
            headers = {"Content-Type": "application/json"}
            response = requests.post(url1, data=json.dumps(results), headers=headers)
            if response.status_code == 200:
                print('데이터 전송 성공')
            else:
                print(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        except Exception as e:
            print(f"데이터 전송 중 오류 발생: {str(e)}")
        return jsonify(results)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

# 대전광역시 문화관광(숙박정보)
# 데이터 포맷 : JSON
def get_lodge_djs():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)

# 경상북도_숙박시설 정보조회
# 데이터 포맷 : XML
def get_lodge_gsbd():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)

# 경상북도 경주시_경주문화관광_테마별 숙박업 정보
# 데이터 포맷 : JSON
def get_lodge_gjs():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)

# 경상남도 김해시_숙박업 정보 (https://www.gimhae.go.kr/00761/00832/05866.web)
# 데이터 포맷 : JSON
def get_lodge_ghs():
# url 잘 나옴 (record_count 169, pageunit 최대 10이니까 page (1~17) 숫자 적절히 바꿀 것)
    url = 'http://www.gimhae.go.kr/openapi/tour/lodging.do?pageunit=10&page=17'
    try:
# JSON 데이터 가져오기
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
# 필요한 데이터 추출하여 리스트에 저장
        lodges = data['results']
        lodge_data = []
        for item in lodges:
            timage = item.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = item.get('address', 'N/A')
            # if not taddr.startswith('경상남도 김해시'):
            #     if taddr.startswith('김해시'):
            #         taddr = '경상남도 ' + taddr
            #     else:
            #         taddr = '경상남도 김해시 ' + taddr
            lodge = {
                'tname': item.get('name', 'N/A'),
                'taddr': taddr,
                'tcategory': '숙박',
                'timage': timage,
                'phone': item.get('phone', 'N/A'),
                'time': item.get('checktime', 'N/A'),
                'homepage': item.get('homepage', 'N/A'),
                'vehicle': item.get('park', 'N/A'),
                'info': item.get('content', 'N/A')
            }
            lodge_data.append(lodge)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        try:
            url1 = 'http://localhost:8222/api/travel'
            headers = {"Content-Type": "application/json"}
            response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
            if response.status_code == 200:  # 응답 확인
                print('데이터 전송 성공')
            else:
                logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        except Exception as e:
            logging.error(f"데이터 전송 예외 발생: {str(e)}")
# HTML 템플릿을 사용하여 결과를 반환
        html_template = """
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {% for lodge in lodge_data %}
                    <h4>tname : {{ lodge.tname }}</h2>
                    <p>tcategory : 숙박</p>
                    <p>taddr : {{ lodge.taddr }}</p>
                    <p>info : {{ lodge.info }}</p>
                    <p>phone : {{ lodge.phone }}</p>
                    <p>time : {{ lodge.time }}</p>
                    <p>homepage : {{ lodge.homepage }}</p>
                    <p>vehicle : {{ lodge.vehicle }}</p>
                    <p>timage : 
                        {% if lodge.timage %}
                            <img src="{{ lodge.timage }}" alt="맛집 이미지">
                        {% else %}
                        {% endif %}
                    </p><hr>
                {% endfor %}
            </body>
            </html>
            """
        return render_template_string(html_template, lodge_data=lodge_data)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500
# 성공!

# 경상남도 진주시_숙박시설
# 데이터 포맷 : JSON
def get_lodge_jjs():
    url = 'https://www.jinju.go.kr/openapi/tour/lodging.do'
# url 잘 나옴
    try:
        # HTTP GET 요청
        response = requests.get(url)
        data = response.json()
        lodges = data.get('results', [])
        lodge_data = []
        for item in lodges:
            timage = item.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = item.get("address", "")
            if not taddr.startswith("경상남도"):
                taddr = "경상남도 " + taddr
            # 숙박 데이터 추가
            lodge = {
                "tname": item.get("name", "N/A"),
                "tcategory": "숙박",
                "taddr": taddr,
                "homepage": item.get("homepage", "N/A"),
                "phone": item.get("phone", "N/A"),
                "time": item.get("checktime", "N/A"),
                "vehicle": item.get("park", "N/A"),
                "info": item.get("content", "N/A"),
                "guide": item.get("information", "N/A"),
                "timage": timage
            }
            lodge_data.append(lodge)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
# HTML 템플릿 생성 및 데이터 렌더링
        template = """
            <!doctype html>
            <html lang="ko">
              <head>
                <meta charset="utf-8">
              </head>
              <body>
                <h4>진주 숙박 정보</h4>
                {% for lodge in lodges %}
                  <p>tname : {{ lodge.tname }}</h2>
                  <p>tcategory : 숙박</p>
                  <p>taddr : {{ lodge.taddr }}</p>
                  <p>homepage : {{ lodge.homepage }}</p>
                  <p>phone : {{ lodge.phone }}</p>
                  <p>time : {{ lodge.time }}</p>
                  <p>vehicle : {{ lodge.vehicle }}</p>
                  <p>info : {{ lodge.info }}</p>
                  <p>guide : {{ lodge.guide }}</p>
                  <p>timage : <img src="{{ lodge.timage }}" alt="숙박업소 이미지"></p><hr>
                {% endfor %}
              </body>
            </html>
            """
        return render_template_string(template, lodges=lodge_data)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500

# 전북특별자치도_관광지숙박 정보
# 데이터 포맷 : XML
def get_lodge_jb():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)

# 전라남도_전남 숙박 정보
# 데이터 포맷 : XML
def get_lodge_jn():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)

# 충청남도_대표 숙박업소
# 데이터 포맷 : XML
def get_lodge_ccnd():
    url = 'https://tour.chungnam.go.kr/_prog/openapi/?func=stay&start=1&end=9708'
    try:
# HTTP GET 요청
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        lodge = soup.find_all('item')
        lodge_data = []
        for item in lodge:
            addr_text = item.find('addr').text.strip().replace('충남', '충청남도') if item.find('addr') else 'N/A'
            timage = item.find('list_img').text.strip() if item.find('list_img') else ''
            if timage.endswith('thm_'):
                timage = ''  # 이미지 정보가 없는 것으로 보고 출력하지 않음
            lodge = {
                'tname': item.find('nm').text.strip() if item.find('nm') else '',
                'taddr': addr_text,
                'tcategory': '숙박',
                'timage': timage,
                'phone': item.find('tel').text.strip() if item.find('tel') else '',
                'homepage': item.find('h_url').text.strip() if item.find('h_url') else '',
                'info': item.find('desc').text.strip() if item.find('desc') else ''
            }
            lodge_data.append(lodge)
# 스프링 부트 RestController 엔드포인트 URL
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(lodge_data), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
#             return Response("Failed to send data to the external API", status=500)
        template = """
            <!doctype html>
            <html lang="ko">
              <head>
                <meta charset="utf-8">
              </head>
              <body>
                <h4>충청남도 숙박 정보</h4>
                {% for lodge in lodge_data %}
                  <p>tname : {{ lodge.tname }}</h2>
                  <p>tcategory : 숙박</p>
                  <p>taddr : {{ lodge.taddr }}</p>
                  <p>phone : {{ lodge.phone }}</p>
                  <p>homepage : {{ lodge.homepage }}</p>
                  <p>info : {{ lodge.info }}</p>
                  <p>timage : <img src="{{ lodge.timage }}" alt="숙박업소 이미지"></p><hr>
                {% endfor %}
              </body>
            </html>
            """
        return render_template_string(template, lodge_data=lodge_data)
    except Exception as e:
        return f"Error: {str(e)}", 500
