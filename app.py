from flask import Flask, jsonify, Response, request
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def hello():
    return ('Hello, Flask!!!')

if __name__ == '__main__':
    app.run()

