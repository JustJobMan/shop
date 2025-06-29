from flask import Flask, jsonify, request
import os

# --- Flask 앱 초기화 ---
app = Flask(__name__)

# --- 루트 경로 라우트 추가 (Replit 웹뷰 404 방지용) ---
@app.route('/')
def index():
    return "안녕하세요! Flask 서버가 정상적으로 작동 중입니다. /public-specific-member-points 로 요청하세요."

# --- API 엔드포인트 정의 ---
@app.route('/public-specific-member-points')
def get_public_specific_member_points():
    # 실제 데이터베이스나 다른 소스에서 데이터를 가져오는 로직
    # 여기서는 예시 데이터를 사용합니다.
    try:
        # 실제 데이터는 여기서 가져와야 합니다.
        # 예시 데이터 (실제 사용 시에는 이 부분을 데이터베이스 연동 등으로 대체하세요)
        member_points_data = [
            {"display_name": "첫 번째 회원", "points": 12345},
            {"display_name": "두 번째 회원", "points": 6789},
            {"display_name": "세 번째 회원", "points": 9876},
            {"display_name": "네 번째 회원", "points": 54321}
        ]

        # 성공 응답 반환
        return jsonify({
            "success": True,
            "data": member_points_data,
            "message": "회원 포인트 정보를 성공적으로 불러왔습니다."
        }), 200

    except Exception as e:
        # 오류 발생 시 에러 응답 반환
        print(f"데이터 처리 중 오류 발생: {e}")
        return jsonify({
            "success": False,
            "data": [],
            "message": f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"
        }), 500

# --- Flask 서버 실행 ---
if __name__ == '__main__':
    # Replit 환경에서는 PORT 환경 변수를 사용하는 것이 좋습니다.
    # Replit은 기본적으로 8080 포트를 사용하지만, Flask는 기본 5000을 사용하므로 맞춰줍니다.
    port = int(os.environ.get('PORT', 5000)) # Replit에서 PORT 환경 변수가 없으면 5000 사용

    print(f"Flask 앱 'shop' 시작 중...")
    print(f"* Serving Flask app 'shop'")
    print(f"* Debug mode: off")
    print(f"WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.")
    print(f"* Running on all addresses (0.0.0.0)")
    print(f"* Running on http://127.0.0.1:{port}")
    print(f"* Running on http://172.31.128.42:{port} (내부 IP, 실제 외부 접근은 Replit URL 사용)")

    # Flask 앱 실행
    app.run(host='0.0.0.0', port=port)