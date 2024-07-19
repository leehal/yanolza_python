import requests
from bs4 import BeautifulSoup
import json
import logging
from flask import Flask, jsonify, request, render_template_string, Response, Blueprint
import xmltodict
import urllib.parse
import time

# 행정안전부_통계연보_자전거도로 현황 : API 신청 중

# 한국문화정보원_방방곳곳 트래킹 안내 서비스
# https://www.culture.go.kr/data/openapi/openapiView.do?id=372&category=I&gubun=B#/default/%EC%9A%94%EC%B2%AD%EB%A9%94%EC%8B%9C%EC%A7%80_Get
# 데이터 포맷 : JSON+XML
cache = {}  # 트래킹 전용
tracking_bp = Blueprint('tracking', __name__)
@tracking_bp.route('/api/tracking', methods=['GET'])
def get_tracking():
    url = 'http://api.kcisa.kr/openapi/service/rest/convergence2017/conver2?serviceKey=9326ebba-fc9b-4a54-93f2-55a4b85088ed&numOfRows=4175&pageNo=1'
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류가 발생했는지 확인
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        tracking_data_list = []
        for item in items:
            tracking_data = {
                'tname': item.find('title').text if item.find('title') else '',
                'tcategory': "관광",
                'info': item.find('description').text if item.find('description') else '',
                'guide': item.find('alternativeTitle').text if item.find('alternativeTitle') else '',
                'taddr': item.find('spatial').text if item.find('spatial') else '',
            }
            tracking_data_list.append(tracking_data)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url1, data=json.dumps(tracking_data_list), headers=headers)
            if response.status_code == 200:  # 응답 확인
                print('데이터 전송 성공')
            else:
                logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        except Exception as e:
            logging.error(f'API 전송 중 오류 발생: {str(e)}')
        cache['tracking'] = tracking_data_list  # 응답을 캐시에 저장
    except requests.exceptions.RequestException as e:
        if 'tracking' in cache:
            return json.dumps({"error": str(e), "cached_response": cache['tracking']}, ensure_ascii=False)
        return json.dumps({"error": f"Failed to fetch data: {e}"}, ensure_ascii=False)
    if not tracking_data_list:
        return json.dumps({"error": "Invalid response structure from external API"}, ensure_ascii=False)
    result_str = "\n\n".join([ # 각 항목을 문자열로 변환하고 줄바꿈 추가
        f"tname : {item['tname']}\ninfo : {item['info']}\nguide : {item['guide']}\ntaddr : {item['taddr']}\n"
        for item in tracking_data_list
    ])
    return Response(result_str, mimetype='text/plain')
# 성공

# 국토교통부_자전거길(WMS/WFS) : 인증키만 받았고 어떻게 해야 할지 모르겠음
def get_bicycle():
    # GET Param 방식 요청
    API_KEY = '85B430D8-8DB5-3639-BB8A-7C594890F746' # 만료일 2024년 12월 25일
    API_KEY_decode = requests.utils.unquote(API_KEY)
    # 요청 주소 및 요청 변수 지정(공공데이터포털 - 데이터찾기 - V월드)
    url = ''
    # 한 페이지에 포함된 결과 수
    num_of_rows = 6
    # 페이지 번호
    page_no = 1
    # 응답 데이터 형식 지정
    data_type = 'JSON'
    req_parameter = {'serviceKey': API_KEY_decode,
                     'pageNo': page_no, 'numOfRows': num_of_rows,
                     'dataType': data_type
    }