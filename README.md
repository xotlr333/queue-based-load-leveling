# 파일 경로: README.md

# BSS Queue-Based Load Leveling 패턴 구현

Queue-Based Load Leveling 디자인 패턴을 Azure AKS 환경에서 구현한 BSS(Business Support System) 메시지 처리 시스템입니다.

## 📋 프로젝트 개요

### 목적
- Queue-Based Load Leveling 패턴의 이해 및 구현 역량 확보
- 단일 큐 기반의 부하 분산 및 시스템 안정성 향상
- BSS 업무 적용 시나리오 개발 및 패턴 효과 검증

### 주요 특징
- **단일 큐 구조**: 4개 메시지 타입이 하나의 큐를 통해 처리
- **타입별 필터링**: 각 Consumer가 자신의 타입만 선별 처리
- **자동 스케일링**: Kubernetes HPA 기반 동적 확장
- **모니터링 On/Off**: 성능 오버헤드 최소화를 위한 선택적 모니터링
- **패턴 검증**: 자동화된 실험을 통한 패턴 효과 측정

## 🏗️ 아키텍처

```
[클라이언트] → [API Gateway] → [Message Router] → [단일 BSS 큐] → [4개 Consumer] → [처리 완료]
                                                                        ↓
                                                              [메트릭 수집 & 모니터링]
```

### 핵심 컴포넌트

1. **Producer 영역**
   - API Gateway (FastAPI): HTTP 요청 수신 및 메시지 생성
   - Message Router: 메시지 검증 및 단일 큐 전송
   - Message Producer: RabbitMQ 연동 및 메시지 발행

2. **Queue 영역**
   - RabbitMQ 단일 큐: 모든 메시지 타입 통합 처리
   - 메시지 지속성 및 고가용성 보장

3. **Consumer 영역**
   - 가입처리서비스 (SUBSCRIPTION)
   - 번호이동처리서비스 (MNP)  
   - 명의변경처리서비스 (CHANGE)
   - 해지처리서비스 (TERMINATION)

4. **모니터링 영역** (선택적)
   - 모니터링 스위치: On/Off 제어
   - 메트릭 수집기: Prometheus 연동
   - 성능 측정 및 통계 수집

5. **실험 영역**
   - 부하 생성기: 다양한 트래픽 패턴 생성
   - 패턴 검증기: 부하 평활화 효과 측정

## 🚀 빠른 시작

### 1. 환경 요구사항
- Docker Desktop
- Minikube
- kubectl
- Helm
- Python 3.9+

### 2. Minikube 환경 설정
```bash
# Minikube 시작
./scripts/setup-minikube.sh
```

### 3. 전체 시스템 배포
```bash
# 시스템 배포
./scripts/deploy.sh
```

### 4. 기본 테스트
```bash
# 패턴 검증 테스트
./scripts/run-experiments.sh

# 또는 Python 스크립트로 상세 테스트
python scripts/test-pattern.py --test-type all
```

## 📖 사용법

### API 엔드포인트

#### 메시지 전송
```bash
# 단일 메시지 전송
curl -X POST http://$(minikube ip):30080/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "타입": "SUBSCRIPTION",
    "내용": "신규 가입 요청",
    "속성들": {"고객ID": "CUST001"}
  }'

# 배치 메시지 전송
curl -X POST http://$(minikube ip):30080/api/messages/batch \
  -H "Content-Type: application/json" \
  -d '{
    "메시지목록": [
      {"타입": "SUBSCRIPTION", "내용": "가입 요청"},
      {"타입": "MNP", "내용": "번호이동 요청"}
    ]
  }'
```

#### 시스템 상태 조회
```bash
# 큐 상태
curl http://$(minikube ip):30080/api/queue/status

# 처리 통계
curl http://$(minikube ip):30080/api/stats

# 모니터링 토글
curl -X POST http://$(minikube ip):30080/api/monitoring/toggle
```

### 부하 생성 및 패턴 검증

```python
from src.experiments.load_generator import 부하생성기
from src.experiments.pattern_validator import 패턴검증기
import asyncio

async def 실험():
    # 부하 생성
    generator = 부하생성기("http://$(minikube ip):30080")
    
    # 급증 부하
    result1 = await generator.급증부하생성(1000, 60)
    
    # 지속 부하  
    result2 = await generator.지속부하생성(50, 300)
    
    # 패턴 검증
    validator = 패턴검증기("http://$(minikube ip):30080")
    
    # 부하 평활화 검증
    validation = await validator.부하평활화검증(1000, 120)
    
    # 검증 보고서
    report = validator.검증보고서생성()
    print(report)

asyncio.run(실험())
```

## 🧪 테스트

### 단위 테스트
```bash
# 전체 테스트 실행
pytest tests/

# 특정 테스트
pytest tests/test_message_models.py -v

# 커버리지 포함
pytest tests/ --cov=src --cov-report=html
```

### 통합 테스트
```bash
# Docker Compose로 로컬 테스트
cd docker
docker-compose up -d

# 테스트 실행
python scripts/test-pattern.py --api-url http://localhost:8000

# 정리
docker-compose down
```

## 📊 모니터링

### Prometheus 메트릭
- `bss_messages_processed_total`: 처리된 메시지 수
- `bss_message_processing_duration_seconds`: 메시지 처리 시간
- `bss_queue_length`: 큐 길이
- `bss_service_health`: 서비스 상태

### 대시보드 접근
```bash
# RabbitMQ 관리 UI
kubectl port-forward svc/rabbitmq 15672:15672 -n bss-queue-system
# http://localhost:15672 (admin/secretpassword)

# Minikube 대시보드
minikube dashboard
```

## 🔧 설정

### 환경 변수
```bash
# RabbitMQ 연결
RABBITMQ_URL=amqp://admin:secretpassword@rabbitmq:5672/
QUEUE_NAME=bss_single_queue

# 모니터링
MONITORING_ENABLED=true
LOG_LEVEL=INFO

# 처리 설정
MAX_RETRIES=3
BATCH_SIZE=100
PROCESSING_TIMEOUT_SEC=300
```

### Kubernetes 설정
- **Producer**: 고정 2개 Pod
- **Consumer**: HPA로 1-10개 Pod 자동 조정
- **리소스**: CPU 100m-500m, Memory 128Mi-512Mi

## 🎯 패턴 검증 결과

Queue-Based Load Leveling 패턴의 효과를 다음 지표로 측정:

1. **부하 평활화 계수**: 입력 분산 / 출력 분산 ≥ 5.0
2. **시스템 보호**: 최대 CPU 사용률 ≤ 80%
3. **메시지 손실률**: ≤ 1%
4. **처리량 증가**: ≥ 150%

## 📚 주요 학습 내용

1. **Queue-Based Load Leveling 패턴 이해**
   - 패턴의 정의, 이점, 적용 시나리오
   - 단일 큐 vs 다중 큐 아키텍처 비교

2. **Kubernetes 환경 구현**
   - HPA 기반 자동 스케일링
   - ConfigMap/Secret 설정 관리
   - 서비스 간 통신 및 로드 밸런싱

3. **메시지 큐 설계**
   - RabbitMQ 고가용성 구성
   - 메시지 지속성 및 재시도 로직
   - Consumer 패턴 및 백프레셔 처리

4. **모니터링 및 관찰성**
   - Prometheus 메트릭 설계
   - 성능 오버헤드 최소화
   - 실시간 시스템 상태 추적

## 🤝 기여

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👥 팀

- **고상철** - 전체 계획/목표/산출물 정리
- **공태식** - 서비스 배포 및 테스트  
- **권승연** - 클래스 설계 및 관리
- **윤나리** - 성능 향상 관점 및 실험 검증
- **문향은** - 기술조사 및 데이터 수집

---

**BSS Queue-Based Load Leveling Pattern Team**  
*Queue-Based Load Leveling 패턴을 통한 안정적이고 확장 가능한 메시지 처리 시스템*