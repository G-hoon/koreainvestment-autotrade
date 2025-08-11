#!/usr/bin/env python3
"""
Google Cloud Run용 시작 스크립트
HTTP 헬스체크 서버와 자동매매 프로그램을 동시에 실행
"""
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json

# 환경 변수에서 포트 가져오기 (Cloud Run 기본값: 8080)
PORT = int(os.environ.get('PORT', 8080))

# 자동매매 프로그램 상태 추적
autotrade_process = None
autotrade_status = {"status": "starting", "last_update": time.time()}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            # 헬스체크 엔드포인트
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "healthy",
                "timestamp": time.time(),
                "autotrade_status": autotrade_status["status"],
                "last_update": autotrade_status["last_update"]
            }
            
            self.wfile.write(json.dumps(status).encode())
            
        elif self.path == '/status':
            # 상태 확인 엔드포인트
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            global autotrade_process
            is_running = autotrade_process and autotrade_process.poll() is None
            
            status = {
                "autotrade_running": is_running,
                "process_id": autotrade_process.pid if is_running else None,
                "status": autotrade_status["status"],
                "last_update": autotrade_status["last_update"],
                "uptime": time.time() - start_time
            }
            
            self.wfile.write(json.dumps(status).encode())
            
        elif self.path == '/':
            # 기본 페이지
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Korean Investment Auto Trading</title>
                <meta charset="utf-8">
                <meta http-equiv="refresh" content="30">
            </head>
            <body>
                <h1>🚀 한국투자증권 자동매매</h1>
                <h2>📊 상태</h2>
                <p><strong>프로그램 상태:</strong> {autotrade_status["status"]}</p>
                <p><strong>마지막 업데이트:</strong> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(autotrade_status["last_update"]))}</p>
                <p><strong>실행 시간:</strong> {int(time.time() - start_time)}초</p>
                
                <h2>🔗 API 엔드포인트</h2>
                <ul>
                    <li><a href="/health">/health</a> - 헬스체크</li>
                    <li><a href="/status">/status</a> - 상세 상태</li>
                </ul>
                
                <p><em>이 페이지는 30초마다 자동 새로고침됩니다.</em></p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # HTTP 서버 로그를 간소화
        pass

def run_autotrade():
    """자동매매 프로그램을 별도 스레드에서 실행"""
    global autotrade_process, autotrade_status
    
    try:
        print("🚀 자동매매 프로그램 시작...")
        autotrade_status["status"] = "running"
        autotrade_status["last_update"] = time.time()
        
        # 자동매매 프로그램 실행
        autotrade_process = subprocess.Popen(
            ['python', 'UsaStockAutoTrade.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 출력 스트림 읽기
        for line in iter(autotrade_process.stdout.readline, ''):
            if line:
                print(f"[AutoTrade] {line.strip()}")
                autotrade_status["last_update"] = time.time()
                
                # 특정 키워드로 상태 업데이트
                if "매수 성공" in line:
                    autotrade_status["status"] = "trading_active"
                elif "오류" in line:
                    autotrade_status["status"] = "error"
                elif "프로그램을 종료" in line:
                    autotrade_status["status"] = "shutting_down"
        
        # 프로세스 종료 처리
        autotrade_process.wait()
        print("❌ 자동매매 프로그램이 종료되었습니다.")
        autotrade_status["status"] = "stopped"
        autotrade_status["last_update"] = time.time()
        
    except Exception as e:
        print(f"❌ 자동매매 프로그램 실행 오류: {e}")
        autotrade_status["status"] = "error"
        autotrade_status["last_update"] = time.time()

def run_http_server():
    """HTTP 헬스체크 서버 실행"""
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    print(f"🌐 HTTP 서버 시작 - 포트: {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    start_time = time.time()
    
    print(f"🚀 Google Cloud Run 자동매매 컨테이너 시작")
    print(f"📡 HTTP 서버 포트: {PORT}")
    
    # HTTP 서버를 별도 스레드에서 실행
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # 잠시 대기 후 자동매매 프로그램 시작
    time.sleep(2)
    
    # 자동매매 프로그램 실행 (메인 스레드에서)
    run_autotrade()
    
    # 프로그램이 종료되면 컨테이너도 종료
    print("🔄 컨테이너 종료 중...")