from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BSS Producer API with Monitoring", version="1.0.0")

# 모니터링 상태 관리 클래스
class MonitoringSwitch:
    def __init__(self):
        self.current_state = self._get_monitoring_state()
        logger.info(f"모니터링 스위치 초기화: {'활성화' if self.current_state else '비활성화'}")
    
    def _get_monitoring_state(self) -> bool:
        """환경변수에서 모니터링 상태 확인"""
        return os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    
    def enable(self) -> Dict[str, Any]:
        """모니터링 활성화"""
        previous_state = self.current_state
        os.environ['MONITORING_ENABLED'] = 'true'
        self.current_state = True
        
        logger.info("모니터링이 활성화되었습니다")
        
        return {
            'success': True,
            'message': '모니터링이 활성화되었습니다',
            'previous_state': previous_state,
            'current_state': self.current_state,
            'timestamp': datetime.now().isoformat()
        }
    
    def disable(self) -> Dict[str, Any]:
        """모니터링 비활성화"""
        previous_state = self.current_state
        os.environ['MONITORING_ENABLED'] = 'false'
        self.current_state = False
        
        logger.info("모니터링이 비활성화되었습니다")
        
        return {
            'success': True,
            'message': '모니터링이 비활성화되었습니다',
            'previous_state': previous_state,
            'current_state': self.current_state,
            'timestamp': datetime.now().isoformat()
        }
    
    def toggle(self) -> Dict[str, Any]:
        """모니터링 상태 토글"""
        if self.current_state:
            return self.disable()
        else:
            return self.enable()
    
    def get_status(self) -> Dict[str, Any]:
        """현재 모니터링 상태 조회"""
        # 환경변수와 동기화
        env_state = self._get_monitoring_state()
        if self.current_state != env_state:
            logger.debug(f"모니터링 상태 동기화: {self.current_state} -> {env_state}")
            self.current_state = env_state
        
        return {
            'monitoring_enabled': self.current_state,
            'status_text': '활성화' if self.current_state else '비활성화',
            'environment_variable': os.getenv('MONITORING_ENABLED', 'true'),
            'timestamp': datetime.now().isoformat()
        }

# 전역 모니터링 스위치 인스턴스
monitoring_switch = MonitoringSwitch()

# 요청/응답 모델
class Message(BaseModel):
    타입: str
    내용: str
    속성들: dict = {}

class BatchMessages(BaseModel):
    메시지목록: list

# 메시지 처리 통계 (간단한 인메모리 저장)
message_stats = {
    'total_processed': 0,
    'by_type': {},
    'last_processed': None
}

@app.get("/")
async def root():
    return {
        "message": "BSS Producer API with Monitoring",
        "version": "1.0.0",
        "monitoring_enabled": monitoring_switch.get_status()['monitoring_enabled']
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "bss-producer",
        "monitoring": monitoring_switch.get_status()['monitoring_enabled'],
        "timestamp": datetime.now().isoformat()
    }

# === 메시지 처리 API ===
@app.post("/api/message")
async def send_message(message: Message):
    """단일 메시지 전송"""
    logger.info(f"메시지 수신: {message}")
    
    # 통계 업데이트 (모니터링 상태와 관계없이 기본 통계는 유지)
    message_stats['total_processed'] += 1
    message_stats['by_type'][message.타입] = message_stats['by_type'].get(message.타입, 0) + 1
    message_stats['last_processed'] = datetime.now().isoformat()
    
    # 모니터링이 활성화된 경우 추가 로깅
    if monitoring_switch.get_status()['monitoring_enabled']:
        logger.info(f"📊 [모니터링] 메시지 처리: {message.타입} - {message.내용}")
    
    return {
        "status": "success",
        "message": "메시지가 성공적으로 처리되었습니다",
        "message_type": message.타입,
        "monitoring_enabled": monitoring_switch.get_status()['monitoring_enabled']
    }

@app.post("/api/messages/batch")
async def send_batch_messages(messages: BatchMessages):
    """배치 메시지 전송"""
    processed_count = len(messages.메시지목록)
    logger.info(f"배치 메시지 수신: {processed_count}개")
    
    # 통계 업데이트
    message_stats['total_processed'] += processed_count
    
    for msg in messages.메시지목록:
        msg_type = msg.get('타입', 'UNKNOWN')
        message_stats['by_type'][msg_type] = message_stats['by_type'].get(msg_type, 0) + 1
    
    message_stats['last_processed'] = datetime.now().isoformat()
    
    # 모니터링이 활성화된 경우 추가 로깅
    if monitoring_switch.get_status()['monitoring_enabled']:
        logger.info(f"📊 [모니터링] 배치 메시지 처리: {processed_count}개")
    
    return {
        "status": "success",
        "processed": processed_count,
        "monitoring_enabled": monitoring_switch.get_status()['monitoring_enabled']
    }

# === 모니터링 제어 API ===
@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """모니터링 상태 조회"""
    status = monitoring_switch.get_status()
    return {
        "monitoring_status": status,
        "system_info": {
            "total_messages_processed": message_stats['total_processed'],
            "messages_by_type": message_stats['by_type'],
            "last_processed": message_stats['last_processed']
        }
    }

@app.post("/api/monitoring/toggle")
async def toggle_monitoring():
    """모니터링 상태 토글"""
    result = monitoring_switch.toggle()
    logger.info(f"모니터링 토글: {result}")
    return result

@app.post("/api/monitoring/enable")
async def enable_monitoring():
    """모니터링 활성화"""
    result = monitoring_switch.enable()
    logger.info(f"모니터링 활성화: {result}")
    return result

@app.post("/api/monitoring/disable")
async def disable_monitoring():
    """모니터링 비활성화"""
    result = monitoring_switch.disable()
    logger.info(f"모니터링 비활성화: {result}")
    return result

# === 시스템 상태 API ===
@app.get("/api/queue/status")
async def get_queue_status():
    """큐 상태 조회 (시뮬레이션)"""
    # 실제로는 RabbitMQ API를 호출해야 하지만, 여기서는 시뮬레이션
    return {
        "큐길이": 0,
        "초당처리율": message_stats['total_processed'] / max(1, (datetime.now().hour * 3600 + datetime.now().minute * 60 + datetime.now().second)),
        "모니터링상태": monitoring_switch.get_status()['monitoring_enabled']
    }

@app.get("/api/stats")
async def get_stats():
    """처리 통계 조회"""
    return {
        "처리된메시지": message_stats['total_processed'],
        "타입별통계": message_stats['by_type'],
        "마지막처리시간": message_stats['last_processed'],
        "대기중메시지": 0,  # 시뮬레이션
        "모니터링상태": monitoring_switch.get_status()['monitoring_enabled']
    }

# === 문서화 및 개발용 API ===
@app.get("/api/docs-info")
async def get_api_docs():
    """API 문서 정보"""
    return {
        "message": "BSS Producer API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "available_endpoints": {
            "message": "/api/message",
            "batch": "/api/messages/batch",
            "monitoring_status": "/api/monitoring/status",
            "monitoring_toggle": "/api/monitoring/toggle",
            "queue_status": "/api/queue/status",
            "stats": "/api/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
