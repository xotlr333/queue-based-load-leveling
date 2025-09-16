#!/bin/bash

NAMESPACE="bss-queue-system"
INTERVAL=3

echo "🔍 실시간 Pod 리소스 모니터링 시작 (${INTERVAL}초 간격)"
echo "Ctrl+C로 종료"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        BSS Queue System 리소스 모니터링                         ║"
    echo "║                           $(date '+%Y-%m-%d %H:%M:%S')                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "📊 Pod 상태:"
    kubectl get pods -n $NAMESPACE -o wide
    echo ""
    
    echo "📈 리소스 사용량:"
    kubectl top pods -n $NAMESPACE 2>/dev/null || echo "   ⏳ 메트릭 서버 대기 중..."
    echo ""
    
    echo "🔄 HPA 상태:"
    kubectl get hpa -n $NAMESPACE 2>/dev/null || echo "   📝 HPA 정보 없음"
    echo ""
    
    echo "💡 ${INTERVAL}초 후 자동 갱신... (Ctrl+C로 종료)"
    sleep $INTERVAL
done
