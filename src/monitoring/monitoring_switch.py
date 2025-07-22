# 파일 경로: src/monitoring/monitoring_switch.py
# 모니터링 On/Off 스위치 클래스

import os
from typing import Dict, Any
from src.common.config import 설정가져오기


class 모니터링스위치:
    """
    모니터링 활성화/비활성화를 제어하는 스위치 클래스
    
    속성:
        현재상태 (bool): 현재 모니터링 활성화 상태
        설정: 설정 관리자 인스턴스
    """
    
    def __init__(self):
        """모니터링 스위치 초기화"""
        self.설정 = 설정가져오기()
        self.로거 = self.설정.로거설정('모니터링스위치')
        self.현재상태 = self.설정.모니터링상태확인()
        
        self.로거.info(f"모니터링 스위치 초기화: {'활성화' if self.현재상태 else '비활성화'}")
    
    def 모니터링활성화(self) -> Dict[str, Any]:
        """
        모니터링을 활성화하고 환경변수 업데이트
        
        Returns:
            dict: 활성화 결과
        """
        try:
            if self.현재상태:
                return {
                    '성공': True,
                    '메시지': '모니터링이 이미 활성화되어 있습니다',
                    '이전상태': True,
                    '현재상태': True
                }
            
            # 환경변수 업데이트
            os.environ['MONITORING_ENABLED'] = 'true'
            self.설정._load_config()  # 설정 재로드
            
            이전상태 = self.현재상태
            self.현재상태 = True
            
            self.로거.info("모니터링이 활성화되었습니다")
            
            return {
                '성공': True,
                '메시지': '모니터링이 활성화되었습니다',
                '이전상태': 이전상태,
                '현재상태': self.현재상태,
                '변경시간': self._현재시간()
            }
            
        except Exception as e:
            error_msg = f"모니터링 활성화 실패: {e}"
            self.로거.error(error_msg)
            
            return {
                '성공': False,
                '메시지': error_msg,
                '이전상태': self.현재상태,
                '현재상태': self.현재상태
            }
    
    def 모니터링비활성화(self) -> Dict[str, Any]:
        """
        모니터링을 비활성화하고 환경변수 업데이트
        
        Returns:
            dict: 비활성화 결과
        """
        try:
            if not self.현재상태:
                return {
                    '성공': True,
                    '메시지': '모니터링이 이미 비활성화되어 있습니다',
                    '이전상태': False,
                    '현재상태': False
                }
            
            # 환경변수 업데이트
            os.environ['MONITORING_ENABLED'] = 'false'
            self.설정._load_config()  # 설정 재로드
            
            이전상태 = self.현재상태
            self.현재상태 = False
            
            self.로거.info("모니터링이 비활성화되었습니다")
            
            return {
                '성공': True,
                '메시지': '모니터링이 비활성화되었습니다',
                '이전상태': 이전상태,
                '현재상태': self.현재상태,
                '변경시간': self._현재시간()
            }
            
        except Exception as e:
            error_msg = f"모니터링 비활성화 실패: {e}"
            self.로거.error(error_msg)
            
            return {
                '성공': False,
                '메시지': error_msg,
                '이전상태': self.현재상태,
                '현재상태': self.현재상태
            }
    
    def 상태확인(self) -> bool:
        """
        현재 모니터링 상태 반환
        
        Returns:
            bool: 모니터링이 활성화되어 있으면 True
        """
        # 설정에서 최신 상태 확인
        최신상태 = self.설정.모니터링상태확인()
        
        # 상태가 변경된 경우 동기화
        if self.현재상태 != 최신상태:
            self.로거.debug(f"모니터링 상태 동기화: {self.현재상태} -> {최신상태}")
            self.현재상태 = 최신상태
        
        return self.현재상태
    
    def 상태토글(self) -> Dict[str, Any]:
        """
        모니터링 상태를 토글 (활성화 ↔ 비활성화)
        
        Returns:
            dict: 토글 결과
        """
        현재상태 = self.상태확인()
        
        if 현재상태:
            return self.모니터링비활성화()
        else:
            return self.모니터링활성화()
    
    def 상태정보조회(self) -> Dict[str, Any]:
        """
        상세한 모니터링 상태 정보 조회
        
        Returns:
            dict: 상태 정보
        """
        return {
            '모니터링상태': {
                '활성화': self.상태확인(),
                '상태문자열': '활성화' if self.상태확인() else '비활성화',
                '환경변수값': os.getenv('MONITORING_ENABLED', 'false'),
                '설정값': self.설정.모니터링상태확인()
            },
            '시스템정보': {
                '현재시간': self._현재시간(),
                '설정파일': '환경변수 기반',
                '로그레벨': self.설정.로그레벨
            }
        }
    
    def _현재시간(self) -> str:
        """현재 시간을 ISO 형식으로 반환"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __str__(self) -> str:
        """문자열 표현"""
        상태 = '활성화' if self.상태확인() else '비활성화'
        return f"모니터링스위치(상태: {상태})"
    
    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"모니터링스위치(현재상태={self.현재상태})"


# 전역 모니터링 스위치 인스턴스 (싱글톤)
_모니터링스위치_인스턴스 = None


def 모니터링스위치가져오기() -> 모니터링스위치:
    """
    전역 모니터링 스위치 인스턴스 반환 (싱글톤)
    
    Returns:
        모니터링스위치: 모니터링 스위치 인스턴스
    """
    global _모니터링스위치_인스턴스
    if _모니터링스위치_인스턴스 is None:
        _모니터링스위치_인스턴스 = 모니터링스위치()
    return _모니터링스위치_인스턴스


def 모니터링스위치초기화():
    """모니터링 스위치 인스턴스 초기화 (테스트용)"""
    global _모니터링스위치_인스턴스
    _모니터링스위치_인스턴스 = None