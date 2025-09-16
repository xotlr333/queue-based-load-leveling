# 파일 경로: scripts/cleanup.sh
# 환경 정리 스크립트

#!/bin/bash

echo "=== BSS Queue-Based Load Leveling 패턴 환경 정리 ==="

# 1. Kubernetes 리소스 삭제
echo "1. Kubernetes 리소스 삭제 중..."
kubectl delete namespace bss-queue-system --ignore-not-found=true

# 2. Helm 릴리스 삭제
echo "2. Helm 릴리스 정리 중..."
helm uninstall rabbitmq -n bss-queue-system --ignore-not-found

# 3. Docker 이미지 정리
echo "3. Docker 이미지 정리 중..."
docker rmi bss-producer:latest bss-consumer:latest 2>/dev/null || true

# 4. Minikube 중지 (선택적)
read -p "Minikube를 중지하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "4. Minikube 중지 중..."
    minikube stop
fi

echo "정리 완료!"