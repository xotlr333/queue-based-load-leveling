# 파일 경로: tests/conftest.py
"""
pytest 설정 및 픽스처
"""

import pytest
import os
from unittest.mock import Mock


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 설정"""
    # 테스트용 환경변수 설정
    os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'
    os.environ['QUEUE_NAME'] = 'test_queue'
    os.environ['MONITORING_ENABLED'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'


@pytest.fixture
def mock_rabbitmq():
    """RabbitMQ Mock 픽스처"""
    mock_connection = Mock()
    mock_channel = Mock()
    mock_connection.channel.return_value = mock_channel

    return mock_connection, mock_channel


@pytest.fixture
def sample_message():
    """샘플 메시지 픽스처"""
    from src.common.message_models import BSS메시지
    return BSS메시지("SUBSCRIPTION", "테스트 메시지", 속성들={"테스트": True})