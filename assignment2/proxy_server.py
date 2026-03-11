# proxy_server.py (HTTPS + Caching + CORS 최종 버전)
from flask import Flask, jsonify, make_response
from flask_cors import CORS  # 1. CORS 라이브러리 import
import requests
import time

app = Flask(__name__)
CORS(app)  # 2. CORS를 앱 전체에 적용

# 본인의 실제 API 키로 교체해야 합니다.
API_KEY = "23e1c43e06ebbf18f7886c1f70760514" 

# 서버 측 캐시를 위한 딕셔너리 (메모리 캐시)
server_cache = {}

@app.route('/weather/<city>')
def get_weather(city):
    current_time = time.time()
    cache_duration = 600  # 캐시 유효 시간 (초), 10분

    # 1. 서버 캐시 확인
    if city in server_cache and current_time - server_cache[city]['timestamp'] < cache_duration:
        print(f"'{city}' 정보를 서버 캐시에서 반환합니다.")
        cached_data = server_cache[city]['data']
        
        # 브라우저 캐싱을 위한 헤더 추가
        response = make_response(jsonify(cached_data))
        response.headers['Cache-Control'] = f'public, max-age={cache_duration}'
        return response

    # 2. 캐시에 없으면 OpenWeatherMap API로 새로 요청
    print(f"'{city}' 정보를 API를 통해 새로 요청합니다.")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    api_response = requests.get(url)

    if api_response.status_code == 200:
        weather_data = api_response.json()
        
        # 3. 성공적인 응답을 서버 캐시에 저장
        server_cache[city] = {
            'data': weather_data,
            'timestamp': current_time
        }
        
        # 브라우저 캐싱을 위한 헤더 추가 후 응답
        response = make_response(jsonify(weather_data))
        response.headers['Cache-Control'] = f'public, max-age={cache_duration}'
        return response
    else:
        # API 요청 실패 시 에러 응답
        return jsonify({"error": "Failed to fetch weather from API"}), api_response.status_code

if __name__ == '__main__':
    # HTTPS 적용을 위한 SSL 컨텍스트 설정
    # cert.pem과 key.pem 파일이 이 스크립트와 같은 위치에 있어야 함
    try:
        context = ('cert.pem', 'key.pem')
        app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)
    except FileNotFoundError:
        print("="*60)
        print("오류: 'cert.pem' 또는 'key.pem' 파일을 찾을 수 없습니다.")
        print("OpenSSL을 사용하여 인증서를 먼저 생성해주세요.")
        print("예: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        print("="*60)
