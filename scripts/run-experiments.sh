# 파일 경로: scripts/run-experiments.sh
# 패턴 검증 실험 실행 스크립트

#!/bin/bash

set -e

echo "=== Queue-Based Load Leveling 패턴 검증 실험 ==="

# API Gateway 주소 설정
API_URL="http://$(minikube ip):30080"

echo "1. 시스템 상태 확인 중..."
curl -f "$API_URL/health" > /dev/null
echo "   시스템 정상 상태 확인됨"

echo "2. 기본 메시지 전송 테스트..."
curl -X POST "$API_URL/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "타입": "SUBSCRIPTION",
    "내용": "테스트 가입 요청"
  }'

echo "3. 큐 상태 확인..."
curl -s "$API_URL/api/queue/status" | jq '.'

echo "4. 배치 메시지 전송 테스트..."
curl -X POST "$API_URL/api/messages/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "메시지목록": [
      {"타입": "SUBSCRIPTION", "내용": "가입 요청 1"},
      {"타입": "MNP", "내용": "번호이동 요청 1"},
      {"타입": "CHANGE", "내용": "명의변경 요청 1"},
      {"타입": "TERMINATION", "내용": "해지 요청 1"}
    ]
  }'

echo "5. 시스템 통계 확인..."
curl -s "$API_URL/api/stats" | jq '.'

echo "실험 완료! 추가 부하 테스트는 Python 스크립트를 사용하세요:"
echo "  python -c \"
from src.experiments.load_generator import 부하생성기
import asyncio

async def 실험():
    generator = 부하생성기('$API_URL')
    result = await generator.급증부하생성(100, 30)
    print('급증 부하 테스트 결과:', result)

asyncio.run(실험())
\""