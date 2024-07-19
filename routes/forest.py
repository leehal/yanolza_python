import requests
from bs4 import BeautifulSoup
import json
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import urllib.parse
import re

# 산림청_숲에 사는 식물 정보(산림문화·휴양정보) (https://www.data.go.kr/data/3044607/openapi.do)
# 데이터 포맷 : XML
def get_plant():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)
    url = f"http://api.forest.go.kr/openapi/service/cultureInfoService/fStoryOpenAPI?serviceKey={API_KEY_decode}"
# HTTP GET 요청
    response = requests.get(url)
    if response.status_code != 200:
        return Response("Failed to retrieve data from API", status=500)
# 응답 데이터 출력 (디버깅 목적)
    print(response.text)
# XML 파싱
    soup = BeautifulSoup(response.text, "xml")
    output = ""
    for loc in soup.select("item"):
        fskname = loc.select_one('fskname')
        fsinhabit = loc.select_one('fsinhabit')
        fsguide = loc.select_one('fsguide')
        if fskname and fsinhabit and fsguide:
            output += f"<h3>식물명 : {fskname.string}</h3>"
            output += f"서식 장소 : {fsinhabit.string}</br>"
            output += f"안내 : {fsguide.string}</br>"
    if not output:
        return Response("No data found", status=204)
# HTML 응답 생성
    return Response(output, mimetype='text/html')
# 성공!

# 산림청_숲서비스 및 둘레길 정보
# https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15002725
# 데이터 포맷 : XML
def get_trail():
# GET Param 방식 요청
# API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
# 요청 주소(마이페이지 - API신청 - 활용신청 현황 - 산림청_숲서비스 및 둘레길 정보 - 개발계정 상세보기 - 활용신청 상세기능정보 - 확인 - 미리보기)
    url = 'http://api.forest.go.kr/openapi/service/trailInfoService/getforestservice?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&pageNo=1&numOfRows=26'
# 한 페이지에 포함된 결과 수(num_of_rows) = 26
# 요청 및 응답
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making a request: {e}")
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False), mimetype='application/json')
    try:
        dict_data = response.json()
    except json.JSONDecodeError:
        soup = BeautifulSoup(response.content, 'xml') # XML 파서 사용
        items = soup.find_all('item')
        result_list = []
        for item in items:
            course = item.find('dullegilvia').text.strip() if item.find('dullegilvia') else ""
            if '폐쇄' in course:
                continue  # course에 '폐쇄'가 포함되어 있으면 출력 X
            tname_start = item.find('dullegilsections').text.strip() if item.find('dullegilsections') else ""
            tname_end = item.find('dullegilsectione').text.strip() if item.find('dullegilsectione') else ""
            tname = f"{tname_start} - {tname_end} 둘레길"
            fir_co = course.split(' -')[0].strip() if ' -' in course else ""
# info에서 '전라', '경상'으로 시작하는 글자 추출
            info = item.find('dullegilintro').text.strip() if item.find('dullegilintro') else ""
            guide = item.find('dullegildetailintro').text.strip() if item.find('dullegildetailintro') else ""
            shared_words = set(tname_start.split()) & set(fir_co.split())
            shared_word = list(shared_words)[0] if shared_words else None
            if re.match(r'^(전라|경상)', info):
                if shared_word and shared_word in info:
                    match = re.search(r'(전라|경상).*?' + re.escape(tname_start), info)
                    if match:
                        taddr = match.group(0)[:18]
                    else:
                        taddr = info[:10]
                else:
                    taddr = info[:15]
            else:
                if tname_start == fir_co:
                    if len(tname_start) == 2:
                        taddr = "전라남도 구례군 토지면 송정리"
                    elif len(tname_start) == 3:
                        taddr = "경상남도 하동군 하동읍"
                elif len(tname_start) < len(fir_co):
                    if len(fir_co) >= 8:
                        taddr = "경상남도 하동군 적량면 동촌길 삼화실안내소"
                    elif len(fir_co) >= 5:
                        taddr = "경상남도 산청군 단성면 어천리"
                # else:
                #     taddr = "경상남도 산청군 시천면 원리교"
            trail_item = {
                "tname": tname,
                "tcategory": "관광",
                "taddr": taddr,
                "course": course,
                "info": info,
                "guide": guide
            }
            result_list.append(trail_item)
# 스프링 부트 RestController 엔드포인트 URL
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(result_list), headers=headers)
#         if response.status_code == 200: # 응답 확인
#                 print('데이터 전송 성공')
#         else:
#                 print('데이터 전송 실패')
        if result_list:
            result_str = "\n\n".join([
                f"tname : {item['tname']}\ntcategory : 관광\ntaddr : {item['taddr']}\ncourse : {item['course']}\ninfo : {item['info']}\nguide : {item['guide']}"
                for item in result_list
            ])
        else:
            result_str = "No data available"
        return Response(result_str, mimetype='text/plain')
# 성공