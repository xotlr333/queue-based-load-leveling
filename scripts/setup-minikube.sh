#!/bin/bash

set -e

echo "=== BSS Queue-Based Load Leveling 프로젝트 - Minikube 환경 설정 ==="

# Minikube 시작
echo "1. Minikube 시작 중..."
minikube start --memory=6144 --cpus=4 --disk-size=20g --driver=docker

# 애드온 활성화
echo "2. 필수 애드온 활성화 중..."
minikube addons enable ingress
minikube addons enable metrics-server

# Docker 환경 설정
echo "3. Docker 환경 설정 중..."
eval $(minikube docker-env)

# Helm 설치 확인
echo "4. Helm 설치 확인 중..."
if ! command -v helm &> /dev/null; then
    echo "Helm이 설치되어 있지 않습니다. 설치를 시작합니다..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo "5. Minikube 설정 완료!"
echo "   - IP: $(minikube ip)"
echo "   - Dashboard: minikube dashboard"
echo "   - 상태: $(minikube status)"