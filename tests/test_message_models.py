# 파일 경로: tests/test_message_models.py
"""
BSS메시지 모델 테스트
"""

import pytest
from datetime import datetime
from src.common.message_models import BSS메시지, MessageType, 가입메시지생성


class TestBSS메시지:
    """BSS메시지 클래스 테스트"""

    def test_메시지생성(self):
        """메시지 생성 테스트"""
        메시지 = BSS메시지("SUBSCRIPTION", "테스트 가입 메시지")

        assert 메시지.타입 == "SUBSCRIPTION"
        assert 메시지.내용 == "테스트 가입 메시지"
        assert 메시지.아이디 is not None
        assert isinstance(메시지.생성시간, datetime)

    def test_메시지검증_성공(self):
        """메시지 검증 성공 테스트"""
        메시지 = BSS메시지("SUBSCRIPTION", "유효한 메시지")

        assert 메시지.메시지검증() == True

    def test_메시지검증_실패(self):
        """메시지 검증 실패 테스트"""
        # 빈 내용
        메시지1 = BSS메시지("SUBSCRIPTION", "")
        assert 메시지1.메시지검증() == False

        # 잘못된 타입
        메시지2 = BSS메시지("INVALID_TYPE", "테스트")
        assert 메시지2.메시지검증() == False

    def test_타입확인(self):
        """메시지 타입 확인 테스트"""
        메시지 = BSS메시지("SUBSCRIPTION", "테스트")

        assert 메시지.타입확인("SUBSCRIPTION") == True
        assert 메시지.타입확인("subscription") == True  # 대소문자 무관
        assert 메시지.타입확인("MNP") == False

    def test_JSON변환(self):
        """JSON 변환 테스트"""
        원본메시지 = BSS메시지("MNP", "번호이동 테스트", 속성들={"테스트": True})

        # JSON 문자열로 변환
        json_str = 원본메시지.to_json()
        assert isinstance(json_str, str)

        # JSON에서 메시지 복원
        복원메시지 = BSS메시지.from_json(json_str)
        assert 복원메시지.타입 == 원본메시지.타입
        assert 복원메시지.내용 == 원본메시지.내용
        assert 복원메시지.아이디 == 원본메시지.아이디


def test_헬퍼함수들():
    """메시지 생성 헬퍼 함수 테스트"""
    # 가입 메시지 생성
    가입메시지 = 가입메시지생성("신규 가입", {"고객ID": "CUST001"})
    assert 가입메시지.타입 == "SUBSCRIPTION"
    assert "신규 가입" in 가입메시지.내용
    assert 가입메시지.속성들["고객정보"]["고객ID"] == "CUST001"