# 파일 경로: src/common/config.py
# 설정 관리자 클래스

import os
from typing import Optional, Dict, Any
import logging


class 설정관리자:
    """
    Queue-Based Load Leveling 패턴을 위한 설정 관리 클래스
    
    속성:
        큐연결문자열 (str): RabbitMQ 연결 문자열
        모니터링활성화 (bool): 모니터링 활성화 여부
    """
    
    def __init__(self):
        """설정 관리자 초기화"""
        self._load_config()
    
    def _load_config(self):
        """환경 변수에서 설정 로드"""
        # RabbitMQ 연결 설정
        self.큐연결문자열 = os.getenv(
            'RABBITMQ_URL',
            'amqp://admin:secretpassword@localhost:5672/'
        )
        
        # 모니터링 설정
        self.모니터링활성화 = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
        
        # 큐 설정
        self.큐이름 = os.getenv('QUEUE_NAME', 'bss_single_queue')
        self.큐내구성 = os.getenv('QUEUE_DURABLE', 'true').lower() == 'true'
        
        # 메시지 설정
        self.최대재시도횟수 = int(os.getenv('MAX_RETRIES', '3'))
        self.재시도지연시간 = int(os.getenv('RETRY_DELAY_MS', '5000'))
        self.메시지TTL = int(os.getenv('MESSAGE_TTL', '3600000'))  # 1시간
        
        # 처리 설정
        self.배치크기 = int(os.getenv('BATCH_SIZE', '100'))
        self.처리타임아웃 = int(os.getenv('PROCESSING_TIMEOUT_SEC', '300'))  # 5분
        self.프리페치카운트 = int(os.getenv('CONSUMER_PREFETCH_COUNT', '10'))
        
        # 로깅 설정
        self.로그레벨 = os.getenv('LOG_LEVEL', 'INFO')
        
        # API 설정
        self.API포트 = int(os.getenv('API_PORT', '8000'))
        self.메트릭포트 = int(os.getenv('METRICS_PORT', '9090'))
        self.헬스체크포트 = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
    
    def 연결문자열가져오기(self) -> str:
        """
        RabbitMQ 연결 문자열 반환
        
        Returns:
            str: RabbitMQ 연결 문자열
        """
        return self.큐연결문자열
    
    def 모니터링상태확인(self) -> bool:
        """
        현재 모니터링 활성화 상태 반환
        
        Returns:
            bool: 모니터링이 활성화되어 있으면 True, 그렇지 않으면 False
        """
        return self.모니터링활성화
    
    def 큐설정가져오기(self) -> Dict[str, Any]:
        """
        큐 설정 정보 반환
        
        Returns:
            dict: 큐 설정 딕셔너리
        """
        return {
            '큐이름': self.큐이름,
            '내구성': self.큐내구성,
            '자동삭제': False,
            '배타적': False,
            'TTL': self.메시지TTL
        }
    
    def 처리설정가져오기(self) -> Dict[str, Any]:
        """
        메시지 처리 설정 정보 반환
        
        Returns:
            dict: 처리 설정 딕셔너리
        """
        return {
            '배치크기': self.배치크기,
            '타임아웃': self.처리타임아웃,
            '프리페치카운트': self.프리페치카운트,
            '최대재시도': self.최대재시도횟수,
            '재시도지연': self.재시도지연시간
        }
    
    def 포트설정가져오기(self) -> Dict[str, int]:
        """
        포트 설정 정보 반환
        
        Returns:
            dict: 포트 설정 딕셔너리
        """
        return {
            'API': self.API포트,
            '메트릭': self.메트릭포트,
            '헬스체크': self.헬스체크포트
        }
    
    def 로거설정(self, 이름: str) -> logging.Logger:
        """
        로거 설정 및 반환
        
        Args:
            이름: 로거 이름
            
        Returns:
            logging.Logger: 설정된 로거
        """
        logger = logging.getLogger(이름)
        
        if not logger.handlers:
            # 핸들러가 없는 경우에만 설정
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        # 로그 레벨 설정
        log_level = getattr(logging, self.로그레벨.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        return logger
    
    def 설정정보출력(self) -> Dict[str, Any]:
        """
        전체 설정 정보를 딕셔너리로 반환 (디버깅용)
        
        Returns:
            dict: 전체 설정 정보
        """
        return {
            '연결': {
                '큐연결문자열': self.큐연결문자열,
                '큐이름': self.큐이름
            },
            '모니터링': {
                '활성화': self.모니터링활성화
            },
            '큐설정': self.큐설정가져오기(),
            '처리설정': self.처리설정가져오기(),
            '포트설정': self.포트설정가져오기(),
            '로깅': {
                '레벨': self.로그레벨
            }
        }
    
    def 환경변수업데이트(self, 키: str, 값: str):
        """
        환경 변수 업데이트 및 설정 재로드
        
        Args:
            키: 환경 변수 키
            값: 설정할 값
        """
        os.environ[키] = 값
        self._load_config()
    
    def 모니터링토글(self) -> bool:
        """
        모니터링 상태를 토글하고 새로운 상태 반환
        
        Returns:
            bool: 변경된 모니터링 상태
        """
        new_state = not self.모니터링활성화
        self.환경변수업데이트('MONITORING_ENABLED', str(new_state).lower())
        return self.모니터링활성화


# 전역 설정 인스턴스 (싱글톤 패턴)
_설정_인스턴스: Optional[설정관리자] = None


def 설정가져오기() -> 설정관리자:
    """
    전역 설정 인스턴스 반환 (싱글톤)
    
    Returns:
        설정관리자: 설정 관리자 인스턴스
    """
    global _설정_인스턴스
    if _설정_인스턴스 is None:
        _설정_인스턴스 = 설정관리자()
    return _설정_인스턴스


def 설정초기화():
    """설정 인스턴스 초기화 (테스트용)"""
    global _설정_인스턴스
    _설정_인스턴스 = None