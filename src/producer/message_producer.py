# 파일 경로: src/producer/message_producer.py
# BSS 메시지 생산자 클래스

import pika
import json
import time
from typing import Optional, Dict, Any
from src.common.message_models import BSS메시지
from src.common.config import 설정가져오기


class BSS메시지생산자:
    """
    RabbitMQ를 사용한 BSS 메시지 생산자 클래스
    
    속성:
        큐연결: RabbitMQ 연결 객체
        채널: RabbitMQ 채널 객체
        설정: 설정 관리자 인스턴스
    """
    
    def __init__(self):
        """BSS 메시지 생산자 초기화"""
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('BSS메시지생산자')
        self.큐연결: Optional[pika.BlockingConnection] = None
        self.채널: Optional[pika.channel.Channel] = None
        self._연결생성()
    
    def _연결생성(self):
        """RabbitMQ 연결 및 채널 생성"""
        try:
            # 연결 파라미터 설정
            connection_params = pika.URLParameters(self.설정.연결문자열가져오기())
            
            # 연결 생성
            self.큐연결 = pika.BlockingConnection(connection_params)
            self.채널 = self.큐연결.channel()
            
            # 큐 선언
            큐설정 = self.설정.큐설정가져오기()
            self.채널.queue_declare(
                queue=큐설정['큐이름'],
                durable=큐설정['내구성'],
                auto_delete=큐설정['자동삭제'],
                exclusive=큐설정['배타적']
            )
            
            self.로거.info(f"RabbitMQ 연결 성공: {큐설정['큐이름']}")
            
        except Exception as e:
            self.로거.error(f"RabbitMQ 연결 실패: {e}")
            raise
    
    def 연결확인(self) -> bool:
        """
        RabbitMQ 연결 상태 확인
        
        Returns:
            bool: 연결이 정상이면 True, 그렇지 않으면 False
        """
        try:
            if self.큐연결 and not self.큐연결.is_closed:
                # 간단한 heartbeat 확인
                self.큐연결.process_data_events(time_limit=0)
                return True
            return False
        except Exception as e:
            self.로거.warning(f"연결 상태 확인 실패: {e}")
            return False
    
    def _연결재시도(self, 최대시도: int = 3, 지연시간: int = 5) -> bool:
        """
        연결 재시도
        
        Args:
            최대시도: 최대 재시도 횟수
            지연시간: 재시도 간 지연 시간(초)
            
        Returns:
            bool: 재연결 성공 여부
        """
        for 시도 in range(최대시도):
            try:
                self.로거.info(f"연결 재시도 {시도 + 1}/{최대시도}")
                self._연결해제()
                time.sleep(지연시간)
                self._연결생성()
                return True
            except Exception as e:
                self.로거.warning(f"재시도 {시도 + 1} 실패: {e}")
                if 시도 == 최대시도 - 1:
                    self.로거.error("모든 재시도 실패")
                    return False
        return False
    
    def 큐전송(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        메시지를 RabbitMQ 단일 큐로 전송
        
        Args:
            메시지: 전송할 BSS 메시지
            
        Returns:
            dict: 전송 결과 {'성공': bool, '메시지': str, '메시지아이디': str}
        """
        try:
            # 메시지 유효성 검증
            if not 메시지.메시지검증():
                return {
                    '성공': False,
                    '메시지': '메시지 유효성 검증 실패',
                    '메시지아이디': 메시지.아이디
                }
            
            # 연결 상태 확인 및 재연결
            if not self.연결확인():
                if not self._연결재시도():
                    return {
                        '성공': False,
                        '메시지': 'RabbitMQ 연결 실패',
                        '메시지아이디': 메시지.아이디
                    }
            
            # 메시지 발행
            큐설정 = self.설정.큐설정가져오기()
            
            # 메시지 속성 설정
            properties = pika.BasicProperties(
                message_id=메시지.아이디,
                content_type='application/json',
                delivery_mode=2,  # 메시지 지속성
                timestamp=int(메시지.생성시간.timestamp()),
                headers={
                    'message_type': 메시지.타입,
                    'created_at': 메시지.생성시간.isoformat()
                }
            )
            
            # 메시지 발행
            self.채널.basic_publish(
                exchange='',
                routing_key=큐설정['큐이름'],
                body=메시지.to_json(),
                properties=properties
            )
            
            self.로거.info(f"메시지 전송 성공: {메시지.타입} - {메시지.아이디}")
            
            return {
                '성공': True,
                '메시지': '메시지 전송 성공',
                '메시지아이디': 메시지.아이디
            }
            
        except Exception as e:
            error_msg = f"메시지 전송 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg,
                '메시지아이디': 메시지.아이디
            }
    
    def 배치전송(self, 메시지목록: list[BSS메시지]) -> Dict[str, Any]:
        """
        여러 메시지를 배치로 전송
        
        Args:
            메시지목록: 전송할 BSS 메시지 리스트
            
        Returns:
            dict: 배치 전송 결과
        """
        성공개수 = 0
        실패개수 = 0
        결과목록 = []
        
        for 메시지 in 메시지목록:
            결과 = self.큐전송(메시지)
            결과목록.append(결과)
            
            if 결과['성공']:
                성공개수 += 1
            else:
                실패개수 += 1
        
        return {
            '전체개수': len(메시지목록),
            '성공개수': 성공개수,
            '실패개수': 실패개수,
            '성공률': round(성공개수 / len(메시지목록) * 100, 2) if 메시지목록 else 0,
            '상세결과': 결과목록
        }
    
    def 큐상태확인(self) -> Dict[str, Any]:
        """
        큐 상태 정보 조회
        
        Returns:
            dict: 큐 상태 정보
        """
        try:
            if not self.연결확인():
                return {'오류': 'RabbitMQ 연결 실패'}
            
            큐설정 = self.설정.큐설정가져오기()
            method = self.채널.queue_declare(
                queue=큐설정['큐이름'],
                passive=True  # 큐 상태만 확인
            )
            
            return {
                '큐이름': 큐설정['큐이름'],
                '메시지개수': method.method.message_count,
                '소비자개수': method.method.consumer_count
            }
            
        except Exception as e:
            self.로거.error(f"큐 상태 확인 실패: {e}")
            return {'오류': str(e)}
    
    def _연결해제(self):
        """RabbitMQ 연결 해제"""
        try:
            if self.채널 and not self.채널.is_closed:
                self.채널.close()
            if self.큐연결 and not self.큐연결.is_closed:
                self.큐연결.close()
        except Exception as e:
            self.로거.warning(f"연결 해제 중 오류: {e}")
    
    def __del__(self):
        """소멸자에서 연결 해제"""
        self._연결해제()