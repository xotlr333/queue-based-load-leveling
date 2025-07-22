# 파일 경로: src/consumer/subscription_processor.py
# 가입 처리 서비스

import time
import random
from typing import Dict, Any
from src.consumer.base_processor import 기본처리서비스
from src.common.message_models import BSS메시지, MessageType


class 가입처리서비스(기본처리서비스):
    """
    가입 요청 메시지를 처리하는 서비스
    SUBSCRIPTION 타입 메시지만 처리
    """
    
    def __init__(self):
        """가입 처리 서비스 초기화"""
        super().__init__(MessageType.SUBSCRIPTION.value)
        
        # 가입 처리 전용 통계
        self.가입통계 = {
            '신규가입': 0,
            '재가입': 0,
            '가입실패': 0
        }
        
        self.로거.info("가입 처리 서비스 초기화 완료")
    
    def 메시지처리(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        가입 메시지 처리
        
        Args:
            메시지: 처리할 가입 메시지
            
        Returns:
            dict: 처리 결과
        """
        try:
            self.로거.info(f"가입 처리 시작: {메시지.아이디}")
            
            # 메시지 타입 확인
            if not 메시지.타입확인(MessageType.SUBSCRIPTION.value):
                return {
                    '성공': False,
                    '메시지': f'잘못된 메시지 타입: {메시지.타입}',
                    '결과데이터': None
                }
            
            # 가입 처리 시뮬레이션 수행
            처리결과 = self.처리시뮬레이션()
            
            if 처리결과['성공']:
                # 성공 시 통계 업데이트
                가입타입 = 처리결과.get('가입타입', '신규가입')
                self.가입통계[가입타입] += 1
                
                self.로거.info(f"가입 처리 완료: {메시지.아이디} - {가입타입}")
                
                return {
                    '성공': True,
                    '메시지': f'가입 처리 성공: {가입타입}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '처리타입': self.처리타입,
                        '가입타입': 가입타입,
                        '처리시간': 처리결과['처리시간'],
                        '고객정보': 처리결과.get('고객정보', {})
                    }
                }
            else:
                self.가입통계['가입실패'] += 1
                return {
                    '성공': False,
                    '메시지': f'가입 처리 실패: {처리결과["오류"]}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '오류원인': 처리결과.get('오류', '알 수 없는 오류')
                    }
                }
                
        except Exception as e:
            self.가입통계['가입실패'] += 1
            error_msg = f"가입 처리 중 예외 발생: {e}"
            self.로거.error(error_msg)
            
            return {
                '성공': False,
                '메시지': error_msg,
                '결과데이터': {
                    '메시지아이디': 메시지.아이디,
                    '예외타입': type(e).__name__
                }
            }
    
    def 처리시뮬레이션(self) -> Dict[str, Any]:
        """
        가입 처리 시뮬레이션
        실제 데이터베이스 작업 대신 시뮬레이션 수행
        
        Returns:
            dict: 시뮬레이션 결과
        """
        try:
            # 처리 시간 시뮬레이션 (0.1~2.0초)
            처리시간 = random.uniform(0.1, 2.0)
            time.sleep(처리시간)
            
            # 가입 타입 랜덤 결정 (80% 신규가입, 15% 재가입, 5% 실패)
            rand = random.random()
            if rand < 0.8:
                가입타입 = '신규가입'
                성공 = True
            elif rand < 0.95:
                가입타입 = '재가입'
                성공 = True
            else:
                가입타입 = '가입실패'
                성공 = False
            
            if 성공:
                # 성공 시뮬레이션
                고객번호 = f"CUST{random.randint(100000, 999999)}"
                서비스번호 = f"010{random.randint(10000000, 99999999)}"
                
                return {
                    '성공': True,
                    '가입타입': 가입타입,
                    '처리시간': round(처리시간, 3),
                    '고객정보': {
                        '고객번호': 고객번호,
                        '서비스번호': 서비스번호,
                        '가입일시': time.strftime('%Y-%m-%d %H:%M:%S'),
                        '상태': '활성'
                    }
                }
            else:
                # 실패 시뮬레이션
                오류원인 = random.choice([
                    '신용정보 불량',
                    '중복 가입',
                    '서류 미비',
                    '시스템 오류'
                ])
                
                return {
                    '성공': False,
                    '가입타입': 가입타입,
                    '처리시간': round(처리시간, 3),
                    '오류': 오류원인
                }
                
        except Exception as e:
            return {
                '성공': False,
                '오류': f'시뮬레이션 실행 실패: {e}',
                '처리시간': 0
            }
    
    def 가입통계조회(self) -> Dict[str, Any]:
        """
        가입 처리 전용 통계 조회
        
        Returns:
            dict: 가입 통계 정보
        """
        기본통계 = self.처리통계조회()
        
        총가입시도 = sum(self.가입통계.values())
        가입성공률 = round(
            (self.가입통계['신규가입'] + self.가입통계['재가입']) / 총가입시도 * 100, 2
        ) if 총가입시도 > 0 else 0
        
        return {
            **기본통계,
            '가입별통계': {
                '신규가입': self.가입통계['신규가입'],
                '재가입': self.가입통계['재가입'],
                '가입실패': self.가입통계['가입실패'],
                '총가입시도': 총가입시도,
                '가입성공률': f"{가입성공률}%"
            }
        }


# 메인 실행부 (컨테이너에서 직접 실행될 때)
if __name__ == "__main__":
    import signal
    import sys
    
    # 가입 처리 서비스 인스턴스 생성
    processor = 가입처리서비스()
    
    # Graceful shutdown을 위한 시그널 핸들러
    def signal_handler(signum, frame):
        processor.로거.info("종료 신호 수신, 가입 처리 서비스 종료 중...")
        processor.메시지처리중지()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 메시지 처리 시작
        processor.메시지처리시작()
        processor.로거.info("가입 처리 서비스 실행 중... (Ctrl+C로 종료)")
        
        # 메인 스레드에서 대기
        while True:
            time.sleep(10)
            
            # 주기적으로 통계 출력 (모니터링 활성화 시)
            if processor.설정.모니터링상태확인():
                통계 = processor.가입통계조회()
                processor.로거.info(f"가입 처리 통계: {통계['기본통계']}")
                
    except KeyboardInterrupt:
        processor.로거.info("키보드 인터럽트 수신")
    except Exception as e:
        processor.로거.error(f"가입 처리 서비스 실행 중 오류: {e}")
    finally:
        processor.메시지처리중지()
        processor.로거.info("가입 처리 서비스 종료 완료")