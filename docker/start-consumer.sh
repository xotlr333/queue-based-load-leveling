# 파일 경로: docker/start-consumer.sh
# Consumer 서비스 시작 스크립트

#!/bin/bash

# 스크립트 실행 시 오류 발생 시 중단
set -e

# 로그 출력 함수
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 환경 변수 검증
if [ -z "$PROCESSOR_TYPE" ]; then
    log "ERROR: PROCESSOR_TYPE 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# RabbitMQ 연결 대기
wait_for_rabbitmq() {
    local host="${RABBITMQ_HOST:-rabbitmq}"
    local port="${RABBITMQ_PORT:-5672}"
    local max_attempts=30
    local attempt=1

    log "RabbitMQ 연결 대기 중... ($host:$port)"
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port"; then
            log "RabbitMQ 연결 성공!"
            return 0
        fi
        
        log "RabbitMQ 연결 실패 (시도 $attempt/$max_attempts), 2초 후 재시도..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "ERROR: RabbitMQ 연결 실패 - 최대 시도 횟수 초과"
    exit 1
}

# 헬스 체크 서버 시작 (백그라운드)
start_health_server() {
    cat > /tmp/health_server.py << 'EOF'
import http.server
import socketserver
import json
import os
from datetime import datetime

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            response = {
                "status": "healthy",
                "processor_type": os.getenv('PROCESSOR_TYPE', 'unknown'),
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/ready':
            # RabbitMQ 연결 상태 확인 로직 추가 가능
            response = {"status": "ready", "timestamp": datetime.now().isoformat()}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 로그 출력 비활성화

PORT = int(os.getenv('HEALTH_CHECK_PORT', 8080))
with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
    httpd.serve_forever()
EOF

    python /tmp/health_server.py &
    local health_pid=$!
    log "헬스 체크 서버 시작됨 (PID: $health_pid, Port: ${HEALTH_CHECK_PORT:-8080})"
    echo $health_pid > /tmp/health_server.pid
}

# 프로세스 정리 함수
cleanup() {
    log "정리 작업 시작..."
    
    # 헬스 서버 종료
    if [ -f /tmp/health_server.pid ]; then
        local health_pid=$(cat /tmp/health_server.pid)
        if kill -0 $health_pid 2>/dev/null; then
            kill $health_pid
            log "헬스 체크 서버 종료됨"
        fi
        rm -f /tmp/health_server.pid
    fi
    
    log "정리 작업 완료"
}

# 시그널 핸들러 등록
trap cleanup EXIT TERM INT

# 메인 실행 로직
main() {
    log "BSS Consumer 서비스 시작: $PROCESSOR_TYPE"
    
    # RabbitMQ 연결 대기
    wait_for_rabbitmq
    
    # 헬스 체크 서버 시작
    start_health_server
    
    # 프로세서 타입에 따라 다른 서비스 실행
    case "$PROCESSOR_TYPE" in
        "SUBSCRIPTION")
            log "가입 처리 서비스 시작"
            python -m src.consumer.subscription_processor
            ;;
        "MNP")
            log "번호이동 처리 서비스 시작"
            python -m src.consumer.mnp_processor
            ;;
        "CHANGE")
            log "명의변경 처리 서비스 시작"
            python -m src.consumer.change_processor
            ;;
        "TERMINATION")
            log "해지 처리 서비스 시작"
            python -m src.consumer.termination_processor
            ;;
        *)
            log "ERROR: 알 수 없는 PROCESSOR_TYPE: $PROCESSOR_TYPE"
            log "지원되는 타입: SUBSCRIPTION, MNP, CHANGE, TERMINATION"
            exit 1
            ;;
    esac
}

# 메인 함수 실행
main "$@"