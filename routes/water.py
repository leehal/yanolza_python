import requests
from bs4 import BeautifulSoup
import json
import logging
from flask import Flask, jsonify, request, render_template_string, Response
import xmltodict
import urllib.parse

LAYER_NAMES = [
    'TB_YACHT_RPNT', 'TB_FACI_FSHLC', 'TB_FACI_SPORT', 'TB_YACHT_MARINA_P',
    'TL_RFISHERY_P' 'TL_SFISHERY_P', 'TB_FACI_TEMPLE', 'TB_YACHT_SPOINT',
    'TB_SAILER', 'TB_FACI_GARDEN', 'VI_SEA_VR', 'TB_FACI_FISHPORT',
    'TB_FACI_FILMSITE', 'TL_RUTE_L', 'TB_FACI_SCENIC', 'TB_FACI_FISHINGOLE',
    'TB_FACI_EXHIBIT', 'TL_CONECT_L', 'TL_ALLRUTE_L', 'TL_MARINA_L',
    'TB_FACI_FESTIVAL', 'TB_FACI_CAMPSITE', 'TB_FACI_THEMEPARK', 'VI_BCROAD_L',
    'TB_FACI_MARINTRAFF', 'TB_FACI_BEACH', 'TB_FACI_TRAIL', 'TB_FACI_RCRFCT',
    'TB_AREA_NAME_OCEAN', 'TL_FPILBOAT_A', 'TL_QUAARE_A', 'TB_ZN_MING',
    'TB_ZN_TRSF', 'VI_ZN_CYFST', 'TL_RESARE_ENS', 'TL_RESARE_FR',
    'TB_ZN_TRDEPT', 'TL_CLRGN_FSPT_A', 'TB_ZN_INDWSTE', 'TL_VTMSA_A',
    'TL_HJPMMP_A', 'TL_SARDRA_L', 'ML_ZN_WTR_LEIS_PRO_L', 'TL_SHMSCH_A',
    'TL_JUKJGY_L', 'TL_EUJOBHSY_L', 'TB_ZN_FRRSR', 'TL_DIST_FSHFRM',
    'TL_CSTZNE_A', 'TL_YACSGRGY_P', 'TL_MIDS_P', 'TB_ZN_TRTSEA',
    'TL_TISVCONA_A', 'TB_ZN_OKR', 'TL_RESARE_AP', 'TL_RSTRCT_A',
    'TB_ZN_FSHOPR', 'TL_FSHSPA_A', 'TL_SWYWRN_A', 'TL_KMSTARE_L',
    'VI_STSLNE_L', 'TL_RESARE_EN', 'TL_RESARE_ER', 'TL_WAINARE_A',
    'TL_SSAONFI_A', 'TL_SSAONFI_L', 'TL_CAPBANA_A', 'TL_HNINTZ_A',
    'TL_HNINTZ_L', 'TL_GDSE_A', 'TL_BECONSSA_A', 'ML_RESARE_RESTRN_27_A',
    'TL_HMBHDJ_P', 'TL_HAEGU_A', 'TB_ZN_SEATN', 'TB_SLFTN_FRT_REGL_SAR_L',
    'ML_ZN_MRT_LEIS_PER_L', 'TB_ZN_EVSR', 'TL_KCGAREA_A', 'TL_CCTVVI_P',
    'TL_POLTRP_P', 'VI_TIDEWY_L', 'VI_UWTROC_P', 'TL_POLSTA_P',
    'TL_STWA_A', 'VI_DWRTPT_A', 'VI_LNDARE_P', 'TL_PTGSCT_ETRYPT_L',
    'TL_PTGSCT_TKOFF_L', 'VI_PILBOP_P', 'VI_FERYRT_L', 'VI_LNDMRK_P',
    'TL_HOSPAL_P', 'TL_PUBHEA_P', 'VI_DOCARE_A', 'VI_SHPACC_P',
    'VI_BERTHS_P', 'TL_BERTH_A', 'TL_BERTH_P', 'TL_TURNBASI_A',
    'TL_FIRSTA_P', 'TL_SOUNDG_P', 'TL_PARMAC_P', 'VI_TWRTPT_A',
    'TL_OBSTRN_P', 'TL_MGWA_A', 'VI_NSHPAC_P', 'VI_FAIRWY_A',
    'VI_ACHARE_A', 'TB_ZN_ROUTE', 'TL_WRECK_P', 'VI_TSSBND_L',
    'VI_TSSCRS_A', 'VI_TSEZNE_A', 'VI_TSELNE_L', 'VI_TSSLPT_A',
    'TL_SMWA_A', 'TL_SEAWAY_A', 'VI_NAVLNE_L', 'TL_COAGUA_P',
    'VI_TIDCHA_A', 'TL_LEIHAZ_TIDCHA_L_2019', 'TL_PBLOFC_P', 'TL_LEQMBD_P',
    'TL_LEIHAZ_TROTSE_A', 'TL_LESALI_L', 'TL_TKTOFC_P', 'TL_SHWROM_P',
    'TL_MALIRE_P', 'TL_SWMRES_L', 'TL_ACCOMM_P', 'TL_INFSIG_P',
    'TL_WCHTWR_P', 'TL_DGSATC_SUBMEROC_P', 'TL_NIFIZO_P', 'TL_KIDZON_P',
    'TL_HOTSPR_P', 'VI_PUDDLE_A', 'TL_DRIFOU_P', 'VI_OFFCUR_A',
    'TL_RESCUE_P', 'TL_WARSYS_P', 'TL_INFCEN_P', 'TL_PRKPLC_P',
    'TL_DREROM_P', 'TL_TUBLND_P', 'TL_ADSECE_P', 'TL_TOILET_P',
    'TL_SMOZON_P', 'VI_BOYINB_P', 'VI_MORFAC_P', 'VI_BOYCAR_P',
    'VI_BCNCAR_P', 'VI_BOYSAW_P', 'VI_SLCONS_L', 'VI_BCNLAT_P',
    'VI_BOYSPP_P', 'VI_BCNSPP_P', 'VI_HRBARE_A', 'TB_SAILER_5030105',
    'TL_VTSCEN_P', 'VI_CBLSUB_L', 'TB_COAST_STAT_INFO', 'TB_SANDRIDGE_BOUNDARY',
    'TB_SAILER_5030103', 'TB_SAILER_5030104', 'TB_SAILER_5030102', 'VI_BCNISD_P'
]

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
#     print(fishing_data)
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
        return Response(f"Error: {str(e)}", status=500)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('row')
    fishing_data = []
    for item in items:
        tname = item.find('HOTSPA_NM').text if item.find('HOTSPA_NM') else '정보없음'
        road_addr = item.find('REFINE_ROADNM_ADDR')
        lot_addr = item.find('REFINE_LOTNO_ADDR')
        taddr = road_addr.text if road_addr and road_addr.text.strip() \
            else (lot_addr.text if lot_addr else '정보없음')
        if not taddr: # 주소 없으면 출력 X
            continue
        info = item.find('INGRDNT_NM').text if item.find('INGRDNT_NM') else '정보없음'
        fishing_data.append({
            'tname': tname, # 온천
            'tcategory': "관광",
            'taddr': taddr,
            'info': info # + guide
        })
    response_text = ""
    for data in fishing_data:
        response_text += f"tname : {data['tname']}\n"
        response_text += f"tcategory : 관광\n"
        response_text += f"taddr : {data['taddr']}\n"
        response_text += f"info : 성분명 : {data['info']}\n\n"
    return Response(response_text, mimetype='text/plain')

def get_beach_leisure():
# GET Param 방식 요청
    API_KEY = '4D048B473A8EABF8A7B7F2C54'
    API_KEY_decode = requests.utils.unquote(API_KEY)
# 요청 주소 및 요청 변수 지정(공공데이터포털 - 데이터찾기 - 레저관광 검색 - 오픈API상세 - URL - 오픈API신청)
    url = 'http://www.khoa.go.kr/oceanmap/otmsInfoApi.do?ServiceKey='
# 한 페이지에 포함된 결과 수
    num_of_rows = 10
# 페이지 번호
    page_no = 1
# 응답 데이터 형식 지정
    result_type = 'JSON'
    for Layer in LAYER_NAMES:
        try:
            response = requests.get(url, params={'Key': API_KEY_decode})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            continue  # 오류가 발생하면 해당 구역을 건너뜀
    sido_cd = 2800000000
    req_parameter = {'serviceKey': API_KEY_decode,
                     'pageNo': page_no, 'numOfRows': num_of_rows,
                     'Layer': LAYER_NAMES, 'SIDOCD': sido_cd,
                   # 'resultType': XML OR JSON
    }
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
    beach_items = dict_data['response']['body']['items']['item']
    beach_data = {}
    for k in range(len(beach_items)):
        beach_item = beach_items[k]
        obsrValue = beach_item['obsrValue']
        if beach_item['category'] == 'POINT_NM': # 자료구분코드 = 항목값
            print(f"[ 지점명 : {obsrValue} ]")
            beach_data['지점명'] = f"{obsrValue}" # 화면에 보이는 이름
        elif beach_item['category'] == 'ADR_KNM':
            print(f"[ 행정구역명 : {obsrValue} ]")
            beach_data['행정구역명'] = f"{obsrValue}"
        elif beach_item['category'] == 'TARGET':
            print(f"[ 지점명 : {obsrValue} ]")
            beach_data['대상어/낚시채비'] = f"{obsrValue}"
        elif beach_item['category'] == 'TIDE_TIME':
            print(f"[ 주요수산물 : {obsrValue} ]")
            beach_data['적정물때'] = f"{obsrValue}"
        elif beach_item['category'] == 'MATERIAL':
            print(f"[ 주요수산물 : {obsrValue} ]")
            beach_data['해저물질(저질)'] = f"{obsrValue}"
# 딕셔너리를 JSON 형태로 변환
    json_beach = json.dumps(beach_data, ensure_ascii=False, indent=4)
    return json_beach