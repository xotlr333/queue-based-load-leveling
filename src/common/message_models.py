# 파일 경로: src/common/message_models.py
# BSS 메시지 모델 클래스 정의

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """메시지 타입 열거형"""
    SUBSCRIPTION = "SUBSCRIPTION"
    MNP = "MNP"
    CHANGE = "CHANGE"
    TERMINATION = "TERMINATION"


class BSS메시지:
    """
    Queue-Based Load Leveling 패턴을 위한 기본 BSS 메시지 클래스
    
    속성:
        아이디 (str): 고유 메시지 식별자
        타입 (str): 메시지 타입 (SUBSCRIPTION, MNP, CHANGE, TERMINATION)
        내용 (str): 메시지 본문 내용
        생성시간 (datetime): 메시지 생성 시간
        속성들 (dict): 추가 메시지 속성
    """
    
    def __init__(self, 타입: str, 내용: str, 아이디: Optional[str] = None, 속성들: Optional[Dict[str, Any]] = None):
        """
        BSS 메시지 초기화
        
        Args:
            타입: 메시지 타입 (SUBSCRIPTION, MNP, CHANGE, TERMINATION)
            내용: 메시지 내용
            아이디: 메시지 고유 식별자 (None이면 자동 생성)
            속성들: 추가 메시지 속성
        """
        self.아이디 = 아이디 or str(uuid.uuid4())
        self.타입 = 타입.upper()
        self.내용 = 내용
        self.생성시간 = datetime.now()
        self.속성들 = 속성들 or {}
    
    def 메시지검증(self) -> bool:
        """
        메시지 유효성 검증
        
        Returns:
            bool: 메시지가 유효하면 True, 그렇지 않으면 False
        """
        try:
            # 필수 필드 존재 확인
            if not self.아이디 or not self.타입 or not self.내용:
                return False
            
            # 타입 유효성 확인
            valid_types = [t.value for t in MessageType]
            if self.타입 not in valid_types:
                return False
            
            # 내용 길이 확인 (최소 1자 이상)
            if len(self.내용.strip()) == 0:
                return False
                
            return True
            
        except Exception:
            return False
    
    def 타입확인(self, 타입: str) -> bool:
        """
        메시지 타입이 지정된 타입과 일치하는지 확인
        
        Args:
            타입: 확인할 메시지 타입
            
        Returns:
            bool: 타입이 일치하면 True, 그렇지 않으면 False
        """
        return self.타입 == 타입.upper()
    
    def to_json(self) -> str:
        """
        메시지를 JSON 문자열로 변환
        
        Returns:
            str: JSON 형식의 메시지 문자열
        """
        return json.dumps({
            '아이디': self.아이디,
            '타입': self.타입,
            '내용': self.내용,
            '생성시간': self.생성시간.isoformat(),
            '속성들': self.속성들
        }, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BSS메시지':
        """
        JSON 문자열에서 BSS메시지 객체 생성
        
        Args:
            json_str: JSON 형식의 메시지 문자열
            
        Returns:
            BSS메시지: 생성된 메시지 객체
            
        Raises:
            ValueError: JSON 파싱 실패 또는 필수 필드 누락 시
        """
        try:
            data = json.loads(json_str)
            
            # 필수 필드 확인
            required_fields = ['아이디', '타입', '내용', '생성시간']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"필수 필드 누락: {field}")
            
            # 메시지 객체 생성
            message = cls(
                타입=data['타입'],
                내용=data['내용'],
                아이디=data['아이디'],
                속성들=data.get('속성들', {})
            )
            
            # 생성시간 복원
            message.생성시간 = datetime.fromisoformat(data['생성시간'])
            
            return message
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}")
        except Exception as e:
            raise ValueError(f"메시지 생성 실패: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        메시지를 딕셔너리로 변환
        
        Returns:
            dict: 메시지 딕셔너리
        """
        return {
            '아이디': self.아이디,
            '타입': self.타입,
            '내용': self.내용,
            '생성시간': self.생성시간.isoformat(),
            '속성들': self.속성들
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"BSS메시지(아이디={self.아이디}, 타입={self.타입}, 내용={self.내용[:50]}...)"
    
    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"BSS메시지(아이디='{self.아이디}', 타입='{self.타입}', 내용='{self.내용}', 생성시간='{self.생성시간}')"


# 편의를 위한 팩토리 함수들
def 가입메시지생성(내용: str, 고객정보: Optional[Dict] = None) -> BSS메시지:
    """가입 메시지 생성 헬퍼 함수"""
    속성들 = {'고객정보': 고객정보} if 고객정보 else {}
    return BSS메시지(타입=MessageType.SUBSCRIPTION.value, 내용=내용, 속성들=속성들)


def 번호이동메시지생성(내용: str, 이동정보: Optional[Dict] = None) -> BSS메시지:
    """번호이동 메시지 생성 헬퍼 함수"""
    속성들 = {'이동정보': 이동정보} if 이동정보 else {}
    return BSS메시지(타입=MessageType.MNP.value, 내용=내용, 속성들=속성들)


def 명의변경메시지생성(내용: str, 변경정보: Optional[Dict] = None) -> BSS메시지:
    """명의변경 메시지 생성 헬퍼 함수"""
    속성들 = {'변경정보': 변경정보} if 변경정보 else {}
    return BSS메시지(타입=MessageType.CHANGE.value, 내용=내용, 속성들=속성들)


def 해지메시지생성(내용: str, 해지정보: Optional[Dict] = None) -> BSS메시지:
    """해지 메시지 생성 헬퍼 함수"""
    속성들 = {'해지정보': 해지정보} if 해지정보 else {}
    return BSS메시지(타입=MessageType.TERMINATION.value, 내용=내용, 속성들=속성들)