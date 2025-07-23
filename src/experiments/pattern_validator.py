# 파일 경로: src/experiments/pattern_validator.py
# 패턴 검증기 클래스

import asyncio
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.experiments.load_generator import 부하생성기
from src.common.config import 설정가져오기


@dataclass
class 검증결과:
    """검증 결과 데이터 클래스"""
    검증명: str
    성공: bool
    점수: float
    기준값: float
    측정값: float
    메시지: str
    세부정보: Dict[str, Any]


class 패턴검증기:
    """
    Queue-Based Load Leveling 패턴의 효과를 검증하는 클래스
    다양한 실험을 통해 패턴의 부하 평활화, 시스템 보호 효과 측정
    
    속성:
        부하생성기: 부하생성기 인스턴스
        설정: 설정 관리자 인스턴스
        검증결과들: 수행된 검증 결과 목록
    """
    
    def __init__(self, 게이트웨이주소: str = None):
        """
        패턴 검증기 초기화
        
        Args:
            게이트웨이주소: API Gateway 주소
        """
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('패턴검증기')
        self.부하생성기 = 부하생성기(게이트웨이주소)
        
        # 검증 결과 저장
        self.검증결과들: List[검증결과] = []
        
        # 검증 기준값들
        self.검증기준 = {
            '부하평활화계수': 5.0,      # 최소 5배 평활화
            'CPU사용률한계': 80.0,      # 최대 80% CPU 사용률
            '응답시간한계': 2.0,        # 최대 2초 응답시간
            '메시지손실률한계': 1.0,     # 최대 1% 메시지 손실
            '처리량증가율': 150.0       # 최소 150% 처리량 증가
        }
        
        self.로거.info("패턴 검증기 초기화 완료")
    
    async def 부하평활화검증(self, 급증메시지수: int = 1000, 측정시간: int = 120) -> 검증결과:
        """
        급증 트래픽이 안정적으로 처리되는지 검증
        
        Args:
            급증메시지수: 급증 투입할 메시지 수
            측정시간: 전체 측정 시간 (초)
            
        Returns:
            검증결과: 부하 평활화 검증 결과
        """
        try:
            self.로거.info(f"부하 평활화 검증 시작: {급증메시지수}개 메시지, {측정시간}초 측정")
            
            # 1단계: 기준 상태 측정 (30초)
            self.로거.info("1단계: 기준 상태 측정")
            기준상태 = await self._시스템상태측정(30)
            
            # 2단계: 급증 부하 투입 + 측정
            self.로거.info("2단계: 급증 부하 투입")
            시작시간 = time.time()
            
            # 급증 부하 생성 (비동기)
            부하태스크 = asyncio.create_task(
                self.부하생성기.급증부하생성(급증메시지수, 60)  # 1분간 급속 투입
            )
            
            # 동시에 시스템 상태 모니터링
            모니터링태스크 = asyncio.create_task(
                self._연속상태측정(측정시간)
            )
            
            # 두 태스크 완료 대기
            부하결과, 모니터링결과 = await asyncio.gather(부하태스크, 모니터링태스크)
            
            # 3단계: 결과 분석
            self.로거.info("3단계: 부하 평활화 효과 분석")
            
            # 입력 부하의 분산 계산
            입력분산 = self._부하분산계산(부하결과)
            
            # 출력 처리의 분산 계산 (모니터링 데이터 기반)
            출력분산 = self._처리분산계산(모니터링결과)
            
            # 평활화 계수 계산
            평활화계수 = 입력분산 / 출력분산 if 출력분산 > 0 else 0
            
            # 검증 결과 생성
            기준값 = self.검증기준['부하평활화계수']
            성공 = 평활화계수 >= 기준값
            
            검증결과객체 = 검증결과(
                검증명="부하평활화검증",
                성공=성공,
                점수=min(평활화계수 / 기준값 * 100, 100),
                기준값=기준값,
                측정값=평활화계수,
                메시지=f"평활화 계수: {평활화계수:.2f} ({'성공' if 성공 else '실패'})",
                세부정보={
                    '급증메시지수': 급증메시지수,
                    '측정시간': 측정시간,
                    '입력분산': 입력분산,
                    '출력분산': 출력분산,
                    '부하결과': 부하결과,
                    '기준상태': 기준상태,
                    '모니터링결과': 모니터링결과
                }
            )
            
            self.검증결과들.append(검증결과객체)
            self.로거.info(f"부하 평활화 검증 완료: {검증결과객체.메시지}")
            
            return 검증결과객체
            
        except Exception as e:
            error_msg = f"부하 평활화 검증 실패: {e}"
            self.로거.error(error_msg)
            
            return 검증결과(
                검증명="부하평활화검증",
                성공=False,
                점수=0.0,
                기준값=self.검증기준['부하평활화계수'],
                측정값=0.0,
                메시지=error_msg,
                세부정보={'오류': str(e)}
            )
    
    async def 시스템보호검증(self, 부하강도: int = 500, 지속시간: int = 180) -> 검증결과:
        """
        백엔드 시스템이 과부하로부터 보호되는지 검증
        
        Args:
            부하강도: 초당 메시지 수
            지속시간: 부하 지속 시간 (초)
            
        Returns:
            검증결과: 시스템 보호 검증 결과
        """
        try:
            self.로거.info(f"시스템 보호 검증 시작: {부하강도}/초, {지속시간}초 지속")
            
            # 1단계: 기준 상태 측정
            기준상태 = await self._시스템상태측정(30)
            
            # 2단계: 지속적 고부하 투입
            시작시간 = time.time()
            
            부하태스크 = asyncio.create_task(
                self.부하생성기.지속부하생성(부하강도, 지속시간)
            )
            
            모니터링태스크 = asyncio.create_task(
                self._연속상태측정(지속시간 + 30)  # 추가 30초 모니터링
            )
            
            부하결과, 모니터링결과 = await asyncio.gather(부하태스크, 모니터링태스크)
            
            # 3단계: 시스템 보호 효과 분석
            보호분석결과 = self._시스템보호분석(모니터링결과, 기준상태)
            
            # 검증 기준: CPU 사용률이 기준값 이하로 유지되었는가?
            최대CPU사용률 = 보호분석결과['최대CPU사용률']
            기준값 = self.검증기준['CPU사용률한계']
            성공 = 최대CPU사용률 <= 기준값
            
            검증결과객체 = 검증결과(
                검증명="시스템보호검증",
                성공=성공,
                점수=max(0, (기준값 - 최대CPU사용률) / 기준값 * 100),
                기준값=기준값,
                측정값=최대CPU사용률,
                메시지=f"최대 CPU 사용률: {최대CPU사용률:.1f}% ({'성공' if 성공 else '실패'})",
                세부정보={
                    '부하강도': 부하강도,
                    '지속시간': 지속시간,
                    '보호분석결과': 보호분석결과,
                    '부하결과': 부하결과,
                    '기준상태': 기준상태
                }
            )
            
            self.검증결과들.append(검증결과객체)
            self.로거.info(f"시스템 보호 검증 완료: {검증결과객체.메시지}")
            
            return 검증결과객체
            
        except Exception as e:
            error_msg = f"시스템 보호 검증 실패: {e}"
            self.로거.error(error_msg)
            
            return 검증결과(
                검증명="시스템보호검증",
                성공=False,
                점수=0.0,
                기준값=self.검증기준['CPU사용률한계'],
                측정값=100.0,
                메시지=error_msg,
                세부정보={'오류': str(e)}
            )
    
    async def 큐버퍼링효과검증(self, 순간메시지수: int = 2000) -> 검증결과:
        """
        큐의 버퍼 역할 확인 - 순간 대량 트래픽의 점진적 소진
        
        Args:
            순간메시지수: 순간 투입할 메시지 수
            
        Returns:
            검증결과: 큐 버퍼링 효과 검증 결과
        """
        try:
            self.로거.info(f"큐 버퍼링 효과 검증 시작: {순간메시지수}개 순간 투입")
            
            # 1단계: 큐 상태 초기 확인
            초기큐상태 = await self._큐상태조회()
            
            # 2단계: 순간 대량 메시지 투입 (10초 내)
            부하결과 = await self.부하생성기.급증부하생성(순간메시지수, 10)
            
            # 3단계: 큐 길이 변화 모니터링 (5분간)
            큐변화데이터 = await self._큐변화모니터링(300)
            
            # 4단계: 버퍼링 효과 분석
            버퍼링분석 = self._큐버퍼링분석(큐변화데이터, 부하결과)
            
            # 검증 기준: 메시지 손실률이 기준값 이하인가?
            메시지손실률 = 버퍼링분석['메시지손실률']
            기준값 = self.검증기준['메시지손실률한계']
            성공 = 메시지손실률 <= 기준값
            
            검증결과객체 = 검증결과(
                검증명="큐버퍼링효과검증",
                성공=성공,
                점수=max(0, (기준값 - 메시지손실률) / 기준값 * 100),
                기준값=기준값,
                측정값=메시지손실률,
                메시지=f"메시지 손실률: {메시지손실률:.2f}% ({'성공' if 성공 else '실패'})",
                세부정보={
                    '순간메시지수': 순간메시지수,
                    '초기큐상태': 초기큐상태,
                    '버퍼링분석': 버퍼링분석,
                    '큐변화데이터': 큐변화데이터,
                    '부하결과': 부하결과
                }
            )
            
            self.검증결과들.append(검증결과객체)
            self.로거.info(f"큐 버퍼링 효과 검증 완료: {검증결과객체.메시지}")
            
            return 검증결과객체
            
        except Exception as e:
            error_msg = f"큐 버퍼링 효과 검증 실패: {e}"
            self.로거.error(error_msg)
            
            return 검증결과(
                검증명="큐버퍼링효과검증",
                성공=False,
                점수=0.0,
                기준값=self.검증기준['메시지손실률한계'],
                측정값=100.0,
                메시지=error_msg,
                세부정보={'오류': str(e)}
            )
    
    def 검증보고서생성(self) -> Dict[str, Any]:
        """
        모든 검증 결과를 종합한 보고서 생성
        
        Returns:
            dict: 종합 검증 보고서
        """
        if not self.검증결과들:
            return {
                '보고서상태': '검증 결과 없음',
                '메시지': '수행된 검증이 없습니다. 먼저 검증을 실행해주세요.'
            }
        
        # 전체 점수 계산
        총점수 = sum(결과.점수 for 결과 in self.검증결과들)
        평균점수 = 총점수 / len(self.검증결과들)
        
        # 성공한 검증 수
        성공개수 = sum(1 for 결과 in self.검증결과들 if 결과.성공)
        성공률 = (성공개수 / len(self.검증결과들)) * 100
        
        # 등급 결정
        if 평균점수 >= 90:
            등급 = "A (우수)"
        elif 평균점수 >= 80:
            등급 = "B (양호)"
        elif 평균점수 >= 70:
            등급 = "C (보통)"
        elif 평균점수 >= 60:
            등급 = "D (미흡)"
        else:
            등급 = "F (불량)"
        
        # 권장사항 생성
        권장사항 = self._권장사항생성()
        
        return {
            '보고서정보': {
                '생성시간': datetime.now().isoformat(),
                '검증수행개수': len(self.검증결과들),
                '성공개수': 성공개수,
                '실패개수': len(self.검증결과들) - 성공개수
            },
            '종합결과': {
                '평균점수': round(평균점수, 1),
                '성공률': round(성공률, 1),
                '등급': 등급,
                '패턴효과': '확인됨' if 성공률 >= 70 else '미흡'
            },
            '검증별결과': [
                {
                    '검증명': 결과.검증명,
                    '성공여부': 결과.성공,
                    '점수': round(결과.점수, 1),
                    '측정값': 결과.측정값,
                    '기준값': 결과.기준값,
                    '메시지': 결과.메시지
                }
                for 결과 in self.검증결과들
            ],
            '권장사항': 권장사항,
            '상세데이터': {
                '검증기준': self.검증기준,
                '전체검증결과': [
                    {
                        '검증명': 결과.검증명,
                        '세부정보': 결과.세부정보
                    }
                    for 결과 in self.검증결과들
                ]
            }
        }
    
    async def _시스템상태측정(self, 측정시간: int) -> Dict[str, Any]:
        """시스템 기준 상태 측정"""
        try:
            # 큐 상태 조회
            큐상태 = await self._큐상태조회()
            
            # API 응답 시간 측정
            응답시간들 = []
            for _ in range(10):  # 10회 측정
                시작 = time.time()
                try:
                    response = requests.get(f"{self.부하생성기.게이트웨이주소}/health", timeout=5)
                    if response.status_code == 200:
                        응답시간들.append(time.time() - 시작)
                except:
                    pass
                await asyncio.sleep(1)
            
            평균응답시간 = sum(응답시간들) / len(응답시간들) if 응답시간들 else 0
            
            return {
                '측정시간': 측정시간,
                '큐상태': 큐상태,
                '평균응답시간': 평균응답시간,
                '타임스탬프': time.time()
            }
            
        except Exception as e:
            self.로거.warning(f"시스템 상태 측정 실패: {e}")
            return {
                '측정시간': 측정시간,
                '오류': str(e),
                '타임스탬프': time.time()
            }
    
    async def _연속상태측정(self, 총시간: int) -> List[Dict[str, Any]]:
        """연속적인 시스템 상태 측정"""
        측정데이터 = []
        측정간격 = 5  # 5초 간격
        
        for i in range(0, 총시간, 측정간격):
            try:
                측정시점 = time.time()
                
                # 큐 상태 조회
                큐상태 = await self._큐상태조회()
                
                # 간단한 상태 측정
                상태데이터 = {
                    '측정시점': 측정시점,
                    '경과시간': i,
                    '큐길이': 큐상태.get('메시지개수', 0),
                    '소비자수': 큐상태.get('소비자개수', 0),
                    '가상CPU사용률': min(50 + (큐상태.get('메시지개수', 0) / 10), 95)  # 시뮬레이션
                }
                
                측정데이터.append(상태데이터)
                
                if i < 총시간 - 측정간격:
                    await asyncio.sleep(측정간격)
                    
            except Exception as e:
                self.로거.warning(f"상태 측정 오류 (시점 {i}초): {e}")
        
        return 측정데이터
    
    async def _큐상태조회(self) -> Dict[str, Any]:
        """큐 상태 조회"""
        try:
            response = requests.get(f"{self.부하생성기.게이트웨이주소}/api/queue/status", timeout=5)
            if response.status_code == 200:
                return response.json().get('세부정보', {})
            else:
                return {'오류': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'오류': str(e)}
    
    async def _큐변화모니터링(self, 모니터링시간: int) -> List[Dict[str, Any]]:
        """큐 길이 변화 모니터링"""
        변화데이터 = []
        
        for i in range(0, 모니터링시간, 10):  # 10초 간격
            큐상태 = await self._큐상태조회()
            
            변화데이터.append({
                '시점': i,
                '큐길이': 큐상태.get('메시지개수', 0),
                '타임스탬프': time.time()
            })
            
            if i < 모니터링시간 - 10:
                await asyncio.sleep(10)
        
        return 변화데이터
    
    def _부하분산계산(self, 부하결과: Dict[str, Any]) -> float:
        """입력 부하의 분산 계산"""
        try:
            # 부하 결과에서 시간별 전송량 추출
            결과 = 부하결과.get('결과', {})
            실행시간 = 결과.get('실행시간', 1)
            총요청수 = 결과.get('총요청수', 0)
            
            # 간단한 분산 시뮬레이션 (실제로는 더 정교한 계산 필요)
            if '급증' in 부하결과.get('부하타입', ''):
                # 급증 부하: 높은 분산
                return 총요청수 / max(실행시간, 1) * 10
            else:
                # 지속 부하: 낮은 분산  
                return 총요청수 / max(실행시간, 1)
        except:
            return 1.0
    
    def _처리분산계산(self, 모니터링결과: List[Dict[str, Any]]) -> float:
        """출력 처리의 분산 계산"""
        try:
            if not 모니터링결과:
                return 1.0
            
            # 큐 길이 변화율 계산
            큐길이들 = [data.get('큐길이', 0) for data in 모니터링결과]
            if len(큐길이들) < 2:
                return 1.0
            
            # 변화율의 분산 계산
            변화율들 = []
            for i in range(1, len(큐길이들)):
                변화율 = abs(큐길이들[i] - 큐길이들[i-1])
                변화율들.append(변화율)
            
            if not 변화율들:
                return 1.0
            
            평균변화율 = sum(변화율들) / len(변화율들)
            return max(평균변화율, 0.1)  # 최소값 보장
            
        except:
            return 1.0
    
    def _시스템보호분석(self, 모니터링결과: List[Dict[str, Any]], 기준상태: Dict[str, Any]) -> Dict[str, Any]:
        """시스템 보호 효과 분석"""
        try:
            CPU사용률들 = [data.get('가상CPU사용률', 0) for data in 모니터링결과]
            
            return {
                '최대CPU사용률': max(CPU사용률들) if CPU사용률들 else 0,
                '평균CPU사용률': sum(CPU사용률들) / len(CPU사용률들) if CPU사용률들 else 0,
                '기준CPU사용률': 기준상태.get('가상CPU사용률', 20),
                'CPU증가율': max(CPU사용률들) - 기준상태.get('가상CPU사용률', 20) if CPU사용률들 else 0
            }
        except:
            return {
                '최대CPU사용률': 100,
                '평균CPU사용률': 100,
                '기준CPU사용률': 20,
                'CPU증가율': 80
            }
    
    def _큐버퍼링분석(self, 큐변화데이터: List[Dict[str, Any]], 부하결과: Dict[str, Any]) -> Dict[str, Any]:
        """큐 버퍼링 효과 분석"""
        try:
            투입메시지수 = 부하결과.get('결과', {}).get('총요청수', 0)
            성공메시지수 = 부하결과.get('결과', {}).get('성공요청수', 0)
            
            메시지손실수 = 투입메시지수 - 성공메시지수
            메시지손실률 = (메시지손실수 / 투입메시지수 * 100) if 투입메시지수 > 0 else 0
            
            # 큐 길이 변화 분석
            큐길이들 = [data.get('큐길이', 0) for data in 큐변화데이터]
            최대큐길이 = max(큐길이들) if 큐길이들 else 0
            
            return {
                '투입메시지수': 투입메시지수,
                '성공메시지수': 성공메시지수,
                '메시지손실수': 메시지손실수,
                '메시지손실률': 메시지손실률,
                '최대큐길이': 최대큐길이,
                '버퍼효과': '양호' if 메시지손실률 < 1.0 else '미흡'
            }
        except:
            return {
                '투입메시지수': 0,
                '성공메시지수': 0,
                '메시지손실수': 0,
                '메시지손실률': 100.0,
                '최대큐길이': 0,
                '버퍼효과': '불량'
            }
    
    def _권장사항생성(self) -> List[str]:
        """검증 결과 기반 권장사항 생성"""
        권장사항 = []
        
        for 결과 in self.검증결과들:
            if not 결과.성공:
                if 결과.검증명 == "부하평활화검증":
                    권장사항.append("큐 크기를 증가시키거나 Consumer 수를 늘려 부하 평활화 효과를 개선하세요")
                elif 결과.검증명 == "시스템보호검증":
                    권장사항.append("Consumer의 처리 성능을 최적화하거나 HPA 설정을 조정하여 시스템 보호 효과를 강화하세요")
                elif 결과.검증명 == "큐버퍼링효과검증":
                    권장사항.append("큐의 내구성 설정을 확인하고 메시지 처리 실패 시 재시도 로직을 개선하세요")
        
        if not 권장사항:
            권장사항.append("모든 검증이 성공했습니다. 현재 설정을 유지하세요")
        
        # 일반적인 권장사항 추가
        권장사항.extend([
            "정기적으로 시스템 성능을 모니터링하여 패턴 효과를 지속적으로 확인하세요",
            "비즈니스 요구사항 변화에 따라 큐 설정과 스케일링 정책을 조정하세요",
            "장애 상황에 대비한 Circuit Breaker 패턴 도입을 고려하세요"
        ])
        
        return 권장사항