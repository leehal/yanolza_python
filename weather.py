import json
import requests
from bs4 import BeautifulSoup
from flask import request
import datetime
from urllib.parse import unquote_plus
import xml.etree.ElementTree as ET
from urllib.parse import unquote




def get_nearest_base_time():
    """
    현재 시간을 기준으로 가장 가까운 발표 시간(base_time)을 계산하는 함수.
    """
    now = datetime.datetime.now()
    one_day_ago = now - datetime.timedelta(days=1)
    current_time = int(now.strftime('%H%M'))  # 현재 시간을 분 단위로 변환

    # 발표 시간 설정: 현재 시간보다 이전의 발표 시간 중 가장 최근의 것을 찾기 위해
    if current_time < 210:  # 00:00 이전
        base_time = '2300'  # 전날 23시
        base_date = one_day_ago.strftime('%Y%m%d')
    elif current_time < 510:  # 02:00 이전
        base_time = '0200'  # 당일 02시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 810:  # 05:00 이전
        base_time = '0500'  # 당일 05시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 1110:  # 08:00 이전
        base_time = '0800'  # 당일 08시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 1410:  # 11:00 이전
        base_time = '1100'  # 당일 11시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 1710:  # 14:00 이전
        base_time = '1400'  # 당일 14시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 2010:  # 17:00 이전
        base_time = '1700'  # 당일 17시
        base_date = now.strftime('%Y%m%d')
    elif current_time < 2310:  # 20:00 이전
        base_time = '2000'  # 당일 20시
        base_date = now.strftime('%Y%m%d')
    else:  # 23:00 이후
        base_time = '2300'  # 당일 23시
        base_date = now.strftime('%Y%m%d')

    return base_date, base_time


def get_weather2():
    """
    GET 요청을 받아 기상청 API를 사용하여 날씨 정보를 가져오는 함수.
    """
    try:
        # 가장 가까운 발표 시간을 계산
        base_date, base_time = get_nearest_base_time()

        # one_day_ago를 이용하여 TMN과 TMX를 전일 기준으로 조회
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        base_date = one_day_ago.strftime('%Y%m%d')

        # 요청 변수 설정
        nx_val = request.args.get('x', default=None, type=None)
        ny_val = request.args.get('y', default=None, type=None)
        API_KEY = 'MpgyoKFMLkzjZB8BpGH5Vh8SxaJwI%2FxWNUtX8iyrh%2F6lOtI3iPeHAKRrIjt2SskZwwq45Z%2FFoxXNIZCAeIJN1w%3D%3D'
        API_KEY_decode = unquote_plus(API_KEY)
        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
        num_of_rows = 1000  # 테스트용으로 작은 값 설정 (실제 사용 시 조정 필요)
        page_no = 1
        data_type = 'XML'

        # API 요청 파라미터 설정
        req_parameter = {
            'serviceKey': API_KEY_decode,
            'nx': nx_val,
            'ny': ny_val,
            'base_date': base_date,
            'base_time': base_time,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'dataType': data_type
        }

        # API 요청 보내기
        r = requests.get(url, params=req_parameter)
        r.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # XML 데이터를 파싱하여 처리
        root = ET.fromstring(r.text)

        # 에러 처리
        if root.find('.//errMsg') is not None:
            err_msg = root.find('.//errMsg').text
            auth_msg = root.find('.//returnAuthMsg').text
            reason_code = root.find('.//returnReasonCode').text
            error_response = {
                "error": err_msg,
                "authMsg": auth_msg,
                "reasonCode": reason_code
            }
            return json.dumps(error_response, ensure_ascii=False)

        # 정상적인 데이터 처리
        weather_items = root.findall('.//item')
        weather_data = {}

        def map_sky_code(sky_code):
            if '0' <= sky_code <= '5':
                return "맑음"
            elif '6' <= sky_code <= '8':
                return "구름 많음"
            elif '9' <= sky_code <= '10':
                return "흐림"
            else:
                return "알 수 없음"

        now = datetime.datetime.now()
        current_date = now.strftime('%Y%m%d')
        current_time = int(now.strftime('%H%M'))

        nearest_time = None
        for weather_item in weather_items:
            fcstDate = weather_item.find('.//fcstDate').text  # 예보 날짜
            fcstTime = int(weather_item.find('.//fcstTime').text)  # fcstTime을 정수형으로 변환
            fcstValue = weather_item.find('.//fcstValue').text
            category = weather_item.find('.//category').text

            # 현재 날짜와 23시까지의 데이터만 처리
            if fcstDate == current_date and fcstTime >= current_time and fcstTime <= 2300:
                if nearest_time is None or abs(fcstTime - current_time) < abs(nearest_time - current_time):
                    nearest_time = fcstTime

            if fcstDate == current_date and fcstTime == nearest_time:
                if category == 'TMP':  # 기온
                    weather_data['tmp'] = f"{fcstValue}℃"
                elif category == 'TMN':  # 최저기온
                    weather_data['min_temp'] = f"{fcstValue}℃"
                elif category == 'TMX':  # 최고기온
                    weather_data['max_temp'] = f"{fcstValue}℃"
                elif category == 'REH':  # 습도
                    weather_data['hum'] = f"{fcstValue}%"
                elif category == 'POP':  # 강수확률
                    weather_data['pop'] = f"{fcstValue}%"
                elif category == 'PTY':  # 강수 형태
                    if fcstValue == '0':
                        weather_data['pty'] = "none"
                    elif fcstValue == '1':
                        weather_data['pty'] = "비"
                    elif fcstValue == '2':
                        weather_data['pty'] = "비/눈"
                    elif fcstValue == '3':
                        weather_data['pty'] = "눈"
                    elif fcstValue == '4':
                        weather_data['pty'] = "소나기"
                elif category == 'SKY':  # 하늘 상태
                    weather_data['sky'] = map_sky_code(fcstValue)
                elif category not in weather_data and category not in ['TMP', 'TMN', 'TMX', 'REH', 'POP', 'PTY', 'SKY']:
                    weather_data[category.lower()] = fcstValue

                print(
                    f"예보 날짜: {fcstDate}, 예보 시간: {fcstTime}, 카테고리: {category}, 값: {fcstValue}, base_date:{base_date},base_time:{base_time}")

        for weather_item in weather_items:
            fcstDate = weather_item.find('.//fcstDate').text  # 예보 날짜

            fcstValue = weather_item.find('.//fcstValue').text
            category = weather_item.find('.//category').text

            if fcstDate == current_date:
                if category == 'TMX':  # 최고기온
                    weather_data['max_temp'] = f"{fcstValue}"
                elif category == 'TMN':  # 최저기온
                    weather_data['min_temp'] = f"{fcstValue}"

            # TMX와 TMN 정보가 없을 경우에 대한 처리
        if 'max_temp' not in weather_data:
            weather_data['max_temp'] = 'N/A'  # 최고기온 정보가 없을 경우 처리
        if 'min_temp' not in weather_data:
            weather_data['min_temp'] = 'N/A'  # 최저기온 정보가 없을 경우 처리

        # 딕셔너리를 JSON 형태로 변환, ensure_ascii=False를 설정하여 JSON에 유니코드 문자 포함
        json_weather = json.dumps(weather_data, ensure_ascii=False, indent=4)
        return json_weather

    except requests.exceptions.RequestException as e:
        error_message = {"error": str(e)}
        return json.dumps(error_message, ensure_ascii=False)

    except Exception as e:
        error_message = {"error": f"An error occurred: {e}"}
        return json.dumps(error_message, ensure_ascii=False)

