#!/bin/bash

set -e

echo "=== BSS Queue-Based Load Leveling 시스템 배포 ==="

# 1. 네임스페이스 및 기본 설정
echo "1. 네임스페이스 및 설정 적용 중..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap/

# 2. RabbitMQ 설치
echo "2. RabbitMQ 설치 중..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install rabbitmq bitnami/rabbitmq \
  --namespace bss-queue-system \
  --values k8s/rabbitmq/values.yaml \
  --wait

# 3. Docker 이미지 빌드
echo "3. Docker 이미지 빌드 중..."
eval $(minikube docker-env)

docker build -f docker/Dockerfile.producer -t bss-producer:latest .
docker build -f docker/Dockerfile.consumer -t bss-consumer:latest .

# 4. Producer 배포
echo "4. Producer 배포 중..."
kubectl apply -f k8s/producer/

# 5. Consumer 배포
echo "5. Consumer 배포 중..."
kubectl apply -f k8s/consumer/

# 6. 배포 상태 확인
echo "6. 배포 상태 확인 중..."
kubectl get pods -n bss-queue-system
kubectl get services -n bss-queue-system

echo "7. 배포 완료!"
echo "   - API 주소: http://$(minikube ip):30080"
echo "   - RabbitMQ UI: kubectl port-forward svc/rabbitmq 15672:15672 -n bss-queue-system"