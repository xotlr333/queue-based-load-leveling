# ���� ���: scripts/cleanup.sh
# ȯ�� ���� ��ũ��Ʈ

#!/bin/bash

echo "=== BSS Queue-Based Load Leveling ���� ȯ�� ���� ==="

# 1. Kubernetes ���ҽ� ����
echo "1. Kubernetes ���ҽ� ���� ��..."
kubectl delete namespace bss-queue-system --ignore-not-found=true

# 2. Helm ������ ����
echo "2. Helm ������ ���� ��..."
helm uninstall rabbitmq -n bss-queue-system --ignore-not-found

# 3. Docker �̹��� ����
echo "3. Docker �̹��� ���� ��..."
docker rmi bss-producer:latest bss-consumer:latest 2>/dev/null || true

# 4. Minikube ���� (������)
read -p "Minikube�� �����Ͻðڽ��ϱ�? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "4. Minikube ���� ��..."
    minikube stop
fi

echo "���� �Ϸ�!"