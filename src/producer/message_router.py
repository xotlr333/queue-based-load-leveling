# 파일 경로: src/producer/message_router.py
# 메시지 라우터 클래스

from typing import Dict, Any
from src.common.message_models import BSS메시지, MessageType
from src.producer.message_producer import BSS메시지생산자
from src.common.config import 설정가져오기


class 메시지라우터:
    """
    BSS 메시지 라우팅 및 전송을 담당하는 클래스
    단일 큐 구조에서 메시지 타입 검증 및 전송 처리
    
    속성:
        생산자: BSS메시지생산자 인스턴스
        설정: 설정 관리자 인스턴스
    """
    
    def __init__(self):
        """메시지 라우터 초기화"""
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('메시지라우터')
        self.생산자 = BSS메시지생산자()
        
        # 유효한 메시지 타입 목록
        self.유효한타입들 = [t.value for t in MessageType]
        
        self.로거.info("메시지 라우터 초기화 완료")
    
    def 메시지전송(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        메시지를 큐로 전송하고 결과 반환
        
        Args:
            메시지: 전송할 BSS 메시지
            
        Returns:
            dict: 전송 결과 {'성공': bool, '메시지': str, '세부정보': dict}
        """
        try:
            # 메시지 타입 설정 및 검증
            검증된메시지 = self.메시지타입설정(메시지)
            
            if not 검증된메시지:
                return {
                    '성공': False,
                    '메시지': '메시지 타입 검증 실패',
                    '세부정보': {
                        '원본타입': 메시지.타입,
                        '유효한타입들': self.유효한타입들
                    }
                }
            
            # 메시지 전송
            전송결과 = self.생산자.큐전송(검증된메시지)
            
            # 라우팅 로그 기록
            self._라우팅로그기록(검증된메시지, 전송결과['성공'])
            
            return {
                '성공': 전송결과['성공'],
                '메시지': 전송결과['메시지'],
                '세부정보': {
                    '메시지아이디': 전송결과['메시지아이디'],
                    '메시지타입': 검증된메시지.타입,
                    '큐이름': self.설정.큐설정가져오기()['큐이름'],
                    '전송시간': 검증된메시지.생성시간.isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"메시지 라우팅 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg,
                '세부정보': {
                    '메시지아이디': 메시지.아이디,
                    '오류타입': type(e).__name__
                }
            }
    
    def 메시지타입설정(self, 메시지: BSS메시지) -> BSS메시지:
        """
        메시지 타입 검증 및 설정
        
        Args:
            메시지: 검증할 BSS 메시지
            
        Returns:
            BSS메시지: 검증된 메시지 (실패 시 None)
        """
        try:
            # 메시지 기본 검증
            if not 메시지.메시지검증():
                self.로거.warning(f"메시지 기본 검증 실패: {메시지.아이디}")
                return None
            
            # 메시지 타입 정규화 (대문자 변환)
            정규화된타입 = 메시지.타입.upper().strip()
            
            # 유효한 타입인지 확인
            if 정규화된타입 not in self.유효한타입들:
                self.로거.warning(f"유효하지 않은 메시지 타입: {정규화된타입}")
                return None
            
            # 타입이 변경된 경우 업데이트
            if 메시지.타입 != 정규화된타입:
                메시지.타입 = 정규화된타입
                self.로거.debug(f"메시지 타입 정규화: {메시지.아이디} -> {정규화된타입}")
            
            # 메시지에 라우팅 정보 추가
            메시지.속성들['라우팅정보'] = {
                '라우터': '메시지라우터',
                '대상큐': self.설정.큐설정가져오기()['큐이름'],
                '라우팅시간': 메시지.생성시간.isoformat()
            }
            
            return 메시지
            
        except Exception as e:
            self.로거.error(f"메시지 타입 설정 실패: {e}")
            return None
    
    def 배치메시지전송(self, 메시지목록: list[BSS메시지]) -> Dict[str, Any]:
        """
        여러 메시지를 배치로 라우팅 및 전송
        
        Args:
            메시지목록: 전송할 BSS 메시지 리스트
            
        Returns:
            dict: 배치 전송 결과
        """
        if not 메시지목록:
            return {
                '성공': False,
                '메시지': '전송할 메시지가 없습니다',
                '세부정보': {'전체개수': 0}
            }
        
        검증된메시지들 = []
        검증실패개수 = 0
        
        # 메시지 검증 단계
        for 메시지 in 메시지목록:
            검증된메시지 = self.메시지타입설정(메시지)
            if 검증된메시지:
                검증된메시지들.append(검증된메시지)
            else:
                검증실패개수 += 1
        
        # 검증된 메시지들 배치 전송
        if 검증된메시지들:
            전송결과 = self.생산자.배치전송(검증된메시지들)
        else:
            전송결과 = {
                '전체개수': 0,
                '성공개수': 0,
                '실패개수': 0,
                '성공률': 0
            }
        
        # 통계 정보 포함한 결과 반환
        return {
            '성공': 전송결과['성공개수'] > 0,
            '메시지': f"배치 전송 완료: {전송결과['성공개수']}/{len(메시지목록)} 성공",
            '세부정보': {
                '원본메시지개수': len(메시지목록),
                '검증성공개수': len(검증된메시지들),
                '검증실패개수': 검증실패개수,
                '전송성공개수': 전송결과['성공개수'],
                '전송실패개수': 전송결과['실패개수'],
                '최종성공률': 전송결과['성공률']
            }
        }
    
    def 큐상태조회(self) -> Dict[str, Any]:
        """
        큐 상태 정보 조회
        
        Returns:
            dict: 큐 상태 정보
        """
        try:
            큐상태 = self.생산자.큐상태확인()
            
            if '오류' in 큐상태:
                return {
                    '성공': False,
                    '메시지': f"큐 상태 조회 실패: {큐상태['오류']}"
                }
            
            return {
                '성공': True,
                '메시지': '큐 상태 조회 성공',
                '세부정보': 큐상태
            }
            
        except Exception as e:
            error_msg = f"큐 상태 조회 중 오류: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
    
    def 연결상태확인(self) -> Dict[str, Any]:
        """
        RabbitMQ 연결 상태 확인
        
        Returns:
            dict: 연결 상태 정보
        """
        try:
            연결상태 = self.생산자.연결확인()
            
            return {
                '성공': True,
                '메시지': '연결 상태 확인 완료',
                '세부정보': {
                    '연결상태': '정상' if 연결상태 else '비정상',
                    '연결가능': 연결상태,
                    '큐설정': self.설정.큐설정가져오기()
                }
            }
            
        except Exception as e:
            error_msg = f"연결 상태 확인 실패: {e}"
            self.로거.error(error_msg)
            return {
                '성공': False,
                '메시지': error_msg
            }
    
    def _라우팅로그기록(self, 메시지: BSS메시지, 전송성공: bool):
        """
        라우팅 로그 기록
        
        Args:
            메시지: 라우팅된 메시지
            전송성공: 전송 성공 여부
        """
        상태 = "성공" if 전송성공 else "실패"
        self.로거.info(
            f"메시지 라우팅 {상태}: "
            f"타입={메시지.타입}, "
            f"아이디={메시지.아이디}, "
            f"큐={self.설정.큐설정가져오기()['큐이름']}"
        )
        
        # 모니터링이 활성화된 경우 추가 로그
        if self.설정.모니터링상태확인():
            self.로거.debug(f"라우팅 세부정보: {메시지.속성들.get('라우팅정보', {})}")
    
    def 라우터통계(self) -> Dict[str, Any]:
        """
        라우터 동작 통계 정보 반환
        
        Returns:
            dict: 라우터 통계 정보
        """
        try:
            큐상태 = self.생산자.큐상태확인()
            
            return {
                '라우터정보': {
                    '유효한메시지타입': self.유효한타입들,
                    '대상큐': self.설정.큐설정가져오기()['큐이름'],
                    '모니터링상태': self.설정.모니터링상태확인()
                },
                '큐상태': 큐상태,
                '설정정보': {
                    '연결문자열': self.설정.연결문자열가져오기(),
                    '큐설정': self.설정.큐설정가져오기()
                }
            }
            
        except Exception as e:
            self.로거.error(f"라우터 통계 조회 실패: {e}")
            return {
                '오류': str(e)
            }