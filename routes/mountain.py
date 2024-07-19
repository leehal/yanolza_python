import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import json
import warnings
from flask import Flask, jsonify, request, Blueprint, render_template_string
import urllib.parse
import logging
import re
import html
import xmltodict

# 산림청_산 정보 조회 (https://www.data.go.kr/data/15058682/openapi.do?recommendDataYn=Y)
# 데이터 포맷 : XML
mountain_bp = Blueprint('mountain', __name__)
def clean_html(raw_html):
    if "<" in raw_html and ">" in raw_html:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=MarkupResemblesLocatorWarning)
            clean_text = BeautifulSoup(raw_html, "html.parser").get_text(separator=" ", strip=True)
    else:
        clean_text = raw_html
    clean_text = html.unescape(clean_text)  # HTML 엔티티 변환
    clean_text = re.sub(r'\s+|&nbsp;', ' ', clean_text).strip()  # HTML 엔티티 및 불필요한 공백 제거
    clean_text = re.sub(r'<[^>]+>', '', clean_text)  # HTML 태그 제거
    replacements = { # 특정 HTML 엔티티들을 공백으로 대체
        '&#160;': ' ', '&acirc;': ' ', '&otilde;': ' ', '&ouml;': ' ', '&gt;': ' ', '&ucirc;': ' '
    }
    for old, new in replacements.items():
        clean_text = clean_text.replace(old, new)
    return clean_text
def correct_address(address):
    corrections = {
        "전남": "전라남도", "전북": "전라북도", "충북": "충청북도", "충남": "충청남도", "경북": "경상북도", "경남": "경상남도",
        "거제도": "경상남도 거제시", "김천시": "경상북도 김천시", "상주시": "경상북도 상주시", "횡성군": "강원도 횡성군",
        "강원동 평창군 도암면": "강원도 평창군 대관령면"
    }
    for key, value in corrections.items():
        if address.startswith(key):
            address = address.replace(key, value)
            break
    return address
@mountain_bp.route('/api/mountain', methods=['GET'])
def get_mountain():
    url = "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice?"
    params = {
        'serviceKey': urllib.parse.quote('KyWZFbqa18xa0lm8HRhyexgvbK%2BRVv0pzL2mNe1IaZXLpcPgeiWPK9MU4vju7yz%2F8SFykfu4KO%2FpXu%2FSuRP3ig%3D%3D'),
        'pageNo': '3',     # 1~2, 1~4, 1~6
        'numOfRows': '446' # 664, 446, 223
    } # totalCount : 1338
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('item')
    mountains = []
    def get_text_or_na(tag):  # 내용 없을 때
        if tag and tag.text:
            clean_text = tag.text.strip()
            if clean_text and clean_text not in ['&amp;nbsp;', '<p>&nbsp;</p>', '']:
                return clean_text
        return ''
    def get_info_text(item):  # 짧은 정보 없으면 긴 정보 대체
        for tag_name in ['mntnsbttlinfo', 'hndfmsmtnslctnrson', 'mntninfodscrt', 'mntninfodtlinfocont']:  # 100대 명산 선정 이유, 산 정보 개관, 상세 정보 내용
            tag = item.find(tag_name)
            clean_text = get_text_or_na(tag)
            if clean_text != 'N/A':
                return clean_html(clean_text)[:730] # 데이터 길이 제한
        return ''
    for item in items:
        mntnattchimageseq = get_text_or_na(item.find('mntnattchimageseq'))
        hndfmsmtnmapimageseq = get_text_or_na(item.find('hndfmsmtnmapimageseq'))
        timage = ''
        if mntnattchimageseq != 'http://www.forest.go.kr/newkfsweb/cmm/fms/getImage.do?fileSn=1&atchFileId=':
            timage = mntnattchimageseq
        elif (mntnattchimageseq == 'http://www.forest.go.kr/newkfsweb/cmm/fms/getImage.do?fileSn=1&atchFileId=' and
            len(hndfmsmtnmapimageseq) > len('http://www.forest.go.kr/swf/foreston/mountain/')):
            timage = hndfmsmtnmapimageseq
        elif (mntnattchimageseq == 'http://www.forest.go.kr/newkfsweb/cmm/fms/getImage.do?fileSn=1&atchFileId=' and
            hndfmsmtnmapimageseq == 'http://www.forest.go.kr/swf/foreston/mountain/'):
            timage = ''
        taddr = correct_address(get_text_or_na(item.find('mntninfopoflc')))
        guide = "산 높이 " + get_text_or_na(item.find('mntninfohght')) + "m"  # 높이 값에 'm' 추가
        course = clean_html(get_text_or_na(item.find('crcmrsghtnginfoetcdscrt')) or
                            get_text_or_na(item.find('crcmrsghtnginfodscrt')))
        if '보호수&lt;당산나무' in course:
            course = course.replace('보호수&lt;당산나무', '보호수 : 당산나무')
        mountain = {
            'tname': get_text_or_na(item.find('mntnnm')),
            'taddr': taddr,
            'tcategory': '관광',
            'guide': guide,
            'vehicle': clean_html(get_text_or_na(item.find('pbtrninfodscrt'))),
            'info': get_info_text(item),
            'phone': get_text_or_na(item.find('mntninfomangrtlno')),
            'course': course,
            'timage': timage
        }
        mountains.append(mountain)
    # url1 = 'http://localhost:8222/api/travel'
    # headers = {"Content-Type": "application/json"}
    # response = requests.post(url1, data=json.dumps(mountains), headers=headers)
    # if response.status_code == 200:
    #     print('데이터 전송 성공')
    # else:
    #     print(f'데이터 전송 실패: {response.status_code} - {response.text}')
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        {% for mountain in mountains %}
            <p><strong>tname :</strong> {{ mountain['tname'] }}</p>
            <p><strong>taddr :</strong> {{ mountain['taddr'] }}</p>
            <p><strong>tcategory :</strong> 관광</p>
            <p><strong>guide :</strong> {{ mountain['guide'] }}</p>
            <p><strong>vehicle :</strong> {{ mountain['vehicle'] }}</p>
            <p><strong>phone :</strong> {{ mountain['phone'] }}</p>
            <p><strong>info :</strong> {{ mountain['info'] }}</p>
            <p><strong>course :</strong> {{ mountain['course'] }}</p>
            <p><strong>timage :</strong> 
                {% if mountain['timage'] != 'N/A' %}
                    <img src="{{ mountain['timage'] }}" alt="산 이미지">
                {% else %}
                    이미지 없음
                {% endif %}</p>
            <hr>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html_template, mountains=mountains)
# 성공!