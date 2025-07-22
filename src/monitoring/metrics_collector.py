# 파일 경로: src/monitoring/metrics_collector.py
# 메트릭 수집기 클래스

import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from src.monitoring.monitoring_switch import 모니터링스위치가져오기
from src.common.config import 설정가져오기


class 메트릭수집기:
    """
    성능 메트릭 수집 및 Prometheus 연동 클래스
    모니터링 스위치 상태에 따라 메트릭 수집 On/Off
    
    속성:
        스위치: 모니터링스위치 인스턴스
        설정: 설정 관리자 인스턴스
        메트릭들: Prometheus 메트릭 객체들
    """
    
    def __init__(self):
        """메트릭 수집기 초기화"""
        self.스위치 = 모니터링스위치가져오기()
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('메트릭수집기')
        
        # 메트릭 저장소 (모니터링 비활성화 시에도 최소한의 데이터 보관)
        self.메트릭저장소 = {
            '처리메트릭': defaultdict(list),
            '큐메트릭': deque(maxlen=1000),  # 최근 1000개 데이터만 보관
            '시스템메트릭': {}
        }
        
        # Prometheus 메트릭 정의
        self._prometheus_메트릭_초기화()
        
        # HTTP 서버 상태
        self.메트릭서버시작됨 = False
        
        self.로거.info("메트릭 수집기 초기화 완료")
    
    def _prometheus_메트릭_초기화(self):
        """Prometheus 메트릭 객체 초기화"""
        # 메시지 처리 관련 메트릭
        self.메시지처리카운터 = Counter(
            'bss_messages_processed_total',
            'Total number of messages processed',
            ['message_type', 'processor', 'status']
        )
        
        self.메시지처리시간히스토그램 = Histogram(
            'bss_message_processing_duration_seconds',
            'Time spent processing messages',
            ['message_type', 'processor'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf'))
        )
        
        # 큐 관련 메트릭
        self.큐길이게이지 = Gauge(
            'bss_queue_length',
            'Current queue length',
            ['queue_name']
        )
        
        self.큐처리율게이지 = Gauge(
            'bss_queue_processing_rate',
            'Queue processing rate (messages per second)',
            ['queue_name']
        )
        
        # 시스템 관련 메트릭
        self.모니터링상태게이지 = Gauge(
            'bss_monitoring_enabled',
            'Monitoring enabled status (1=enabled, 0=disabled)'
        )
        
        self.서비스상태게이지 = Gauge(
            'bss_service_health',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service_name', 'service_type']
        )
    
    def 처리메트릭수집(self, 타입: str, 처리시간: float, 프로세서: str = 'unknown', 상태: str = 'success') -> Dict[str, Any]:
        """
        메시지 처리 메트릭 수집
        
        Args:
            타입: 메시지 타입 (SUBSCRIPTION, MNP, CHANGE, TERMINATION)
            처리시간: 처리 시간 (초)
            프로세서: 프로세서 이름
            상태: 처리 상태 (success, failure)
            
        Returns:
            dict: 수집 결과
        """
        if not self.스위치.상태확인():
            # 모니터링 비활성화 시에도 최소한의 로컬 저장
            self.메트릭저장소['처리메트릭'][타입].append({
                '처리시간': 처리시간,
                '프로세서': 프로세서,
                '상태': 상태,
                '타임스탬프': time.time()
            })
            return {'수집됨': False, '이유': '모니터링 비활성화'}
        
        try:
            # Prometheus 메트릭 업데이트
            self.메시지처리카운터.labels(
                message_type=타입,
                processor=프로세서,
                status=상태
            ).inc()
            
            self.메시지처리시간히스토그램.labels(
                message_type=타입,
                processor=프로세서
            ).observe(처리시간)
            
            # 로컬 저장소에도 저장
            self.메트릭저장소['처리메트릭'][타입].append({
                '처리시간': 처리시간,
                '프로세서': 프로세서,
                '상태': 상태,
                '타임스탬프': time.time()
            })
            
            self.로거.debug(f"처리 메트릭 수집: {타입}, {처리시간:.3f}초, {상태}")
            
            return {
                '수집됨': True,
                '메트릭타입': '처리메트릭',
                '데이터': {
                    '타입': 타입,
                    '처리시간': 처리시간,
                    '프로세서': 프로세서,
                    '상태': 상태
                }
            }
            
        except Exception as e:
            error_msg = f"처리 메트릭 수집 실패: {e}"
            self.로거.error(error_msg)
            return {'수집됨': False, '오류': error_msg}
    
    def 큐메트릭수집(self, 길이: int, 큐이름: str = None) -> Dict[str, Any]:
        """
        큐 길이 및 상태 메트릭 수집
        
        Args:
            길이: 현재 큐 길이
            큐이름: 큐 이름 (None이면 설정에서 가져옴)
            
        Returns:
            dict: 수집 결과
        """
        큐이름 = 큐이름 or self.설정.큐설정가져오기()['큐이름']
        
        # 처리율 계산 (최근 메트릭 기반)
        처리율 = self._처리율계산(큐이름)
        
        if not self.스위치.상태확인():
            # 모니터링 비활성화 시에도 최소한의 로컬 저장
            self.메트릭저장소['큐메트릭'].append({
                '큐이름': 큐이름,
                '길이': 길이,
                '처리율': 처리율,
                '타임스탬프': time.time()
            })
            return {'수집됨': False, '이유': '모니터링 비활성화'}
        
        try:
            # Prometheus 메트릭 업데이트
            self.큐길이게이지.labels(queue_name=큐이름).set(길이)
            self.큐처리율게이지.labels(queue_name=큐이름).set(처리율)
            
            # 로컬 저장소에도 저장
            self.메트릭저장소['큐메트릭'].append({
                '큐이름': 큐이름,
                '길이': 길이,
                '처리율': 처리율,
                '타임스탬프': time.time()
            })
            
            self.로거.debug(f"큐 메트릭 수집: {큐이름}, 길이={길이}, 처리율={처리율:.2f}")
            
            return {
                '수집됨': True,
                '메트릭타입': '큐메트릭',
                '데이터': {
                    '큐이름': 큐이름,
                    '길이': 길이,
                    '처리율': 처리율
                }
            }
            
        except Exception as e:
            error_msg = f"큐 메트릭 수집 실패: {e}"
            self.로거.error(error_msg)
            return {'수집됨': False, '오류': error_msg}
    
    def 시스템메트릭수집(self, 서비스이름: str, 서비스타입: str, 상태: bool) -> Dict[str, Any]:
        """
        시스템 상태 메트릭 수집
        
        Args:
            서비스이름: 서비스 이름
            서비스타입: 서비스 타입 (producer, consumer)
            상태: 서비스 상태 (True=정상, False=비정상)
            
        Returns:
            dict: 수집 결과
        """
        try:
            # 모니터링 상태 업데이트
            self.모니터링상태게이지.set(1 if self.스위치.상태확인() else 0)
            
            if self.스위치.상태확인():
                # 서비스 상태 업데이트
                self.서비스상태게이지.labels(
                    service_name=서비스이름,
                    service_type=서비스타입
                ).set(1 if 상태 else 0)
            
            # 로컬 저장소에 저장
            self.메트릭저장소['시스템메트릭'][서비스이름] = {
                '서비스타입': 서비스타입,
                '상태': 상태,
                '마지막업데이트': time.time()
            }
            
            return {
                '수집됨': True,
                '메트릭타입': '시스템메트릭',
                '데이터': {
                    '서비스이름': 서비스이름,
                    '서비스타입': 서비스타입,
                    '상태': 상태
                }
            }
            
        except Exception as e:
            error_msg = f"시스템 메트릭 수집 실패: {e}"
            self.로거.error(error_msg)
            return {'수집됨': False, '오류': error_msg}
    
    def 메트릭서버시작(self, 포트: Optional[int] = None) -> Dict[str, Any]:
        """
        Prometheus 메트릭 HTTP 서버 시작
        
        Args:
            포트: HTTP 서버 포트 (None이면 설정에서 가져옴)
            
        Returns:
            dict: 서버 시작 결과
        """
        if self.메트릭서버시작됨:
            return {
                '성공': True,
                '메시지': '메트릭 서버가 이미 실행 중입니다'
            }
        
        try:
            포트 = 포트 or self.설정.포트설정가져오기()['메트릭']
            
            start_http_server(포트)
            self.메트릭서버시작됨 = True
            
            self.로거.info(f"Prometheus 메트릭 서버 시작됨: 포트 {포트}")
            
            return {
                '성공': True,
                '메시지': f'메트릭 서버가 포트 {포트}에서 시작되었습니다',
                '포트': 포트,
                '엔드포인트': f'http://localhost:{포트}/metrics'
            }
            
        except Exception as e:
            error_msg = f"메트릭 서버 시작 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
    
    def 메트릭통계조회(self) -> Dict[str, Any]:
        """
        수집된 메트릭 통계 조회
        
        Returns:
            dict: 메트릭 통계 정보
        """
        try:
            # 처리 메트릭 통계
            처리통계 = {}
            for 타입, 메트릭목록 in self.메트릭저장소['처리메트릭'].items():
                if 메트릭목록:
                    총개수 = len(메트릭목록)
                    성공개수 = sum(1 for m in 메트릭목록 if m['상태'] == 'success')
                    평균처리시간 = sum(m['처리시간'] for m in 메트릭목록) / 총개수
                    
                    처리통계[타입] = {
                        '총처리개수': 총개수,
                        '성공개수': 성공개수,
                        '실패개수': 총개수 - 성공개수,
                        '성공률': round(성공개수 / 총개수 * 100, 2),
                        '평균처리시간': round(평균처리시간, 3)
                    }
            
            # 큐 메트릭 통계
            큐통계 = {}
            if self.메트릭저장소['큐메트릭']:
                최근큐메트릭 = list(self.메트릭저장소['큐메트릭'])[-10:]  # 최근 10개
                if 최근큐메트릭:
                    평균길이 = sum(m['길이'] for m in 최근큐메트릭) / len(최근큐메트릭)
                    평균처리율 = sum(m['처리율'] for m in 최근큐메트릭) / len(최근큐메트릭)
                    
                    큐통계 = {
                        '평균큐길이': round(평균길이, 1),
                        '평균처리율': round(평균처리율, 2),
                        '최근측정개수': len(최근큐메트릭)
                    }
            
            return {
                '모니터링상태': self.스위치.상태확인(),
                '메트릭서버상태': self.메트릭서버시작됨,
                '처리통계': 처리통계,
                '큐통계': 큐통계,
                '시스템통계': self.메트릭저장소['시스템메트릭'],
                '수집시간': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"메트릭 통계 조회 실패: {e}"
            self.로거.error(error_msg)
            return {'오류': error_msg}
    
    def _처리율계산(self, 큐이름: str) -> float:
        """
        최근 메트릭을 기반으로 처리율 계산 (메시지/초)
        
        Args:
            큐이름: 큐 이름
            
        Returns:
            float: 처리율 (메시지/초)
        """
        try:
            # 최근 1분간의 처리 메트릭 확인
            현재시간 = time.time()
            최근메트릭들 = []
            
            for 타입메트릭들 in self.메트릭저장소['처리메트릭'].values():
                for 메트릭 in 타입메트릭들:
                    if 현재시간 - 메트릭['타임스탬프'] <= 60:  # 최근 1분
                        최근메트릭들.append(메트릭)
            
            if not 최근메트릭들:
                return 0.0
            
            # 1분간 처리된 메시지 수를 초당 처리율로 변환
            처리율 = len(최근메트릭들) / 60.0
            return round(처리율, 2)
            
        except Exception:
            return 0.0


# 전역 메트릭 수집기 인스턴스 (싱글톤)
_메트릭수집기_인스턴스 = None


def 메트릭수집기가져오기() -> 메트릭수집기:
    """
    전역 메트릭 수집기 인스턴스 반환 (싱글톤)
    
    Returns:
        메트릭수집기: 메트릭 수집기 인스턴스
    """
    global _메트릭수집기_인스턴스
    if _메트릭수집기_인스턴스 is None:
        _메트릭수집기_인스턴스 = 메트릭수집기()
    return _메트릭수집기_인스턴스


def 메트릭수집기초기화():
    """메트릭 수집기 인스턴스 초기화 (테스트용)"""
    global _메트릭수집기_인스턴스
    _메트릭수집기_인스턴스 = None