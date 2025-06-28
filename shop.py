import os
import requests
from flask import Flask, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import base64 # Basic 인증 방식 사용 시 필요

app = Flask(__name__)

# --- 설정 (환경 변수에서 가져오는 것을 권장) ---
IMWEB_API_KEY = os.environ.get('IMWEB_API_KEY')       # Replit Secrets 등에 저장
IMWEB_SECRET_KEY = os.environ.get('IMWEB_SECRET_KEY') # Replit Secrets 등에 저장
IMWEB_API_BASE_URL = "https://old-developers.imweb.me" # 아임웹 개발자 문서에 있는 기본 URL (실제 API URL은 다를 수 있음)

# 조회할 특정 멤버들의 정보 (회원 아이디 또는 회원명)
# 아임웹 API가 회원 아이디(uid)로 조회를 지원하는지, 회원명(name)으로 조회를 지원하는지 확인 필요
# 여기서는 회원 아이디(uid)를 사용한다고 가정합니다.
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

# --- API 호출을 위한 헤더 생성 함수 (아임웹 문서 기반으로 수정 필요) ---
def get_imweb_headers():
    if not IMWEB_API_KEY or not IMWEB_SECRET_KEY:
        raise ValueError("IMWEB_API_KEY 또는 IMWEB_SECRET_KEY가 설정되지 않았습니다.")

    # 아임웹 개발자 문서에 명시된 정확한 헤더 형식을 사용해야 합니다.
    # 예시 1: Authorization: Bearer [API_KEY] (Secret Key는 서버 측에서 검증)
    # 예시 2: X-API-KEY: [API_KEY], X-SECRET-KEY: [SECRET_KEY]
    # 예시 3: Authorization: Basic Base64(API_KEY:SECRET_KEY)
    
    # 아임웹 개발자 문서의 회원 조회 API 예시를 보면 'Authorization: Basic' 방식이 사용됩니다.
    # https://old-developers.imweb.me/members/get (이 URL을 참고했습니다.)
    auth_string = f"{IMWEB_API_KEY}:{IMWEB_SECRET_KEY}"
    encoded_auth_string = base64.b64encode(auth_string.encode()).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_auth_string}" # 아임웹 문서에 따른 인증 헤더
    }
    return headers

# --- 특정 멤버의 포인트 조회 함수 ---
def get_member_point_by_uid(member_uid):
    headers = get_imweb_headers()
    
    # 아임웹 회원 조회 API 엔드포인트
    # https://old-developers.imweb.me/members/get 참고
    # uid로 조회하는 파라미터가 있는지 확인 필요 (문서에 'uid' 파라미터가 있습니다!)
    api_url = f"{IMWEB_API_BASE_URL}/members"
    params = {"uid": member_uid} # uid 파라미터로 특정 회원 조회

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # 응답 데이터 구조 확인: 'data' 안에 리스트가 있고, 그 안에 회원 정보가 있을 수 있음
        # 아임웹 회원 조회 API는 단일 회원을 조회해도 리스트 형태로 반환할 수 있습니다.
        members_data = data.get('data', [])
        if members_data:
            # 첫 번째 회원 정보에서 포인트 가져오기
            member_info = members_data[0]
            # 'point_amount' 항목이 포인트입니다.
            return member_info.get('point_amount', 0) 
        return 0 # 회원 정보가 없으면 0 포인트 반환

    except requests.exceptions.RequestException as e:
        print(f"회원 UID {member_uid} 포인트 조회 중 오류 발생: {e}")
        return -1 # 오류 발생 시 -1 반환 (오류 처리용)
    except Exception as e:
        print(f"회원 UID {member_uid} 데이터 처리 중 오류 발생: {e}")
        return -1

# --- Flask 라우트 핸들러 ---
@app.route('/public-specific-member-points')
def get_public_specific_member_points():
    global cached_points_data, cache_expiry_time

    # 캐시된 데이터가 유효하면 캐시 사용
    if cached_points_data and cache_expiry_time and datetime.now() < cache_expiry_time:
        print("캐시된 특정 회원 포인트 데이터 사용")
        return jsonify(cached_points_data)

    try:
        # 각 타겟 멤버의 포인트 조회
        member_points_list = []
        for member_info in TARGET_MEMBERS:
            uid = member_info["uid"]
            display_name = member_info["display_name"]
            
            points = get_member_point_by_uid(uid)
            
            if points != -1: # 조회 성공 시
                member_points_list.append({
                    "display_name": display_name,
                    "points": points
                })
            else: # 조회 실패 시
                member_points_list.append({
                    "display_name": display_name,
                    "points": "조회 불가" # 또는 0, 또는 오류 메시지
                })

        # 캐시 업데이트
        cached_points_data = {"success": True, "data": member_points_list}
        cache_expiry_time = datetime.now() + timedelta(minutes=CACHE_DURATION_MINUTES)
        return jsonify(cached_points_data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": "서버 내부 오류", "details": str(e)}), 500

# Flask 앱 실행 (Koyeb/Replit에서 ENTRYPOINT로 사용)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000)) # 기본 포트 5000
