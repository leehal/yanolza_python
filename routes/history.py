import requests
from bs4 import BeautifulSoup
import json
import re
import logging
from flask import Flask, jsonify, request, render_template_string, Response
import html
import xmltodict
import urllib.parse

# 독립기념관 국내 독립운동사적지 정보 DB (https://search.i815.or.kr/apiDomesitc.do)
# 데이터 포맷 : XML
def get_history_im():
    try:
        url = 'https://search.i815.or.kr/openApiData.do?type=2' # url 잘 나왔음
        response = requests.get(url) # HTTP GET 요청
        if response.status_code != 200:
            return Response("Failed to retrieve data from API", status=500)
        soup = BeautifulSoup(response.text, "xml")
        result_list = [] # 결과를 담을 리스트
        for loc in soup.select("item"):
            tname = loc.select_one('subject').string if loc.select_one('subject') else ""
            tcategory = "관광"
            guide = f"{loc.select_one('define').string if loc.select_one('define') else ''}. {loc.select_one('research').string if loc.select_one('research') else ''} / {loc.select_one('situation').string if loc.select_one('situation') else ''}"
            address_roadname = loc.select_one('addressRoadname')
            address = loc.select_one('address')
            if address_roadname and address_roadname.string:
                taddr = address_roadname.string
            elif address and address.string:
                taddr = address.string
            else:
                taddr = ""
            taddr = taddr.replace("충남", "충청남도").replace("전북", "전라북도")
            info = loc.select_one('content')
            if info:
                info_text = info.decode_contents()
                info_text = re.sub(r'&lt;!\[CDATA\[(.*?)]]', r'\1', info_text, flags=re.DOTALL)
                info_text = re.sub(r'\s+', ' ', info_text).strip()
            else:
                info_text = ""
            history_item = { # 딕셔너리 생성
                "tname": tname,
                "tcategory": tcategory,
                "guide": guide,
                "taddr": taddr,
                "info": info_text
            }
            result_list.append(history_item) # 리스트에 추가
    # 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(result_list), headers=headers)
        if response.status_code == 200: # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
            return Response("Failed to send data to the external API", status=500)
# JSON 응답 생성
        return Response(json.dumps(result_list, ensure_ascii=False, indent=2), mimetype='application/json')
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return Response("Failed to connect to the external API", status=500)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return Response("An error occurred while processing the data", status=500)
# 성공!

# 인천 개항장 역사/문화 시설 정보 조회(https://api.incheoneasy.com/front/apiDetail.do)
# 데이터 포맷 : JSON
def get_open_port_ic():
    url = 'https://api.incheoneasy.com/api/histcul/installationInfo?accessToken=kTQFdTMGNDRCZTMEFTQChDNyUENGRTM4I0QBhDRxQkN'
    try:
        # JSON 데이터 가져오기
        response = requests.get(url)
        response.raise_for_status()  # HTTP 상태 코드가 200이 아닌 경우 예외 발생
        # HTML 엔티티 디코딩
        response_text = response.text
        data = json.loads(response_text.replace('&quot;', '"').replace('&#034;', '"'))
        # 필요한 데이터 추출하여 ports 리스트에 저장
        ports = data.get('dataList', [])
        ports_data = []
        for item in ports:
            phone = item.get('trrsrtTelNo', 'N/A')
            if phone == '000-0000-0000' or '000-000-0000':
                phone = ''  # 빈 문자열로 설정
            port = {
                'tname': item.get('trrsrtNm', 'N/A'),
                'taddr': item.get('trrsrtAddr', 'N/A'),
                'tcategory': '관광',
                'phone': phone,
                'time': item.get('trrsrtBsnTimeCn', 'N/A')
            }
            ports_data.append(port)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(ports_data), headers=headers)
        if response.status_code == 200:  # 응답 확인
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        # HTML 템플릿을 사용하여 결과를 반환
        html_template = """
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {% for port in ports %}
                    <h4>tname : {{ port.tname }}</h2>
                    <p>tcategory : 관광</p>
                    <p>taddr : {{ port.taddr }}</p>
                    <p>phone : {{ port.phone }}</p>            
                    <p>time : {{ port.time }}</p><hr>
                {% endfor %}
            </body>
            </html>
        """
        return render_template_string(html_template, ports=ports_data)
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", 500
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response - {str(e)}", 500
# 성공!

# 문화체육관광부_역사가 있는 여행 이야기 (적합한 내용의 API 맞는지 검토 결과 아닌 걸로 판명됨)
# https://www.culture.go.kr/data/openapi/openapiView.do?id=525&keyword=%EC%97%AD%EC%82%AC%EA%B0%80&searchField=all&gubun=A
# 데이터 포맷 : JSON+XML
def get_history_trip():
    API_KEY = 'ce2eb866-66a0-4592-a9f5-6ccfdb5393fb'
    API_KEY_decode = requests.utils.unquote(API_KEY)
    url = 'http://api.kcisa.kr/openapi/service/rest/convergence2019/getConver10'
    req_parameter = {'serviceKey': API_KEY_decode}
# 요청 및 응답
    try:
        response = requests.get(url, params=req_parameter)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making a request: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
# JSON 형태로 응답받은 데이터를 딕셔너리로 변환
    dict_data = response.json()
# 출력을 이쁘게 하기 위해 json.dumps()를 사용하여 들여쓰기(indent) 옵션 지정
    print(json.dumps(dict_data, indent=2))
# 딕셔너리 데이터를 분석하여 원하는 데이터를 추출
    history_items = dict_data['response']['body']['items']['item']
# response 안의 body 안의 items 안의 item
    history_data = {}
    for k in range(len(history_items)):
        history_item = history_items[k]
        properties = history_item['properties']
        if history_item['category'] == 'T1H':  # 자료구분코드 = 항목값
            print(f"[ 현재 기온 : {obsrValue} ]")
            history_data['tmp'] = f"{obsrValue}"  # 화면에 보이는 이름
        elif history_item['category'] == 'REH':
            print(f"[ 현재 습도 : {obsrValue} ]")
            history_data['hum'] = f"{obsrValue}"
        elif history_item['category'] == 'RN1':
            print(f"[ 1시간 강수량 : {obsrValue} ]")
            history_data['pre'] = f"{obsrValue}"
        elif history_item['category'] == 'REH':
            print(f"[ 현재 습도 : {obsrValue} ]")
            history_data['hum'] = f"{obsrValue}"
        elif history_item['category'] == 'RN1':
            print(f"[ 1시간 강수량 : {obsrValue} ]")
            history_data['pre'] = f"{obsrValue}"
    # 딕셔너리를 JSON 형태로 변환
    json_history = json.dumps(history_data, ensure_ascii=False, indent=4)
    return json_history