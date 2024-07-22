import requests
from bs4 import BeautifulSoup
import json
import logging
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import urllib.parse

 # 경기도_낚시터 현황
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=8M2AW008ZZ275DEX8997536167&infSeq=3
# 데이터 포맷 : XML
def get_fishing_ggd():
    url = 'https://openapi.gg.go.kr/FishingPlaceStatus?KEY=4fc8ecb251d64ad7a7b588256d4e7145&Type=xml&pIndex=1&pSize=310'
    # URL 잘 나오고 있음
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return Response(f"Error: {str(e)}", status=500)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('row')
    fishing_data = []
    for item in items:
        tname = item.find('FISHPLC_NM').text if item.find('FISHPLC_NM') else '정보없음'
        # tname에 '낚시'라는 말이 없으면 ' 낚시터' 추가
        if '낚시' not in tname:
            tname += ' 낚시터'
        road_addr = item.find('REFINE_ROADNM_ADDR')
        lot_addr = item.find('REFINE_LOTNO_ADDR')
        taddr = road_addr.text if road_addr and road_addr.text.strip() else (lot_addr.text if lot_addr else '정보없음')
        tprice = item.find('UTLZ_CHRG').text if item.find('UTLZ_CHRG') else 0
        if tprice.endswith('000'):  # tprice가 '000'으로 끝나는 경우 '원' 붙임
            tprice += '원'
        if '응답거부' in tprice:
            tprice = ''
        if '휴업' in tprice or '수리중' in tprice:  # tprice에 '휴업, 수리중'이 포함되어 있으면 출력 X
            continue
        fishing = {
            'tname': tname,
            'tcategory': "관광",
            'taddr': taddr,
            'tprice': tprice
        }
        fishing_data.append(fishing)
# 스프링 부트 RestController 엔드포인트 URL
    url1 = 'http://localhost:8222/api/travel'
    headers = {"Content-Type": "application/json"}
    response = requests.post(url1, data=json.dumps(fishing_data), headers=headers)
    if response.status_code == 200:
        print('데이터 전송 성공')
    else:
        logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
    response_text = ""
    for data in fishing_data:
        response_text += f"tname : {data['tname']}\n"
        response_text += f"tcategory : 관광\n"
        response_text += f"taddr : {data['taddr']}\n"
        response_text += f"tprice : {data['tprice']}\n\n"
    return Response(response_text, mimetype='text/plain')

# (경기도) 온천 현황
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=2F62SUW995PMYQ1223B311745685&infSeq=3&order=&loc=
# 데이터 포맷 : XML
def get_hot_spring():
# GET Param 방식 요청
    url = 'https://openapi.gg.go.kr/HotSpringStatus?KEY=c8e63555aeb3495e8ab0f6e0dca54651&Type=xml&pIndex=1&pSize=47'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching hot spring data: {str(e)}")
        return Response(f"Error: {str(e)}", status=500)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('row')
    place_data = []
    for item in items:
        tname = item.find('HOTSPA_NM').text if item.find('HOTSPA_NM') else '정보없음'
        if '스파' not in tname and '온수' not in tname:
            tname += ' 온천'
        road_addr = item.find('REFINE_ROADNM_ADDR')
        lot_addr = item.find('REFINE_LOTNO_ADDR')
        taddr = road_addr.text if road_addr and road_addr.text.strip() else (lot_addr.text if lot_addr else '정보없음')
        if not taddr:
            continue
        info = item.find('INGRDNT_NM').text if item.find('INGRDNT_NM') else '정보없음'
        info = f"성분명 : {info}"
        temp = item.find('HOTSPRG_TP').text if item.find('HOTSPRG_TP') else '정보없음'
        depth = item.find('HOTSPRG_DPH').text if item.find('HOTSPRG_DPH') else '정보없음'
        guide = f"온천온도 : {temp} / 온천심도 : {depth}"
        hot_spring = {
            'tname': tname,
            'tcategory': "관광",
            'taddr': taddr,
            'info': info,
            'guide': guide
        }
        place_data.append(hot_spring)
# 스프링 부트 RestController 엔드포인트 URL
    url1 = 'http://localhost:8222/api/travel'
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url1, data=json.dumps(place_data), headers=headers)
        if response.status_code == 200:
            logging.info('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
    except requests.exceptions.RequestException as e:
        logging.error(f'데이터 전송 예외 발생: {str(e)}')
    response_text = ""
    for data in place_data:
        response_text += f"tname : {data['tname']}\n"
        response_text += f"tcategory : 관광\n"
        response_text += f"taddr : {data['taddr']}\n"
        response_text += f"guide : {data['guide']}\n"
        response_text += f"info : {data['info']}\n\n"
    return Response(response_text, mimetype='text/plain')

# 레이어는 url에 각각 요청해야 하며 xml/json 방식으로 호출 가능한 레이어는 일부만 가능
def get_beach():
# GET Param 방식 요청
# 요청 주소 및 요청 변수 지정(공공데이터포털 - 데이터찾기 - 레저관광 검색 - 오픈API상세 - URL - 오픈API신청)
    layer_1 = ['VI_ZN_CYFST'] # 국가어항
    layer_2 = ['TB_SAILER_5030103', 'TB_SAILER_5030104', 'TB_SAILER_5030102', 'TB_SAILER_5030105'] # 국가무역항, 지방무역항, 지방항, 연안항
    all_layers = layer_1 + layer_2
    all_beach_data = []
    for layer in all_layers:
        url = f'http://www.khoa.go.kr/oceanmap/otmsInfoApi.do?ServiceKey=4D048B473A8EABF8A7B7F2C54&Layer={layer}&numOfRows=245'
# 한 페이지에 포함된 결과 수
# num_of_rows = 117, 18, 17, 245, 30
# result_type = XML OR JSON
        try:
            response = requests.get(url)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            try:
                dict_data = response.json() # JSON 형태의 응답을 시도하고 실패 시 XML로 처리
                logging.info(f"Received JSON response for {layer}: {json.dumps(dict_data, ensure_ascii=False, indent=4)}")
                if 'response' in dict_data and 'body' in dict_data['response'] and 'items' in dict_data['response']['body']:
                    beach_items = dict_data['response']['body']['items']['item']
                else:
                    logging.error(f"Unexpected JSON structure for {layer}")
                    continue
            except json.JSONDecodeError:
                soup = BeautifulSoup(response.content, 'xml')
                logging.info(f"Received XML response for {layer}: {soup.prettify()}")
                beach_items = soup.find_all('item')
            for item in beach_items:
                taddr = item.find('sigunguNm').text if item.find('sigunguNm') else ""
                layer1tname = item.find('ZONE_NM').text if item.find('ZONE_NM') else ""
                layer2tname = item.find('name').text if item.find('name') else ""
                info = ""
                guide = ""
                tname = ""
                if layer in layer_2:
                    taddr = f"{taddr} {layer2tname}"
                    tname = layer2tname
                    info = item.find('introdu').text if item.find('introdu') else ""
                elif layer in layer_1:
                    taddr = f"{taddr} {layer1tname}"
                    tname = layer1tname
                    coast = item.find('COAST').text if item.find('COAST') else ""
                    nfp = item.find('CYFST_CD').text if item.find('CYFST_CD') else ""
                    guide = f"해안 : {coast} / {nfp}"
                item_data = {
                    'taddr': taddr,
                    'info': info,
                    'tname': tname,
                    'guide': guide
                }
                item_data = {k: v for k, v in item_data.items() if v}
                if item_data:
                    all_beach_data.append(item_data)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {layer}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing data from {layer}: {str(e)}")
# 스프링 부트 RestController 엔드포인트 URL
    url1 = 'http://localhost:8222/api/travel'
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url1, data=json.dumps(all_beach_data), headers=headers)
        if response.status_code == 200:
            print('데이터 전송 성공')
        else:
            logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
    except requests.exceptions.RequestException as e:
        logging.error(f"데이터 전송 예외 발생: {str(e)}")

        # JSON 형태로 변환하여 반환
    json_beach = json.dumps(all_beach_data, ensure_ascii=False, indent=4)
    return Response(json_beach, content_type='application/json')
# 성공!