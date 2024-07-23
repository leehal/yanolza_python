from flask import Flask

from routes.water import get_beach, get_fishing_ggd, get_hot_spring
from routes.tracking import get_bicycle
from routes.festival import get_festival_ic, festival_jjs_bp, festival_wss_bp, get_festival_djs, festival_ghs_bp, festival_ccnd_bp
from routes.forest import get_plant, get_trail
from routes.history import get_history_im, get_open_port_ic
from routes.lodge import get_lodge_ggd, get_lodge_sjs, get_lodge_seoul, get_lodge_ccnd, get_lodge_dgs, get_lodge_ghs
from routes.mountain import mountain_bp
from routes.play import get_play_sac, get_play_mcst
from routes.restaurant import get_restaurant_seoul, get_restaurant_ggd, get_restaurant_jn, get_restaurant_ccnd, get_restaurant_ghs, get_restaurant_dgs
from routes.tour import get_tour_ggd, get_tour_ghs, get_tour_ccnd, get_tour_ccs
from routes.tracking import get_tracking

# API 서버를 구축하기 위한 기본 구조
app = Flask(__name__)

@app.route('/')
def start():
    return '기본적으로 정상 작동 확인'

app.register_blueprint(mountain_bp)
app.register_blueprint(festival_jjs_bp)
app.register_blueprint(festival_ghs_bp)
app.register_blueprint(festival_wss_bp)
app.register_blueprint(festival_ccnd_bp)

# url에 _ 쓰지 않게 주의
app.add_url_rule('/api/fishing-ggd', 'get_fishing_ggd', get_fishing_ggd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/hot-spring', 'get_hot_spring', get_hot_spring, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/beach', 'get_beach', get_beach, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/bicycle', 'get_bicycle', get_bicycle, methods=['GET']) # ㄴㄴ
app.add_url_rule('/api/plant', 'get_plant', get_plant, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/festival-ic', 'get_festival_ic', get_festival_ic, methods=['GET'])
app.add_url_rule('/api/festival-djs', 'get_festival_djs', get_festival_djs, methods=['GET']) # ㄴㄴ
app.add_url_rule('/api/history-im', 'get_history_im', get_history_im, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/open-port-ic', 'get_get_open_port_ic', get_open_port_ic, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/lodge-seoul', 'get_lodge_seoul', get_lodge_seoul, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/lodge-ccnd', 'get_lodge_ccnd', get_lodge_ccnd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/lodge-dgs', 'get_lodge_dgs', get_lodge_dgs, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/lodge-ggd', 'get_lodge_ggd', get_lodge_ggd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/lodge-ghs', 'get_lodge_ghs', get_lodge_ghs, methods=['GET'])
app.add_url_rule('/api/lodge-sjs', 'get_lodge_sjs', get_lodge_sjs, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/play-mcst', 'get_play_mcst', get_play_mcst, methods=['GET'])
app.add_url_rule('/api/play-sac', 'get_play_sac', get_play_sac, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/restaurant-seoul', 'get_restaurant_seoul', get_restaurant_seoul, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/restaurant-ccnd', 'get_restaurant_ccnd', get_restaurant_ccnd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/restaurant-ggd', 'get_restaurant_ggd', get_restaurant_ggd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/restaurant-jn', 'get_restaurant_jn', get_restaurant_jn, methods=['GET']) # ㄴㄴ
app.add_url_rule('/api/restaurant-ghs', 'get_restaurant_ghs', get_restaurant_ghs, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/restaurant-dgs', 'get_restaurant_dgs', get_restaurant_dgs, methods=['GET'])
app.add_url_rule('/api/tour-ggd', 'get_tour_ggd', get_tour_ggd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/tour-ghs', 'get_tour_ghs', get_tour_ghs, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/tour-ccnd', 'get_tour_ccnd', get_tour_ccnd, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/tour-ccs', 'get_tour_ccs', get_tour_ccs, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/tracking', 'get_tracking', get_tracking, methods=['GET']) # 잘 나와!
app.add_url_rule('/api/trail', 'get_trail', get_trail, methods=['GET']) # 잘 나와!


# 서버 실행
if __name__ == '__main__':
    app.run()