# 파일 경로: src/consumer/__init__.py
"""
소비자 모듈 - 메시지 처리 서비스들
"""

from .base_processor import 기본처리서비스
from .subscription_processor import 가입처리서비스
from .mnp_processor import 번호이동처리서비스
from .change_processor import 명의변경처리서비스
from .termination_processor import 해지처리서비스

__all__ = [
    '기본처리서비스',
    '가입처리서비스',
    '번호이동처리서비스',
    '명의변경처리서비스',
    '해지처리서비스'
]
