from flask import Flask, jsonify, Response, request
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from flask_apscheduler import APScheduler
from weather import get_weather2
from flask_cors import CORS

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

app.add_url_rule('/api/weather2', 'get_weather2', get_weather2, methods=['GET'])
@app.route('/')
def hello():
    return ('Hello, Flask!!!')

if __name__ == '__main__':
    app.run()

