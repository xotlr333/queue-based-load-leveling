# 파일 경로: tests/test_config.py
"""
설정 관리자 테스트
"""

import os
import pytest
from src.common.config import 설정관리자, 설정가져오기, 설정초기화


class Test설정관리자:
    """설정관리자 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전 설정 초기화"""
        설정초기화()

    def test_기본설정(self):
        """기본 설정 테스트"""
        설정 = 설정관리자()

        assert 설정.연결문자열가져오기() is not None
        assert isinstance(설정.모니터링상태확인(), bool)
        assert 설정.큐설정가져오기()["큐이름"] is not None

    def test_환경변수설정(self):
        """환경변수 기반 설정 테스트"""
        # 환경변수 설정
        os.environ['MONITORING_ENABLED'] = 'false'
        os.environ['QUEUE_NAME'] = 'test_queue'

        설정 = 설정관리자()

        assert 설정.모니터링상태확인() == False
        assert 설정.큐설정가져오기()["큐이름"] == 'test_queue'

    def test_싱글톤패턴(self):
        """싱글톤 패턴 테스트"""
        설정1 = 설정가져오기()
        설정2 = 설정가져오기()

        assert 설정1 is 설정2