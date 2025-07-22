# 파일 경로: tests/test_integration.py
"""
통합 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.common.message_models import BSS메시지
from src.producer.message_router import 메시지라우터


class TestIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_메시지처리흐름(self):
        """메시지 처리 전체 흐름 테스트"""
        # Mock 객체 생성
        with patch('src.producer.message_producer.BSS메시지생산자') as mock_producer:
            mock_producer.return_value.큐전송.return_value = {
                '성공': True,
                '메시지': '전송 성공',
                '메시지아이디': 'test-id'
            }

            # 라우터 생성 및 메시지 전송
            라우터 = 메시지라우터()
            메시지 = BSS메시지("SUBSCRIPTION", "통합 테스트 메시지")

            결과 = 라우터.메시지전송(메시지)

            assert 결과['성공'] == True
            assert 'test-id' in str(결과)

    def test_설정연동(self):
        """설정과 다른 모듈 간 연동 테스트"""
        from src.common.config import 설정가져오기
        from src.producer.message_router import 메시지라우터

        설정 = 설정가져오기()
        라우터 = 메시지라우터()

        # 설정이 라우터에서 올바르게 사용되는지 확인
        assert 라우터.설정 is not None
        assert 라우터.설정.큐설정가져오기() is not None