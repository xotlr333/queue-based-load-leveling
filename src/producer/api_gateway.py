# 파일 경로: src/producer/api_gateway.py
# API 게이트웨이 클래스 (FastAPI 기반)

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from src.common.message_models import BSS메시지, MessageType
from src.producer.message_router import 메시지라우터
from src.common.config import 설정가져오기


# 요청 모델 정의
class 메시지요청(BaseModel):
    타입: str = Field(..., description="메시지 타입 (SUBSCRIPTION, MNP, CHANGE, TERMINATION)")
    내용: str = Field(..., description="메시지 내용")
    속성들: Optional[Dict[str, Any]] = Field(None, description="추가 메시지 속성")


class 배치메시지요청(BaseModel):
    메시지목록: List[메시지요청] = Field(..., description="전송할 메시지 목록")


# 응답 모델 정의
class 기본응답(BaseModel):
    성공: bool
    메시지: str
    타임스탬프: str
    세부정보: Optional[Dict[str, Any]] = None


class API게이트웨이:
    """
    BSS Queue-Based Load Leveling 패턴을 위한 API 게이트웨이
    HTTP 요청을 받아 메시지를 생성하고 라우터로 전송
    
    속성:
        라우터: 메시지라우터 인스턴스
        설정: 설정 관리자 인스턴스
        앱: FastAPI 애플리케이션 인스턴스
    """
    
    def __init__(self):
        """API 게이트웨이 초기화"""
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('API게이트웨이')
        self.라우터 = 메시지라우터()
        self.앱 = FastAPI(
            title="BSS Queue-Based Load Leveling API",
            description="BSS 메시지 처리를 위한 Queue-Based Load Leveling 패턴 API",
            version="1.0.0"
        )
        
        # 통계 정보
        self.요청통계 = {
            '총요청수': 0,
            '성공요청수': 0,
            '실패요청수': 0,
            '타입별통계': {타입.value: 0 for 타입 in MessageType}
        }
        
        self._라우트설정()
        self.로거.info("API 게이트웨이 초기화 완료")
    
    def _라우트설정(self):
        """FastAPI 라우트 설정"""
        
        @self.앱.get("/health")
        async def 헬스체크():
            """헬스 체크 엔드포인트"""
            return {"상태": "정상", "타임스탬프": datetime.now().isoformat()}
        
        @self.앱.get("/ready")
        async def 레디니스체크():
            """레디니스 체크 엔드포인트"""
            연결상태 = self.라우터.연결상태확인()
            if 연결상태['성공']:
                return {"상태": "준비완료", "타임스탬프": datetime.now().isoformat()}
            else:
                raise HTTPException(status_code=503, detail="서비스 준비되지 않음")
        
        @self.앱.post("/api/message", response_model=기본응답)
        async def 메시지전송(요청: 메시지요청):
            """단일 메시지 전송"""
            return await self._메시지처리(요청)
        
        @self.앱.post("/api/messages/batch", response_model=기본응답)
        async def 배치메시지전송(요청: 배치메시지요청):
            """배치 메시지 전송"""
            return await self._배치메시지처리(요청)
        
        @self.앱.get("/api/queue/status")
        async def 큐상태조회():
            """큐 상태 조회"""
            return self.라우터.큐상태조회()
        
        @self.앱.get("/api/stats")
        async def 통계조회():
            """API 통계 조회"""
            return await self._통계정보조회()
        
        @self.앱.get("/api/router/info")
        async def 라우터정보조회():
            """라우터 정보 조회"""
            return self.라우터.라우터통계()
        
        # 개발/디버깅용 엔드포인트
        @self.앱.get("/api/config")
        async def 설정정보조회():
            """설정 정보 조회 (개발용)"""
            return self.설정.설정정보출력()
        
        @self.앱.post("/api/monitoring/toggle")
        async def 모니터링토글():
            """모니터링 상태 토글"""
            새상태 = self.설정.모니터링토글()
            return {
                "성공": True,
                "메시지": f"모니터링 상태 변경: {'활성화' if 새상태 else '비활성화'}",
                "모니터링상태": 새상태
            }
    
    async def _메시지처리(self, 요청: 메시지요청) -> 기본응답:
        """
        단일 메시지 처리
        
        Args:
            요청: 메시지 요청 객체
            
        Returns:
            기본응답: 처리 결과
        """
        try:
            self.요청통계['총요청수'] += 1
            
            # HTTP 요청에서 BSS 메시지 생성
            메시지 = self.메시지생성(요청)
            
            # 메시지 라우터로 전송
            결과 = self.라우터.메시지전송(메시지)
            
            # 통계 업데이트
            if 결과['성공']:
                self.요청통계['성공요청수'] += 1
                self.요청통계['타입별통계'][메시지.타입] += 1
            else:
                self.요청통계['실패요청수'] += 1
            
            return 기본응답(
                성공=결과['성공'],
                메시지=결과['메시지'],
                타임스탬프=datetime.now().isoformat(),
                세부정보=결과.get('세부정보', {})
            )
            
        except Exception as e:
            self.요청통계['실패요청수'] += 1
            error_msg = f"메시지 처리 실패: {e}"
            self.로거.error(error_msg)
            
            return 기본응답(
                성공=False,
                메시지=error_msg,
                타임스탬프=datetime.now().isoformat(),
                세부정보={'오류타입': type(e).__name__}
            )
    
    async def _배치메시지처리(self, 요청: 배치메시지요청) -> 기본응답:
        """
        배치 메시지 처리
        
        Args:
            요청: 배치 메시지 요청 객체
            
        Returns:
            기본응답: 처리 결과
        """
        try:
            self.요청통계['총요청수'] += len(요청.메시지목록)
            
            # HTTP 요청에서 BSS 메시지 목록 생성
            메시지목록 = []
            for 메시지요청 in 요청.메시지목록:
                메시지 = self.메시지생성(메시지요청)
                메시지목록.append(메시지)
            
            # 배치 메시지 라우터로 전송
            결과 = self.라우터.배치메시지전송(메시지목록)
            
            # 통계 업데이트
            성공개수 = 결과.get('세부정보', {}).get('전송성공개수', 0)
            실패개수 = 결과.get('세부정보', {}).get('전송실패개수', 0)
            
            self.요청통계['성공요청수'] += 성공개수
            self.요청통계['실패요청수'] += 실패개수
            
            # 타입별 통계 업데이트
            for 메시지 in 메시지목록:
                if 메시지.타입 in self.요청통계['타입별통계']:
                    self.요청통계['타입별통계'][메시지.타입] += 1
            
            return 기본응답(
                성공=결과['성공'],
                메시지=결과['메시지'],
                타임스탬프=datetime.now().isoformat(),
                세부정보=결과.get('세부정보', {})
            )
            
        except Exception as e:
            self.요청통계['실패요청수'] += len(요청.메시지목록)
            error_msg = f"배치 메시지 처리 실패: {e}"
            self.로거.error(error_msg)
            
            return 기본응답(
                성공=False,
                메시지=error_msg,
                타임스탬프=datetime.now().isoformat(),
                세부정보={'오류타입': type(e).__name__}
            )
    
    def 메시지생성(self, 요청: 메시지요청) -> BSS메시지:
        """
        HTTP 요청에서 BSS메시지 객체 생성
        
        Args:
            요청: 메시지 요청 객체
            
        Returns:
            BSS메시지: 생성된 메시지 객체
            
        Raises:
            ValueError: 유효하지 않은 메시지 타입
        """
        # 메시지 타입 유효성 검증
        유효한타입들 = [t.value for t in MessageType]
        if 요청.타입.upper() not in 유효한타입들:
            raise ValueError(f"유효하지 않은 메시지 타입: {요청.타입}")
        
        # BSS 메시지 생성
        메시지 = BSS메시지(
            타입=요청.타입,
            내용=요청.내용,
            속성들=요청.속성들 or {}
        )
        
        # API 요청 정보 추가
        메시지.속성들['API정보'] = {
            '요청시간': datetime.now().isoformat(),
            '게이트웨이': 'API게이트웨이'
        }
        
        self.로거.debug(f"메시지 생성: {메시지.타입} - {메시지.아이디}")
        
        return 메시지
    
    async def _통계정보조회(self) -> Dict[str, Any]:
        """
        API 통계 정보 조회
        
        Returns:
            dict: 통계 정보
        """
        총요청수 = self.요청통계['총요청수']
        성공률 = round(self.요청통계['성공요청수'] / 총요청수 * 100, 2) if 총요청수 > 0 else 0
        
        return {
            '기본통계': {
                '총요청수': 총요청수,
                '성공요청수': self.요청통계['성공요청수'],
                '실패요청수': self.요청통계['실패요청수'],
                '성공률': f"{성공률}%"
            },
            '타입별통계': self.요청통계['타입별통계'],
            '시스템정보': {
                '시작시간': datetime.now().isoformat(),
                '모니터링상태': self.설정.모니터링상태확인(),
                '큐설정': self.설정.큐설정가져오기()
            }
        }
    
    def 서버시작(self, 호스트: str = "0.0.0.0", 포트: Optional[int] = None):
        """
        API 서버 시작
        
        Args:
            호스트: 바인딩할 호스트 주소
            포트: 바인딩할 포트 (None이면 설정에서 가져옴)
        """
        포트 = 포트 or self.설정.포트설정가져오기()['API']
        
        self.로거.info(f"API 서버 시작: {호스트}:{포트}")
        
        uvicorn.run(
            self.앱,
            host=호스트,
            port=포트,
            log_level=self.설정.로그레벨.lower()
        )