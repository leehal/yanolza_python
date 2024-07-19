import requests
from bs4 import BeautifulSoup
import json
import logging
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import urllib.parse

# 로거 설정
logging.basicConfig(level=logging.INFO)

SEOUL_API_URLS = [
# 1. 강남구 모범음식점 지정
    'http://openAPI.gangnam.go.kr:8088/56586a6766746a6435344e6369494b/xml/GnModelRestaurantDesignate/1/311/',
# 2. 강동구 모범음식점 지정
    'http://openapi.gd.go.kr:8088/56586a6766746a6435344e6369494b/xml/GdModelRestaurantDesignate/1/66/',
# 3. 강북구 모범음식점 지정
    'http://openapi.gangbuk.go.kr:8088/56586a6766746a6435344e6369494b/xml/GbModelRestaurantDesignate/1/80/',
# 4. 강서구 모범음식점 지정
    'http://openapi.gangseo.seoul.kr:8088/56586a6766746a6435344e6369494b/xml/GangseoModelRestaurantDesignate/1/129/',
# 5. 관악구 모범음식점 지정
    'http://openapi.gwanak.go.kr:8088/56586a6766746a6435344e6369494b/xml/GaModelRestaurantDesignate/1/121/',
# 6. 광진구 모범음식점 지정
    'http://openapi.gwangjin.go.kr:8088/56586a6766746a6435344e6369494b/xml/GwangjinModelRestaurantDesignate/1/131/',
# 7. 구로구 모범음식점 지정
    'http://openapi.guro.go.kr:8088/56586a6766746a6435344e6369494b/xml/GuroModelRestaurantDesignate/1/65/',
# 8. 금천구 모범음식점 지정
    'http://openapi.geumcheon.go.kr:8088/56586a6766746a6435344e6369494b/xml/GeumcheonModelRestaurantDesignate/1/39/',
# 9. 노원구 모범음식점 지정
    'http://openapi.nowon.go.kr:8088/56586a6766746a6435344e6369494b/xml/NwModelRestaurantDesignate/1/106/',
# 10. 도봉구 모범음식점 지정
    'http://openapi.dobong.go.kr:8088/56586a6766746a6435344e6369494b/xml/DobongModelRestaurantDesignate/1/48/',
# 11. 동대문구 모범음식점 지정
    'http://openapi.ddm.go.kr:8088/56586a6766746a6435344e6369494b/xml/DongdeamoonModelRestaurantDesignate/1/52/',
# 12. 동작구 모범음식점 지정
    'http://openapi.dongjak.go.kr:8088/56586a6766746a6435344e6369494b/xml/DjModelRestaurantDesignate/1/105/',
# 13. 마포구 모범음식점 지정
    'http://openapi.mapo.go.kr:8088/56586a6766746a6435344e6369494b/xml/MpModelRestaurantDesignate/1/182/',
# 14. 서대문구 모범음식점 지정
    'http://openapi.sdm.go.kr:8088/56586a6766746a6435344e6369494b/xml/SeodaemunModelRestaurantDesignate/1/138/',
# 15. 서초구 모범음식점 지정
    'http://openapi.seocho.go.kr:8088/56586a6766746a6435344e6369494b/xml/ScModelRestaurantDesignate/1/250/',
# 16. 성동구 모범음식점 지정
    'http://openapi.sd.go.kr:8088/56586a6766746a6435344e6369494b/xml/SdModelRestaurantDesignate/1/139/',
# 17. 성북구 모범음식점 지정
    'http://openapi.sb.go.kr:8088/56586a6766746a6435344e6369494b/xml/SbModelRestaurantDesignate/1/77/',
# 18. 송파구 모범음식점 지정
    'http://openapi.songpa.seoul.kr:8088/56586a6766746a6435344e6369494b/xml/SpModelRestaurantDesignate/1/70/',
# 19. 양천구 모범음식점 지정
    'http://openapi.yangcheon.go.kr:8088/56586a6766746a6435344e6369494b/xml/YcModelRestaurantDesignate/1/70/',
# 20. 영등포구 모범음식점 지정
    'http://openapi.ydp.go.kr:8088/56586a6766746a6435344e6369494b/xml/YdpModelRestaurantDesignate/1/88/',
# 21. 용산구 모범음식점 지정
    'http://openapi.yongsan.go.kr:8088/56586a6766746a6435344e6369494b/xml/YsModelRestaurantDesignate/1/133/',
# 22. 은평구 모범음식점 지정
    'http://openapi.ep.go.kr:8088/56586a6766746a6435344e6369494b/xml/EpModelRestaurantDesignate/1/205/',
# 23. 종로구 모범음식점 지정
    'http://openapi.jongno.go.kr:8088/56586a6766746a6435344e6369494b/xml/JongnoModelRestaurantDesignate/1/71/',
# 24. 중구 모범음식점 지정
    'http://openapi.junggu.seoul.kr:8088/56586a6766746a6435344e6369494b/xml/JungguModelRestaurantDesignate/1/129/',
# 25. 중랑구 모범음식점 지정
    'http://openapi.jungnang.seoul.kr:8088/56586a6766746a6435344e6369494b/xml/JungnangModelRestaurantDesignate/1/79/'
] # URL 잘 나오고 있음
def get_restaurant_seoul():
    # GET Param 방식 요청
    all_restaurant_data = []
# 요청 및 응답
    for url in SEOUL_API_URLS:
        try:
            response = requests.get(url)
            response.raise_for_status()
            dict_data = xmltodict.parse(response.content)
            restaurant_items = None
            if 'response' in dict_data:
                restaurant_items = dict_data['response'].get('row')
            elif 'GnModelRestaurantDesignate' in dict_data: # 1. 강남구
                restaurant_items = dict_data['GnModelRestaurantDesignate'].get('row')
            elif 'GdModelRestaurantDesignate' in dict_data: # 2. 강동구
                restaurant_items = dict_data['GdModelRestaurantDesignate'].get('row')
            elif 'GbModelRestaurantDesignate' in dict_data: # 3. 강북구
                restaurant_items = dict_data['GbModelRestaurantDesignate'].get('row')
            elif 'GangseoModelRestaurantDesignate' in dict_data: # 4. 강서구
                restaurant_items = dict_data['GangseoModelRestaurantDesignate'].get('row')
            elif 'GaModelRestaurantDesignate' in dict_data: # 관악구
                restaurant_items = dict_data['GaModelRestaurantDesignate'].get('row')
            elif 'GwangjinModelRestaurantDesignate' in dict_data: # 광진구
                restaurant_items = dict_data['GwangjinModelRestaurantDesignate'].get('row')
            elif 'GuroModelRestaurantDesignate' in dict_data: # 구로구
                restaurant_items = dict_data['GuroModelRestaurantDesignate'].get('row')
            elif 'GeumcheonModelRestaurantDesignate' in dict_data: # 금천구
                restaurant_items = dict_data['GeumcheonModelRestaurantDesignate'].get('row')
            elif 'NwModelRestaurantDesignate' in dict_data: # 노원구
                restaurant_items = dict_data['NwModelRestaurantDesignate'].get('row')
            elif 'DobongModelRestaurantDesignate' in dict_data: # 도봉구
                restaurant_items = dict_data['DobongModelRestaurantDesignate'].get('row')
            elif 'DongdeamoonModelRestaurantDesignate' in dict_data: # 동대문구
                restaurant_items = dict_data['DongdeamoonModelRestaurantDesignate'].get('row')
            elif 'DjModelRestaurantDesignate' in dict_data: # 동작구
                restaurant_items = dict_data['DjModelRestaurantDesignate'].get('row')
            elif 'MpModelRestaurantDesignate' in dict_data: # 마포구
                restaurant_items = dict_data['MpModelRestaurantDesignate'].get('row')
            elif 'SeodaemunModelRestaurantDesignate' in dict_data: # 서대문구
                restaurant_items = dict_data['SeodaemunModelRestaurantDesignate'].get('row')
            elif 'ScModelRestaurantDesignate' in dict_data: # 서초구
                restaurant_items = dict_data['ScModelRestaurantDesignate'].get('row')
            elif 'SdModelRestaurantDesignate' in dict_data: # 성동구
                restaurant_items = dict_data['SdModelRestaurantDesignate'].get('row')
            elif 'SbModelRestaurantDesignate' in dict_data: # 성북구
                restaurant_items = dict_data['SbModelRestaurantDesignate'].get('row')
            elif 'SpModelRestaurantDesignate' in dict_data: # 송파구
                restaurant_items = dict_data['SpModelRestaurantDesignate'].get('row')
            elif 'YcModelRestaurantDesignate' in dict_data: # 양천구
                restaurant_items = dict_data['YcModelRestaurantDesignate'].get('row')
            elif 'YdpModelRestaurantDesignate' in dict_data: # 영등포구
                restaurant_items = dict_data['YdpModelRestaurantDesignate'].get('row')
            elif 'YsModelRestaurantDesignate' in dict_data: # 용산구
                restaurant_items = dict_data['YsModelRestaurantDesignate'].get('row')
            elif 'EpModelRestaurantDesignate' in dict_data: # 은평구
                restaurant_items = dict_data['EpModelRestaurantDesignate'].get('row')
            elif 'JongnoModelRestaurantDesignate' in dict_data: # 종로구
                restaurant_items = dict_data['JongnoModelRestaurantDesignate'].get('row')
            elif 'JungguModelRestaurantDesignate' in dict_data: # 중구
                restaurant_items = dict_data['JungguModelRestaurantDesignate'].get('row')
            elif 'JungnangModelRestaurantDesignate' in dict_data: # 중랑구
                restaurant_items = dict_data['JungnangModelRestaurantDesignate'].get('row')
            if not restaurant_items:
                logging.error(f"Unexpected structure for URL: {url}")
                continue
            for item in restaurant_items:
                tname = item.get('UPSO_NM', "")
                main = item.get('MAIN_EDF', "")
                taddr = item.get('SITE_ADDR_RD') if item.get('SITE_ADDR_RD') else item.get('SITE_ADDR', "")
                phone = item.get('UPSO_SITE_TELNO', "")
# 디버그 로깅 추가
                logging.debug(f"Processing restaurant: {tname}, Main: {main}, Address: {taddr}, Phone: {phone}")
                data = {
                    'tname': tname,
                    'tcategory': '맛집',
                    'main': main if main else "",
                    'taddr': taddr if taddr else "",
                    'phone': phone if phone else ""
                }
                all_restaurant_data.append(data)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
            url1 = 'http://localhost:8222/api/travel'
            headers = {"Content-Type": "application/json"}
            response = requests.post(url1, data=json.dumps(all_restaurant_data), headers=headers)
            if response.status_code == 200:  # 응답 확인
                print('데이터 전송 성공')
            else:
                logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL: {url}, Error: {e}")
        except KeyError as e:
            logging.error(f"Parsing error for URL: {url}, Missing Key: {e}")
        except Exception as e:
            logging.error(f"An error occurred for URL: {url}, Error: {e}")
    return jsonify(all_restaurant_data)

# 경기도_맛집 현황
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=6T98794V0223GQQ9O1P42464027&infSeq=3
# 데이터 포맷 : XML
def get_restaurant_ggd():
    # GET Param 방식 요청
    url = 'https://openapi.gg.go.kr/PlaceThatDoATasteyFoodSt?KEY=8a42c0b3579f4b6db90373b373337e50&Type=xml&pIndex=1&pSize=125'
    # URL 잘 나오고 있음
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
    except requests.exceptions.RequestException as e:
        return Response(f"error: {str(e)}", status=500, mimetype='text/plain')
# XML 형태로 응답받은 데이터를 딕셔너리로 변환
    try:
        dict_data = xmltodict.parse(response.text)
# XML 구조 확인 후 올바르게 파싱
        if not dict_data.get('PlaceThatDoATasteyFoodSt', {}).get('head', {}).get('RESULT', {}).get('CODE') == 'INFO-000':
            return Response("error: Invalid API response", status=500, mimetype='text/plain')
        restaurant_items = dict_data['PlaceThatDoATasteyFoodSt']['row']
        restaurant_data = []
        for item in restaurant_items:
            data = {
                "tcategory": "맛집",
                "tname": item.get('RESTRT_NM'),
                "main": item.get('REPRSNT_FOOD_NM'),
                "taddr": item.get('REFINE_ROADNM_ADDR'),
                "phone": item.get('TASTFDPLC_TELNO')
            }
            restaurant_data.append(data)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
#         url1 = 'http://localhost:8222/api/travel'
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url1, data=json.dumps(restaurant_data), headers=headers)
#         if response.status_code == 200:  # 응답 확인
#             print('데이터 전송 성공')
#         else:
#             logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
# 응답 데이터를 텍스트 형태로 변환하여 반환
        response_text = "\n\n".join([
            f"tcategory : {item['tcategory']}\ntname : {item['tname']}\nmain : {item['main']}\ntaddr : {item['taddr']}\nphone : {item['phone']}"
            for item in restaurant_data
        ])
        return Response(response_text, mimetype='text/plain')
    except Exception as e:
        return Response(f"error: {str(e)}", status=500, mimetype='text/plain')

# 전라남도_전남 맛집 정보
# 데이터 포맷 : XML
def get_restaurant_jn():
    API_KEY = 'KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'
    API_KEY_decode = requests.utils.unquote(API_KEY)
    url = 'http://apis.data.go.kr/6460000/jnFood/getNdfoodMenuList'
# URL 안 나오고 있음
    page_size = 10
    # 페이지 번호
    start_page = 0
# 응답 데이터 형식 지정
    req_parameter = {'ServiceKey': API_KEY_decode,
                     'pageSize': page_size, 'startPage': start_page,
    }

# 충청북도_밥맛 좋은 집(https://www.data.go.kr/data/15078870/openapi.do)
# 데이터 포맷 : JSON
def get_restaurant_ccbd():
# URL 잘 나오고 있음
    url = 'https://apis.data.go.kr/6430000/goodRestaService1/getGoodResta1?serviceKey=KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D&currentPage=1&perPage=852'


# 충청남도_음식점(https://www.data.go.kr/data/15063873/openapi.do)
# 데이터 포맷 : XML
def get_restaurant_ccnd():
# URL 잘 나오고 있음
    url = 'https://tour.chungnam.go.kr/_prog/openapi/?func=food&start=1&end=52021'
    try:
        # HTTP GET 요청
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        restaurant = soup.find_all('item')
        restaurant_data = []
        for item in restaurant:
            info_text = item.find('desc').text.strip() if item.find('desc') else 'N/A'
            info_text = info_text.replace('&#039;', "'")
            timage = item.find('list_img').text.strip() if item.find('list_img') else ''
            if timage.endswith('thm_'):
                timage = ''  # 이미지 정보가 없는 것으로 보고 출력하지 않음
            restaurant = {
                'tname': item.find('nm').text.strip() if item.find('nm') else 'N/A',
                'taddr': item.find('addr').text.strip().replace('충남 ', '충청남도 ') if item.find('addr') else 'N/A',
                'tcategory': '맛집',
                'timage': timage,
                'phone': item.find('tel').text.strip() if item.find('tel') else 'N/A',
                'info': info_text
            }
            restaurant_data.append(restaurant)
# 스프링 부트 RestController 엔드포인트 URL
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(restaurant_data), headers=headers)
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
            <h4>충청남도 맛집 정보</h4>
            {% for restaurant in restaurant_data %}
              <p>tname : {{ restaurant.tname }}</h2>
              <p>tcategory : 맛집</p>
              <p>taddr : {{ restaurant.taddr }}</p>
              <p>phone : {{ restaurant.phone }}</p>
              <p>info : {{ restaurant.info }}</p>
              <p>timage : <img src="{{ restaurant.timage }}" alt="맛집 이미지"></p><hr>
            {% endfor %}
          </body>
        </html>
        """
        return render_template_string(template, restaurant_data=restaurant_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

# 경상남도 김해시_음식점 정보(https://www.gimhae.go.kr/00761/00832/05867.web)
# 데이터 포맷 : JSON
def get_restaurant_ghs():
# URL 잘 나오고 있음
    url = 'http://www.gimhae.go.kr/openapi/tour/restaurant.do?pageunit=10&page=27'
    # pageunit = 269
    # page = 27
    try:
# JSON 데이터 가져오기
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
# 필요한 데이터 추출하여 리스트에 저장
        restaurants = data['results']
        restaurant_data = []
        for item in restaurants:
            timage = item.get("images")
            if isinstance(timage, list):
                timage = timage[0] if timage else ""
            taddr = item.get('address', 'N/A')
            if not taddr.startswith('경상남도 김해시'):
                if taddr.startswith('김해시'):
                    taddr = '경상남도 ' + taddr
                else:
                    taddr = '경상남도 김해시 ' + taddr
            restaurant = {
                'tname': item.get('name', 'N/A'),
                'taddr': taddr,
                'tcategory': '맛집',
                'timage': timage,
                'phone': item.get('phone', 'N/A'),
                'time': item.get('businesshour', 'N/A'),
                'main': item.get('menuprice', 'N/A'),
                'info': item.get('content', 'N/A')
            }
            restaurant_data.append(restaurant)
# 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        url1 = 'http://localhost:8222/api/travel'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url1, data=json.dumps(restaurant_data), headers=headers)
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
                {% for restaurant in restaurant_data %}
                    <h4>tname : {{ restaurant.tname }}</h2>
                    <p>tcategory : 맛집</p>
                    <p>taddr : {{ restaurant.taddr }}</p>
                    <p>info : {{ restaurant.info }}</p>
                    <p>phone : {{ restaurant.phone }}</p>
                    <p>time : {{ restaurant.time }}</p>
                    <p>main : {{ restaurant.main }}</p>        
                    <p>timage : 
                        {% if restaurant.timage %}
                            <img src="{{ restaurant.timage }}" alt="맛집 이미지">
                        {% else %}
                        {% endif %}
                    </p><hr>
                {% endfor %}
            </body>
            </html>
            """
        return render_template_string(html_template, restaurant_data=restaurant_data)
    except Exception as e:
        return f"Error: {str(e)}", 500
# 성공!

# 대구광역시_맛집(https://www.data.go.kr/data/15057236/openapi.do)
# 데이터 포맷 : JSON
def get_restaurant_dgs():
# URL 잘 나오고 있음
    url = 'https://www.daegufood.go.kr/kor/api/tasty.html?mode=json&addr=동구'
# addr : 중구, 동구, 남구, 서구, 북구, 수성구, 달서구, 달성군
    try:
        # JSON 데이터 가져오기
        response = requests.get(url)
        data = response.json()
        # 필요한 데이터 추출하여 festivals 리스트에 저장
        restaurant_list = data['data']
        restaurant_data = []
        for item in restaurant_list:
            restaurant = {
                'tname': item.get('BZ_NM', 'N/A'),
                'taddr': item.get('GNG_CS', 'N/A'),
                'tcategory': '맛집',
                'phone': item.get('TLNO', 'N/A'),
                'time': item.get('MBZ_HR', 'N/A'),
                'main': item.get('MNU', 'N/A'),
                'vehicle': item.get('SBW', 'N/A'),
                'info': item.get('SMPL_DESC', 'N/A')
            }
            restaurant_data.append(restaurant)
        # 스프링 부트 RestController 엔드포인트 URL로 데이터 전송
        # url1 = 'http://localhost:8222/api/travel'
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(url1, data=json.dumps(festivals_data), headers=headers)
        # if response.status_code == 200:  # 응답 확인
        #     print('데이터 전송 성공')
        # else:
        #     logging.error(f'데이터 전송 실패 : {response.status_code}, {response.text}')
        # HTML 템플릿을 사용하여 결과를 반환
        html_template = """
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {% for restaurant in restaurants %}
                    <h4>tname : {{ restaurant.tname }}</h2>
                    <p>tcategory : 맛집</p>
                    <p>taddr : {{ restaurant.taddr }}</p>
                    <p>info : {{ restaurant.info }}</p>
                    <p>phone : {{ restaurant.phone }}</p>
                    <p>time : {{ restaurant.time }}</p>
                    <p>main : {{ restaurant.main }}</p>
                    <p>vehicle : {{ restaurant.vehicle }}</p>      
                    <hr>
                {% endfor %}
            </body>
            </html>
            """
        return render_template_string(html_template, restaurant=restaurant_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

# 인천관광공사_인천 스마트음식관광 DB (https://www.data.go.kr/data/15109892/openapi.do)
# 교환 데이터 표준 : JSON
def get_restaurant_ics():
    API_KEY = '4wU3E6Sfbg56mmKvrt5QJsxdEIaqe8pv4FTPZeKjnATcANuBQ1ffaF6sNlya212M'
    # 매장기본정보
    url = 'https://incheon.openapi.redtable.global/api/rstr/korean?serviceKey=4wU3E6Sfbg56mmKvrt5QJsxdEIaqe8pv4FTPZeKjnATcANuBQ1ffaF6sNlya212M'
    # 매장운영정보
    url = 'https://incheon.openapi.redtable.global/api/rstr/oper?serviceKey=4wU3E6Sfbg56mmKvrt5QJsxdEIaqe8pv4FTPZeKjnATcANuBQ1ffaF6sNlya212M'
    # 메뉴 정보
    url = 'https://incheon.openapi.redtable.global/api/menu/korean?serviceKey=4wU3E6Sfbg56mmKvrt5QJsxdEIaqe8pv4FTPZeKjnATcANuBQ1ffaF6sNlya212M'
    # 메뉴 설명 정보
    url = 'https://incheon.openapi.redtable.global/api/menu-expln/korean?serviceKey=4wU3E6Sfbg56mmKvrt5QJsxdEIaqe8pv4FTPZeKjnATcANuBQ1ffaF6sNlya212M'