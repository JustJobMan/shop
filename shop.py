import os
import requests
from flask import Flask, jsonify, render_template_string
from datetime import datetime, timedelta
import json
# import base64 # Basic 인증 방식 사용 시 필요 (이 방식에서는 필요 없음)

app = Flask(__name__)

# --- 설정 (환경 변수에서 가져오는 것을 권장) ---
IMWEB_API_KEY = os.environ.get('IMWEB_API_KEY')       # 아임웹에서 발급받은 API Key
IMWEB_SECRET_KEY = os.environ.get('IMWEB_SECRET_KEY') # 아임웹에서 발급받은 Secret Key

# 아임웹 API 기본 URL (아임웹 개발자 문서에 있는 기본 API URL)
IMWEB_API_BASE_URL = "https://api.imweb.me/v2" 
IMWEB_OAUTH_TOKEN_URL = "https://api.imweb.me/oauth/token" # Access Token 발급 URL (문서 확인)

# 조회할 특정 멤버들의 정보 (회원 아이디 또는 회원명)
TARGET_MEMBERS = [
    {"display_name": "멤버 A", "uid": "guiwoong"}, # 실제 아임웹 회원 아이디로 변경
    {"display_name": "멤버 B", "uid": "wereer@hotmail.com"},
    {"display_name": "멤버 C", "uid": "	1210@naver.com"},
    {"display_name": "멤버 D", "uid": "	happytmvhs00@naver.com"},
    {"display_name": "멤버 E", "uid": "	dydtn2132@naver.com"},
]

# 데이터 캐싱 (API 호출 제한 방지)
cached_points_data = None
cache_expiry_time = None
CACHE_DURATION_MINUTES = 5 # 5분마다 데이터 갱신

# Access Token 캐싱을 위한 전역 변수
cached_access_token = None
access_token_expiry = None

# --- Access Token 발급 함수 ---
def get_imweb_access_token():
    global cached_access_token, access_token_expiry

    # 캐시된 토큰이 있고 만료되지 않았다면 캐시 사용
    if cached_access_token and access_token_expiry and datetime.now() < access_token_expiry:
        print("캐시된 Access Token 사용")
        return cached_access_token

    if not IMWEB_API_KEY or not IMWEB_SECRET_KEY:
        raise ValueError("IMWEB_API_KEY 또는 IMWEB_SECRET_KEY가 설정되지 않았습니다.")

    # 문서에 명시된 Content-Type 사용
    headers = {
        "Content-Type": "application/x-www-form-urlencoded" 
    }
    # 문서에 명시된 요청 데이터 (JSON.dumps 사용 안 함)
    payload = {
        "grant_type": "client_credentials", 
        "client_id": IMWEB_API_KEY,
        "client_secret": IMWEB_SECRET_KEY
    }

    try:
        # data=payload 로 폼 데이터 전송
        response = requests.post(IMWEB_OAUTH_TOKEN_URL, headers=headers, data=payload)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        token_data = response.json()
        
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in") # 토큰 유효 기간 (초 단위)

        if not access_token:
            raise ValueError(f"Access Token 발급 실패: 응답에 access_token이 없습니다. 응답: {token_data}")

        # 토큰 캐시 및 만료 시간 설정 (만료 1분 전 갱신하도록 설정)
        cached_access_token = access_token
        access_token_expiry = datetime.now() + timedelta(seconds=expires_in - 60) 

        print("새로운 Access Token 발급 성공")
        return access_token

    except requests.exceptions.RequestException as e:
        # HTTP 오류 응답을 자세히 로깅
        if e.response is not None:
            print(f"Access Token 발급 API 호출 실패 (HTTP {e.response.status_code}): {e.response.text}")
            raise ConnectionError(f"Access Token 발급 API 호출 실패: {e.response.status_code} - {e.response.text}")
        else:
            raise ConnectionError(f"Access Token 발급 API 호출 실패: {e}")
    except ValueError as e:
        raise ValueError(f"Access Token 응답 처리 실패: {e}")
    except Exception as e:
        raise Exception(f"Access Token 발급 중 알 수 없는 오류 발생: {e}")


# --- 모든 회원의 포인트 조회 함수 (GET /member/members 사용) ---
def get_all_members_with_points():
    # Access Token 발급/가져오기
    access_token = get_imweb_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}" # 발급받은 Access Token 사용
    }
    
    # 찾아주신 정확한 API 엔드포인트 반영
    api_url = f"{IMWEB_API_BASE_URL}/member/members" 
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()

        if data.get('code') != 200: # 아임웹 API 응답 코드 확인
            raise Exception(f"아임웹 API 오류: {data.get('msg', '알 수 없는 오류')}")

        members_data = data.get('data', []) # 'data' 키 안에 회원 리스트가 있음
        
        all_member_points = {}
        for member in members_data:
            # 아임웹 API 응답에서 'uid'와 'point_amount' 필드 사용
            uid = member.get('uid')
            point_amount = member.get('point_amount', 0)
            if uid:
                all_member_points[uid] = point_amount
        return all_member_points

    except requests.exceptions.RequestException as e:
        # HTTP 오류 응답을 자세히 로깅
        if e.response is not None:
            print(f"회원 포인트 API 호출 실패 (HTTP {e.response.status_code}): {e.response.text}")
            raise ConnectionError(f"회원 포인트 API 호출 실패: {e.response.status_code} - {e.response.text}")
        else:
            raise ConnectionError(f"회원 포인트 API 호출 실패: {e}")
    except json.JSONDecodeError:
        raise ValueError("아임웹 API 응답이 유효한 JSON 형식이 아닙니다.")
    except Exception as e:
        raise Exception(f"회원 포인트 데이터 처리 중 알 수 없는 오류 발생: {e}")

# --- Flask 라우트 핸들러 ---
@app.route('/public-specific-member-points')
def get_public_specific_member_points():
    global cached_points_data, cache_expiry_time

    # 캐시된 데이터가 유효하면 캐시 사용
    if cached_points_data and cache_expiry_time and datetime.now() < cache_expiry_time:
        print("캐시된 특정 회원 포인트 데이터 사용")
        return jsonify(cached_points_data)

    try:
        # 모든 회원의 포인트를 한 번에 가져옴
        all_imweb_points = get_all_members_with_points()

        # 타겟 멤버들의 포인트만 추출
        member_points_list = []
        for member_info in TARGET_MEMBERS:
            display_name = member_info["display_name"]
            target_uid = member_info["uid"]
            
            points = all_imweb_points.get(target_uid, "조회 불가") # UID로 포인트 찾기
            
            member_points_list.append({
                "display_name": display_name,
                "points": points
            })

        # 캐시 업데이트
        cached_points_data = {"success": True, "data": member_points_list}
        cache_expiry_time = datetime.now() + timedelta(minutes=CACHE_DURATION_MINUTES)
        return jsonify(cached_points_data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except ConnectionError as e:
        return jsonify({"error": "아임웹 API 연결 오류", "details": str(e)}), 500
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": "서버 내부 오류", "details": str(e)}), 500

# Flask 앱 실행 (Koyeb/Replit에서 ENTRYPOINT로 사용)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000)) # 기본 포트 5000
