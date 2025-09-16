# ���� ���: scripts/run-experiments.sh
# ���� ���� ���� ���� ��ũ��Ʈ

#!/bin/bash

set -e

echo "=== Queue-Based Load Leveling ���� ���� ���� ==="

# API Gateway �ּ� ����
API_URL="http://$(minikube ip):30080"

echo "1. �ý��� ���� Ȯ�� ��..."
curl -f "$API_URL/health" > /dev/null
echo "   �ý��� ���� ���� Ȯ�ε�"

echo "2. �⺻ �޽��� ���� �׽�Ʈ..."
curl -X POST "$API_URL/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "Ÿ��": "SUBSCRIPTION",
    "����": "�׽�Ʈ ���� ��û"
  }'

echo "3. ť ���� Ȯ��..."
curl -s "$API_URL/api/queue/status" | jq '.'

echo "4. ��ġ �޽��� ���� �׽�Ʈ..."
curl -X POST "$API_URL/api/messages/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "�޽������": [
      {"Ÿ��": "SUBSCRIPTION", "����": "���� ��û 1"},
      {"Ÿ��": "MNP", "����": "��ȣ�̵� ��û 1"},
      {"Ÿ��": "CHANGE", "����": "���Ǻ��� ��û 1"},
      {"Ÿ��": "TERMINATION", "����": "���� ��û 1"}
    ]
  }'

echo "5. �ý��� ��� Ȯ��..."
curl -s "$API_URL/api/stats" | jq '.'

echo "���� �Ϸ�! �߰� ���� �׽�Ʈ�� Python ��ũ��Ʈ�� ����ϼ���:"
echo "  python -c \"
from src.experiments.load_generator import ���ϻ�����
import asyncio

async def ����():
    generator = ���ϻ�����('$API_URL')
    result = await generator.�������ϻ���(100, 30)
    print('���� ���� �׽�Ʈ ���:', result)

asyncio.run(����())
\""