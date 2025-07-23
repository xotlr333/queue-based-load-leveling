# 파일 경로: src/experiments/load_generator.py
# 부하 생성기 클래스

import asyncio
import aiohttp
import time
import random
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.common.message_models import BSS메시지, MessageType
from src.common.config import 설정가져오기


class 부하생성기:
    """
    Queue-Based Load Leveling 패턴 검증을 위한 부하 생성기
    다양한 패턴의 트래픽을 생성하여 시스템 테스트
    
    속성:
        게이트웨이주소: API Gateway 주소
        설정: 설정 관리자 인스턴스
        실행상태: 현재 부하 생성 실행 상태
    """
    
    def __init__(self, 게이트웨이주소: str = None):
        """
        부하 생성기 초기화
        
        Args:
            게이트웨이주소: API Gateway 주소 (None이면 기본값 사용)
        """
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('부하생성기')
        
        # API Gateway 주소 설정
        if 게이트웨이주소:
            self.게이트웨이주소 = 게이트웨이주소
        else:
            포트 = self.설정.포트설정가져오기()['API']
            self.게이트웨이주소 = f"http://localhost:{포트}"
        
        # 실행 상태 관리
        self.실행상태 = {
            '실행중': False,
            '중지신호': threading.Event(),
            '현재작업': None,
            '시작시간': None
        }
        
        # 부하 생성 통계
        self.부하통계 = {
            '총요청수': 0,
            '성공요청수': 0,
            '실패요청수': 0,
            '평균응답시간': 0.0,
            '타입별통계': {타입.value: 0 for 타입 in MessageType}
        }
        
        self.로거.info(f"부하 생성기 초기화 완료: {self.게이트웨이주소}")
    
    async def 급증부하생성(self, 개수: int, 기간: int = 60, 메시지타입: Optional[str] = None) -> Dict[str, Any]:
        """
        지정된 기간 동안 대량 메시지를 급속 투입
        
        Args:
            개수: 전송할 메시지 개수
            기간: 전송 기간 (초)
            메시지타입: 특정 메시지 타입 (None이면 랜덤)
            
        Returns:
            dict: 부하 생성 결과
        """
        if self.실행상태['실행중']:
            return {
                '성공': False,
                '메시지': '이미 부하 생성이 실행 중입니다'
            }
        
        try:
            self._실행상태설정(True, f'급증부하생성({개수}개/{기간}초)')
            
            self.로거.info(f"급증 부하 생성 시작: {개수}개 메시지를 {기간}초에 전송")
            
            # 메시지 생성
            메시지목록 = self._메시지목록생성(개수, 메시지타입)
            
            # 병렬 전송
            시작시간 = time.time()
            결과들 = await self._병렬메시지전송(메시지목록, 기간)
            종료시간 = time.time()
            
            # 결과 분석
            결과분석 = self._결과분석(결과들, 시작시간, 종료시간)
            
            self.로거.info(f"급증 부하 생성 완료: {결과분석['성공률']:.1f}% 성공")
            
            return {
                '성공': True,
                '메시지': '급증 부하 생성 완료',
                '부하타입': '급증부하',
                '설정': {
                    '메시지개수': 개수,
                    '기간': 기간,
                    '메시지타입': 메시지타입 or '랜덤'
                },
                '결과': 결과분석
            }
            
        except Exception as e:
            error_msg = f"급증 부하 생성 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
        finally:
            self._실행상태설정(False)
    
    async def 지속부하생성(self, 초당비율: int, 지속시간: int = 300, 메시지타입: Optional[str] = None) -> Dict[str, Any]:
        """
        일정한 비율로 지속적인 메시지 전송
        
        Args:
            초당비율: 초당 전송할 메시지 수
            지속시간: 지속 시간 (초)
            메시지타입: 특정 메시지 타입 (None이면 랜덤)
            
        Returns:
            dict: 부하 생성 결과
        """
        if self.실행상태['실행중']:
            return {
                '성공': False,
                '메시지': '이미 부하 생성이 실행 중입니다'
            }
        
        try:
            self._실행상태설정(True, f'지속부하생성({초당비율}/초, {지속시간}초)')
            
            self.로거.info(f"지속 부하 생성 시작: {초당비율}/초로 {지속시간}초간 전송")
            
            시작시간 = time.time()
            전체결과들 = []
            
            # 1초 간격으로 메시지 전송
            for 초 in range(지속시간):
                if self.실행상태['중지신호'].is_set():
                    self.로거.info("지속 부하 생성 중지 신호 수신")
                    break
                
                # 해당 초에 전송할 메시지 생성
                메시지목록 = self._메시지목록생성(초당비율, 메시지타입)
                
                # 1초 동안 메시지 전송
                배치시작시간 = time.time()
                결과들 = await self._병렬메시지전송(메시지목록, 1)
                전체결과들.extend(결과들)
                
                # 정확한 1초 간격 유지
                경과시간 = time.time() - 배치시작시간
                if 경과시간 < 1.0:
                    await asyncio.sleep(1.0 - 경과시간)
                
                # 진행 상황 로깅 (10초마다)
                if (초 + 1) % 10 == 0:
                    self.로거.info(f"지속 부하 진행: {초 + 1}/{지속시간}초 완료")
            
            종료시간 = time.time()
            
            # 결과 분석
            결과분석 = self._결과분석(전체결과들, 시작시간, 종료시간)
            
            self.로거.info(f"지속 부하 생성 완료: {결과분석['성공률']:.1f}% 성공")
            
            return {
                '성공': True,
                '메시지': '지속 부하 생성 완료',
                '부하타입': '지속부하',
                '설정': {
                    '초당비율': 초당비율,
                    '지속시간': 지속시간,
                    '메시지타입': 메시지타입 or '랜덤'
                },
                '결과': 결과분석
            }
            
        except Exception as e:
            error_msg = f"지속 부하 생성 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
        finally:
            self._실행상태설정(False)
    
    async def 점진적부하생성(self, 시작비율: int, 최대비율: int, 증가시간: int = 300, 메시지타입: Optional[str] = None) -> Dict[str, Any]:
        """
        점진적으로 증가하는 부하 생성
        
        Args:
            시작비율: 시작 시 초당 메시지 수
            최대비율: 최대 초당 메시지 수
            증가시간: 최대 비율까지 증가하는 시간 (초)
            메시지타입: 특정 메시지 타입 (None이면 랜덤)
            
        Returns:
            dict: 부하 생성 결과
        """
        if self.실행상태['실행중']:
            return {
                '성공': False,
                '메시지': '이미 부하 생성이 실행 중입니다'
            }
        
        try:
            self._실행상태설정(True, f'점진적부하생성({시작비율}->{최대비율})')
            
            self.로거.info(f"점진적 부하 생성 시작: {시작비율}/초에서 {최대비율}/초로 {증가시간}초에 걸쳐 증가")
            
            시작시간 = time.time()
            전체결과들 = []
            
            # 매초마다 비율 계산 및 전송
            for 초 in range(증가시간):
                if self.실행상태['중지신호'].is_set():
                    self.로거.info("점진적 부하 생성 중지 신호 수신")
                    break
                
                # 현재 초의 전송 비율 계산 (선형 증가)
                진행비율 = 초 / 증가시간
                현재비율 = int(시작비율 + (최대비율 - 시작비율) * 진행비율)
                
                # 메시지 생성 및 전송
                메시지목록 = self._메시지목록생성(현재비율, 메시지타입)
                
                배치시작시간 = time.time()
                결과들 = await self._병렬메시지전송(메시지목록, 1)
                전체결과들.extend(결과들)
                
                # 정확한 1초 간격 유지
                경과시간 = time.time() - 배치시작시간
                if 경과시간 < 1.0:
                    await asyncio.sleep(1.0 - 경과시간)
                
                # 진행 상황 로깅 (30초마다)
                if (초 + 1) % 30 == 0:
                    self.로거.info(f"점진적 부하 진행: {초 + 1}/{증가시간}초, 현재 비율: {현재비율}/초")
            
            종료시간 = time.time()
            
            # 결과 분석
            결과분석 = self._결과분석(전체결과들, 시작시간, 종료시간)
            
            self.로거.info(f"점진적 부하 생성 완료: {결과분석['성공률']:.1f}% 성공")
            
            return {
                '성공': True,
                '메시지': '점진적 부하 생성 완료',
                '부하타입': '점진적부하',
                '설정': {
                    '시작비율': 시작비율,
                    '최대비율': 최대비율,
                    '증가시간': 증가시간,
                    '메시지타입': 메시지타입 or '랜덤'
                },
                '결과': 결과분석
            }
            
        except Exception as e:
            error_msg = f"점진적 부하 생성 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
        finally:
            self._실행상태설정(False)
    
    def 부하중지(self) -> Dict[str, Any]:
        """
        현재 진행 중인 부하 생성 중지
        
        Returns:
            dict: 중지 결과
        """
        if not self.실행상태['실행중']:
            return {
                '성공': False,
                '메시지': '실행 중인 부하 생성이 없습니다'
            }
        
        try:
            self.실행상태['중지신호'].set()
            self.로거.info("부하 생성 중지 신호 전송")
            
            return {
                '성공': True,
                '메시지': '부하 생성 중지 신호가 전송되었습니다',
                '현재작업': self.실행상태['현재작업']
            }
            
        except Exception as e:
            error_msg = f"부하 중지 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
    
    def _메시지목록생성(self, 개수: int, 메시지타입: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        전송할 메시지 목록 생성
        
        Args:
            개수: 생성할 메시지 개수
            메시지타입: 특정 메시지 타입 (None이면 랜덤)
            
        Returns:
            list: 메시지 목록
        """
        메시지목록 = []
        
        for i in range(개수):
            # 메시지 타입 결정
            if 메시지타입:
                타입 = 메시지타입.upper()
            else:
                타입 = random.choice([t.value for t in MessageType])
            
            # 메시지 내용 생성
            내용 = self._메시지내용생성(타입)
            
            메시지 = {
                '타입': 타입,
                '내용': 내용,
                '속성들': {
                    '실험용': True,
                    '생성시간': datetime.now().isoformat(),
                    '부하생성기': '부하생성기'
                }
            }
            
            메시지목록.append(메시지)
        
        return 메시지목록
    
    def _메시지내용생성(self, 타입: str) -> str:
        """
        메시지 타입별 내용 생성
        
        Args:
            타입: 메시지 타입
            
        Returns:
            str: 생성된 메시지 내용
        """
        if 타입 == MessageType.SUBSCRIPTION.value:
            return f"신규 가입 요청 - 고객번호: CUST{random.randint(100000, 999999)}"
        elif 타입 == MessageType.MNP.value:
            return f"번호이동 요청 - 이동번호: 010{random.randint(10000000, 99999999)}"
        elif 타입 == MessageType.CHANGE.value:
            return f"명의변경 요청 - 계약번호: CONTRACT{random.randint(100000, 999999)}"
        elif 타입 == MessageType.TERMINATION.value:
            return f"해지 요청 - 서비스번호: 010{random.randint(10000000, 99999999)}"
        else:
            return f"일반 메시지 - ID: {random.randint(1000, 9999)}"
    
    async def _병렬메시지전송(self, 메시지목록: List[Dict[str, Any]], 제한시간: int) -> List[Dict[str, Any]]:
        """
        메시지를 병렬로 전송
        
        Args:
            메시지목록: 전송할 메시지 목록
            제한시간: 전송 제한 시간 (초)
            
        Returns:
            list: 전송 결과 목록
        """
        결과들 = []
        
        # HTTP 세션 생성
        timeout = aiohttp.ClientTimeout(total=제한시간 + 5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 병렬 전송 태스크 생성
            태스크들 = []
            for 메시지 in 메시지목록:
                태스크 = self._단일메시지전송(session, 메시지)
                태스크들.append(태스크)
            
            # 모든 태스크 실행
            try:
                결과들 = await asyncio.wait_for(
                    asyncio.gather(*태스크들, return_exceptions=True),
                    timeout=제한시간
                )
            except asyncio.TimeoutError:
                self.로거.warning(f"메시지 전송 타임아웃 ({제한시간}초)")
                결과들 = [{'성공': False, '오류': 'timeout'} for _ in 메시지목록]
        
        return 결과들
    
    async def _단일메시지전송(self, session: aiohttp.ClientSession, 메시지: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 메시지 전송
        
        Args:
            session: HTTP 세션
            메시지: 전송할 메시지
            
        Returns:
            dict: 전송 결과
        """
        시작시간 = time.time()
        
        try:
            url = f"{self.게이트웨이주소}/api/message"
            
            async with session.post(url, json=메시지) as response:
                응답시간 = time.time() - 시작시간
                
                if response.status == 200:
                    응답데이터 = await response.json()
                    return {
                        '성공': True,
                        '응답시간': 응답시간,
                        '메시지타입': 메시지['타입'],
                        '응답데이터': 응답데이터
                    }
                else:
                    응답텍스트 = await response.text()
                    return {
                        '성공': False,
                        '응답시간': 응답시간,
                        '메시지타입': 메시지['타입'],
                        '오류': f"HTTP {response.status}: {응답텍스트}"
                    }
                    
        except Exception as e:
            응답시간 = time.time() - 시작시간
            return {
                '성공': False,
                '응답시간': 응답시간,
                '메시지타입': 메시지['타입'],
                '오류': str(e)
            }
    
    def _결과분석(self, 결과들: List[Dict[str, Any]], 시작시간: float, 종료시간: float) -> Dict[str, Any]:
        """
        전송 결과 분석
        
        Args:
            결과들: 전송 결과 목록
            시작시간: 시작 시간
            종료시간: 종료 시간
            
        Returns:
            dict: 분석 결과
        """
        총개수 = len(결과들)
        성공개수 = sum(1 for r in 결과들 if isinstance(r, dict) and r.get('성공', False))
        실패개수 = 총개수 - 성공개수
        
        # 응답 시간 분석
        성공결과들 = [r for r in 결과들 if isinstance(r, dict) and r.get('성공', False)]
        if 성공결과들:
            응답시간들 = [r['응답시간'] for r in 성공결과들]
            평균응답시간 = sum(응답시간들) / len(응답시간들)
            최대응답시간 = max(응답시간들)
            최소응답시간 = min(응답시간들)
        else:
            평균응답시간 = 최대응답시간 = 최소응답시간 = 0.0
        
        # 타입별 통계
        타입별통계 = {}
        for 결과 in 결과들:
            if isinstance(결과, dict) and '메시지타입' in 결과:
                타입 = 결과['메시지타입']
                if 타입 not in 타입별통계:
                    타입별통계[타입] = {'성공': 0, '실패': 0}
                
                if 결과.get('성공', False):
                    타입별통계[타입]['성공'] += 1
                else:
                    타입별통계[타입]['실패'] += 1
        
        # 처리량 계산
        총시간 = 종료시간 - 시작시간
        처리량 = 성공개수 / 총시간 if 총시간 > 0 else 0
        
        # 통계 업데이트
        self.부하통계['총요청수'] += 총개수
        self.부하통계['성공요청수'] += 성공개수
        self.부하통계['실패요청수'] += 실패개수
        self.부하통계['평균응답시간'] = 평균응답시간
        
        for 타입, 통계 in 타입별통계.items():
            self.부하통계['타입별통계'][타입] += 통계['성공']
        
        return {
            '총요청수': 총개수,
            '성공요청수': 성공개수,
            '실패요청수': 실패개수,
            '성공률': round(성공개수 / 총개수 * 100, 2) if 총개수 > 0 else 0,
            '처리량': round(처리량, 2),
            '응답시간': {
                '평균': round(평균응답시간, 3),
                '최대': round(최대응답시간, 3),
                '최소': round(최소응답시간, 3)
            },
            '타입별통계': 타입별통계,
            '실행시간': round(총시간, 2)
        }
    
    def _실행상태설정(self, 실행중: bool, 작업명: Optional[str] = None):
        """실행 상태 설정"""
        self.실행상태['실행중'] = 실행중
        self.실행상태['현재작업'] = 작업명
        
        if 실행중:
            self.실행상태['시작시간'] = time.time()
            self.실행상태['중지신호'].clear()
        else:
            self.실행상태['시작시간'] = None
            self.실행상태['중지신호'].set()
    
    def 상태조회(self) -> Dict[str, Any]:
        """
        부하 생성기 상태 조회
        
        Returns:
            dict: 상태 정보
        """
        return {
            '실행상태': self.실행상태.copy(),
            '게이트웨이주소': self.게이트웨이주소,
            '부하통계': self.부하통계.copy(),
            '현재시간': datetime.now().isoformat()
        }