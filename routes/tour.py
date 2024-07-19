import requests
from bs4 import BeautifulSoup
import json
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import logging
from requests.adapters import HTTPAdapter
import ssl
import re
import urllib.parse

# 춘천시 정보가 화면에 출력이 안 되어 SSLContext를 명시적으로 설정했으며 개발 환경에서만 사용하는 것이 좋음
# 운영 환경에서는 SSL 인증서를 제대로 검증해야 함
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

# 충청남도_주요 관광정보
# 데이터 포맷 : XML
def clean_info_text(info_text): # 특수 문자 및 불필요한 태그 제거
    info_text = info_text.replace('&#039;', "'").replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('<div>', ' ').replace('</div>', ' ')
    info_text = re.sub(r'<span style="[^"]+">|</span>', '', info_text)
    info_text = info_text.replace('<p>', ' ').replace('</p>', ' ')
    info_text = re.sub(r'<a href="[^"]+"></a>', '', info_text)
    return info_text
def clean_guide_text(guide_text):
    return guide_text.replace('&#039;', "'")
def get_tour_ccnd():
    url = 'https://tour.chungnam.go.kr/_prog/openapi/?func=tour&start=1&end=50561'
# URL 잘 나오고 있음
    try:
        # HTTP GET 요청
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        tour = soup.find_all('item')
        tour_data = []
        for item in tour:
            info_text = item.find('desc').text.strip() if item.find('desc') else 'N/A'
            info_text = clean_info_text(info_text)
            guide_text = item.find('nm_sub').text.strip() if item.find('nm_sub') else 'N/A'
            guide_text = clean_guide_text(guide_text)
# taddr 필드의 '충남'을 '충청남도'로 변경
            addr_text = item.find('addr').text.strip().replace('충남', '충청남도') if item.find('addr') else 'N/A'
            tour = {
                'tname': item.find('nm').text.strip() if item.find('nm') else 'N/A',
                'taddr': addr_text,
                'tcategory': '관광',
                'timage': item.find('list_img').text.strip() if item.find('nm') else 'N/A',
                'phone': item.find('tel').text.strip() if item.find('tel') else 'N/A',
                'homepage': item.find('h_url').text.strip() if item.find('tel') else 'N/A',
                'guide': guide_text,
                'info': info_text
            }
            tour_data.append(tour)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(tour_data), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
            return Response("Failed to send data to the external API", status=500)
        template = """
        <!doctype html>
        <html lang="ko">
          <head>
            <meta charset="utf-8">
          </head>
          <body>
            <h4>충청남도 관광 정보</h4>
            {% for tour in tour_data %}
              <p>tname : {{ tour.tname }}</h2>
              <p>tcategory : 관광</p>
              <p>taddr : {{ tour.taddr }}</p>
              <p>phone : {{ tour.phone }}</p>
              <p>homepage : {{ tour.homepage }}</p>
              <p>guide : {{ tour.guide }}</p>
              <p>info : {{ tour.info }}</p>
              <p>timage : <img src="{{ tour.timage }}" alt="관광 이미지"></p><hr>
            {% endfor %}
          </body>
        </html>
        """
        return render_template_string(template, tour_data=tour_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

# 경기도_관광지 현황
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=1RLM5SEX28H22J8BP1L71055259&infSeq=3&order=&loc=&searchWord=%EA%B4%80%EA%B4%91%EC%A7%80+%ED%98%84%ED%99%A9#none
# 데이터 포맷 : XML
def get_tour_ggd():
# GET Param 방식 요청
    url = 'https://openapi.gg.go.kr/TOURESRTINFO?KEY=7e83009b327e4c3dba706401e2776f31&Type=xml&pIndex=1&pSize=56'
# 요청 및 응답
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')
    try:
        dict_data = xmltodict.parse(response.text)
# XML 구조 확인 후 올바르게 파싱
        if not dict_data.get('TOURESRTINFO', {}).get('head', {}).get('RESULT', {}).get('CODE') == 'INFO-000':
            return Response("error: Invalid API response", status=500, mimetype='text/plain')
        tour_items = dict_data['TOURESRTINFO']['row']
        tour_data = []
        for item in tour_items:
            taddr = item.get('REFINE_ROADNM_ADDR') or item.get('REFINE_LOTNO_ADDR', '')
            convnce_faclt_info = item.get('CONVNCE_FACLT_INFO', '').rstrip(' +') # 시설 정보 처리
            stayng_faclt_info = item.get('STAYNG_FACLT_INFO', '')
            recratn_faclt_info = item.get('RECRATN_FACLT_INFO', '')
            cultur_faclt_info = item.get('CULTUR_FACLT_INFO', '')
            info_parts = [
                convnce_faclt_info, stayng_faclt_info, recratn_faclt_info, cultur_faclt_info
            ]
# 값이 'N'인 항목 무시 및 값이 있는 항목만 추가
            info = ' + '.join(part for part in info_parts if part and part != 'N')
            data = {
                'tname': item.get('FACLT_NM'),
                'tcategory': '관광',
                'taddr': taddr,
                'info': info,
                'guide': item.get('TOURESRT_INFO', ''),
                'phone': item.get('MANAGE_INST_TELNO', '')
            }
            tour_data.append(data)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url1, data=json.dumps(tour_data), headers=headers)
            response.raise_for_status()  # 응답 상태 코드가 4xx나 5xx인 경우 예외 발생
            if response.status_code == 200:  # 응답 확인
                print('데이터 전송 성공')
            else:
                logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        except requests.exceptions.RequestException as e:
            logging.error(f'HTTP 요청 실패 : {str(e)}')
        except Exception as e:
            logging.error(f'데이터 전송 중 예외 발생 : {str(e)}')
        return jsonify(tour_data)
    except Exception as e:
        return Response(f"error: {str(e)}", status=500, mimetype='text/plain')
# 성공!

# 경상남도 김해시_관광정보
def get_tour_ghs():
    url = "http://www.gimhae.go.kr/openapi/tour/tourinfo.do"
# URL 잘 나오고 있음
    try:
# HTTP GET 요청
        response = requests.get(url)
        data = response.json()
        tour_list = []
        for loc in data["results"]:
            info = loc.get("content", "").replace("\r\n", " ")
            time = loc.get("usehour", "").replace("전화문의바람", "전화 문의 바람").replace("전화문의", "전화 문의")
            tprice = loc.get("fee", "").replace("전화문의바람", "전화 문의 바람").replace("전화문의", "전화 문의")
            vehicle = loc.get("parking", "").replace("전화문의바람", "전화 문의 바람").replace("전화문의", "전화 문의")
            timage = loc.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = loc.get("address", "").replace("경남", "경상남도")
            tour_info = {
                "tname": loc.get("name", ""),
                "tcategory": loc.get("category", ""),
                "taddr": taddr,
                "phone": loc.get("phone", ""),
                "homepage": loc.get("homepage", ""),
                "info": info,
                "tprice": tprice,
                "time": time,
                "timage": timage,
                "vehicle": vehicle
            }
            tour_list.append(tour_info)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(tour_list), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
            return Response("Failed to send data to the external API", status=500)
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            {% for tour in tour_list %}
                <h4>tname : {{ tour.tname }}</h2>
                <p>tcategory : 관광</p>
                <p>taddr : {{ tour.taddr }}</p>
                <p>homepage : {{ tour.homepage }}</p>
                <p>info : {{ tour.info }}</p>
                <p>phone : {{ tour.phone }}</p>
                <p>time : {{ tour.time }}</p>
                <p>vehicle : {{ tour.vehicle }}</p>
                <p>tprice : {{ tour.tprice }}</p>
                <p>timage : 
                    {% if tour.timage %}
                        <img src="{{ tour.timage }}" alt="관광명소 이미지">
                    {% else %}
                        이미지 없음
                    {% endif %}
                </p><hr>
            {% endfor %}
        </body>
        </html>
        """
        return render_template_string(html_template, tour_list=tour_list)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500


# 대구광역시_관광지(https://www.data.go.kr/data/3054892/openapi.do)
def get_tour_dgs():
     url = 'https://tour.daegu.go.kr/openapi-data/service/rest/getTourKorAttract/svTourKorAttract.do?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%252BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%252F8SFykfu4KO%252FpXu%252FSuRP3ig%253D%253D&pageNo=1&numOfRows=258&SG_APIM=2ug8Dm9qNBfD32JLZGPN64f3EoTlkpD8kSOHWfXpyrY'

# 강원도 춘천시_관광_관광지_데이터_조회_서비스(https://www.data.go.kr/data/15112144/openapi.do)
# 데이터 포맷 : JSON
def get_tour_ccs():
    url = 'https://apis.data.go.kr/4180000/cctour/getTourList?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&pageNo=1&numOfRows=5'
    s = requests.Session()
    s.mount('https://', SSLAdapter())
    # API 호출
    response = s.get(url)
    response.encoding = 'utf-8'
    if response.status_code == 200:
        data = response.json()
        items = data['data']
        tour_data = []
        for loc in items:
            guide = f"{loc['convenienceFacility']} + {loc['accommodations']} + {loc['amusementFacility']} + {loc['recreationalFacility']}"
            if loc.get('receptionFacility'):
                guide += f" + {loc['receptionFacility']}"
            if loc.get('supportFacility'):
                guide += f" + {loc['supportFacility']}"
            taddr = loc['newAddr'].replace('강원 ', '강원도 ')
            tour = {
                'tname': loc['tourNm'],
                'tcategory': '관광',
                'taddr': taddr,
                'guide': guide,
                'phone': f"{loc['managementNm']} : {loc['managementNum']}",
                'info': f"{loc['info']}"
            }
            tour_data.append(tour)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(tour_data), headers=headers)
        if response.status_code == 200: # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
            return Response("Failed to send data to the external API", status=500)
        return jsonify(tour_data)
    else:
        return jsonify({"error": "Failed to fetch data"}), response.status_code
# 성공