# 파일 경로: src/consumer/base_processor.py
# 기본 처리 서비스 클래스 (부모 클래스)

import pika
import json
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.common.message_models import BSS메시지
from src.common.config import 설정가져오기


class 기본처리서비스(ABC):
    """
    BSS 메시지 처리를 위한 추상 기본 클래스
    모든 Consumer 서비스의 부모 클래스
    
    속성:
        처리타입 (str): 처리할 메시지 타입
        설정: 설정 관리자 인스턴스
        연결: RabbitMQ 연결 객체
        채널: RabbitMQ 채널 객체
        처리중단플래그: 처리 중단 신호
    """
    
    def __init__(self, 처리타입: str):
        """
        기본 처리 서비스 초기화
        
        Args:
            처리타입: 처리할 메시지 타입 (SUBSCRIPTION, MNP, CHANGE, TERMINATION)
        """
        self.처리타입 = 처리타입.upper()
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정(f'{처리타입}처리서비스')
        
        # RabbitMQ 연결 관련
        self.연결: Optional[pika.BlockingConnection] = None
        self.채널: Optional[pika.channel.Channel] = None
        
        # 처리 통계
        self.처리통계 = {
            '총처리개수': 0,
            '성공처리개수': 0,
            '실패처리개수': 0,
            '시작시간': datetime.now(),
            '마지막처리시간': None
        }
        
        # 제어 플래그
        self.처리중단플래그 = threading.Event()
        self.처리스레드: Optional[threading.Thread] = None
        
        self.로거.info(f"{self.처리타입} 처리 서비스 초기화 완료")
    
    def _연결생성(self):
        """RabbitMQ 연결 및 채널 생성"""
        try:
            # 연결 파라미터 설정
            connection_params = pika.URLParameters(self.설정.연결문자열가져오기())
            
            # 연결 생성
            self.연결 = pika.BlockingConnection(connection_params)
            self.채널 = self.연결.channel()
            
            # 큐 선언
            큐설정 = self.설정.큐설정가져오기()
            self.채널.queue_declare(
                queue=큐설정['큐이름'],
                durable=큐설정['내구성'],
                auto_delete=큐설정['자동삭제'],
                exclusive=큐설정['배타적']
            )
            
            # Prefetch 설정
            처리설정 = self.설정.처리설정가져오기()
            self.채널.basic_qos(prefetch_count=처리설정['프리페치카운트'])
            
            self.로거.info(f"RabbitMQ 연결 성공: {큐설정['큐이름']}")
            
        except Exception as e:
            self.로거.error(f"RabbitMQ 연결 실패: {e}")
            raise
    
    def 메시지처리시작(self):
        """
        메시지 처리 시작 (비동기)
        """
        if self.처리스레드 and self.처리스레드.is_alive():
            self.로거.warning("이미 메시지 처리가 실행 중입니다")
            return
        
        self.처리중단플래그.clear()
        self.처리스레드 = threading.Thread(target=self._메시지처리루프, daemon=True)
        self.처리스레드.start()
        self.로거.info(f"{self.처리타입} 메시지 처리 시작")
    
    def 메시지처리중지(self):
        """메시지 처리 중지"""
        self.처리중단플래그.set()
        
        if self.처리스레드 and self.처리스레드.is_alive():
            self.로거.info("메시지 처리 중지 요청...")
            self.처리스레드.join(timeout=30)  # 30초 대기
            
        self._연결해제()
        self.로거.info(f"{self.처리타입} 메시지 처리 중지 완료")
    
    def _메시지처리루프(self):
        """메시지 처리 메인 루프"""
        try:
            # RabbitMQ 연결 생성
            self._연결생성()
            
            # Consumer 설정
            큐설정 = self.설정.큐설정가져오기()
            self.채널.basic_consume(
                queue=큐설정['큐이름'],
                on_message_callback=self._메시지콜백,
                auto_ack=False  # 수동 ACK
            )
            
            self.로거.info(f"{self.처리타입} Consumer 대기 중...")
            
            # 메시지 처리 루프
            while not self.처리중단플래그.is_set():
                try:
                    # 0.1초 타임아웃으로 메시지 처리
                    self.연결.process_data_events(time_limit=0.1)
                except Exception as e:
                    self.로거.error(f"메시지 처리 중 오류: {e}")
                    time.sleep(1)  # 오류 시 잠시 대기
                    
        except Exception as e:
            self.로거.error(f"메시지 처리 루프 실패: {e}")
        finally:
            self._연결해제()
    
    def _메시지콜백(self, channel, method, properties, body):
        """
        RabbitMQ 메시지 콜백 함수
        
        Args:
            channel: RabbitMQ 채널
            method: 메시지 메소드
            properties: 메시지 속성
            body: 메시지 본문
        """
        메시지아이디 = properties.message_id or "unknown"
        
        try:
            # JSON에서 BSS메시지 복원
            메시지 = BSS메시지.from_json(body.decode('utf-8'))
            
            # 메시지 타입 필터링
            if not 메시지.타입확인(self.처리타입):
                # 해당 타입이 아닌 메시지는 reject (다른 Consumer가 처리)
                channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return
            
            # 메시지 처리 시작 시간 기록
            처리시작시간 = time.time()
            
            # 실제 메시지 처리
            처리결과 = self.메시지처리(메시지)
            
            # 처리 시간 계산
            처리시간 = self.처리시간측정(처리시작시간)
            
            # 처리 결과에 따라 ACK/NACK
            if 처리결과['성공']:
                channel.basic_ack(delivery_tag=method.delivery_tag)
                self.처리통계['성공처리개수'] += 1
                self.로거.info(
                    f"메시지 처리 성공: {메시지.타입} - {메시지아이디} "
                    f"(처리시간: {처리시간['처리시간']:.2f}초)"
                )
            else:
                # 재시도 로직
                재시도횟수 = 메시지.속성들.get('재시도횟수', 0)
                최대재시도 = self.설정.처리설정가져오기()['최대재시도']
                
                if 재시도횟수 < 최대재시도:
                    # 재시도 카운트 증가 후 requeue
                    메시지.속성들['재시도횟수'] = 재시도횟수 + 1
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                    self.로거.warning(
                        f"메시지 처리 실패 - 재시도 {재시도횟수 + 1}/{최대재시도}: "
                        f"{메시지.타입} - {메시지아이디}"
                    )
                else:
                    # 최대 재시도 초과 - Dead Letter로 이동
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                    self.로거.error(
                        f"메시지 처리 최종 실패 (최대 재시도 초과): "
                        f"{메시지.타입} - {메시지아이디}"
                    )
                
                self.처리통계['실패처리개수'] += 1
            
            # 통계 업데이트
            self.처리통계['총처리개수'] += 1
            self.처리통계['마지막처리시간'] = datetime.now()
            
        except Exception as e:
            self.로거.error(f"메시지 콜백 처리 실패: {e}")
            # 파싱 실패 등의 경우 메시지 reject (requeue하지 않음)
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            self.처리통계['실패처리개수'] += 1
    
    @abstractmethod
    def 메시지처리(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        실제 메시지 처리 로직 (하위 클래스에서 구현)
        
        Args:
            메시지: 처리할 BSS 메시지
            
        Returns:
            dict: 처리 결과 {'성공': bool, '메시지': str, '결과데이터': any}
        """
        pass
    
    @abstractmethod
    def 처리시뮬레이션(self) -> Dict[str, Any]:
        """
        처리 시뮬레이션 (하위 클래스에서 구현)
        실제 DB 작업 대신 시뮬레이션 수행
        
        Returns:
            dict: 시뮬레이션 결과
        """
        pass
    
    def 처리시간측정(self, 시작시간: float) -> Dict[str, Any]:
        """
        메시지 처리 시간 측정 및 기록
        
        Args:
            시작시간: 처리 시작 시간 (time.time())
            
        Returns:
            dict: 시간 측정 결과
        """
        종료시간 = time.time()
        처리시간 = 종료시간 - 시작시간
        
        # 모니터링이 활성화된 경우 상세 로깅
        if self.설정.모니터링상태확인():
            self.로거.debug(f"{self.처리타입} 처리시간: {처리시간:.3f}초")
        
        return {
            '시작시간': 시작시간,
            '종료시간': 종료시간,
            '처리시간': 처리시간,
            '타임스탬프': datetime.now().isoformat()
        }
    
    def 처리통계조회(self) -> Dict[str, Any]:
        """
        처리 통계 정보 조회
        
        Returns:
            dict: 처리 통계 정보
        """
        총처리개수 = self.처리통계['총처리개수']
        성공률 = round(
            self.처리통계['성공처리개수'] / 총처리개수 * 100, 2
        ) if 총처리개수 > 0 else 0
        
        실행시간 = datetime.now() - self.처리통계['시작시간']
        
        return {
            '처리타입': self.처리타입,
            '기본통계': {
                '총처리개수': 총처리개수,
                '성공처리개수': self.처리통계['성공처리개수'],
                '실패처리개수': self.처리통계['실패처리개수'],
                '성공률': f"{성공률}%"
            },
            '시간정보': {
                '시작시간': self.처리통계['시작시간'].isoformat(),
                '마지막처리시간': (
                    self.처리통계['마지막처리시간'].isoformat() 
                    if self.처리통계['마지막처리시간'] else None
                ),
                '총실행시간': str(실행시간)
            },
            '상태정보': {
                '처리중': self.처리스레드.is_alive() if self.처리스레드 else False,
                '연결상태': not self.연결.is_closed if self.연결 else False
            }
        }
    
    def 연결상태확인(self) -> bool:
        """
        RabbitMQ 연결 상태 확인
        
        Returns:
            bool: 연결이 정상이면 True
        """
        try:
            if self.연결 and not self.연결.is_closed:
                self.연결.process_data_events(time_limit=0)
                return True
            return False
        except Exception:
            return False
    
    def _연결해제(self):
        """RabbitMQ 연결 해제"""
        try:
            if self.채널 and not self.채널.is_closed:
                self.채널.close()
            if self.연결 and not self.연결.is_closed:
                self.연결.close()
        except Exception as e:
            self.로거.warning(f"연결 해제 중 오류: {e}")
    
    def __del__(self):
        """소멸자에서 처리 중지 및 연결 해제"""
        self.메시지처리중지()