# 파일 경로: src/consumer/termination_processor.py
# 해지 처리 서비스

import time
import random
from typing import Dict, Any
from src.consumer.base_processor import 기본처리서비스
from src.common.message_models import BSS메시지, MessageType


class 해지처리서비스(기본처리서비스):
    """
    해지 요청 메시지를 처리하는 서비스
    TERMINATION 타입 메시지만 처리
    """
    
    def __init__(self):
        """해지 처리 서비스 초기화"""
        super().__init__(MessageType.TERMINATION.value)
        
        # 해지 처리 전용 통계
        self.해지통계 = {
            '일반해지': 0,
            '즉시해지': 0,
            '번호보존해지': 0,
            '해지실패': 0
        }
        
        self.로거.info("해지 처리 서비스 초기화 완료")
    
    def 메시지처리(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        해지 메시지 처리
        
        Args:
            메시지: 처리할 해지 메시지
            
        Returns:
            dict: 처리 결과
        """
        try:
            self.로거.info(f"해지 처리 시작: {메시지.아이디}")
            
            # 메시지 타입 확인
            if not 메시지.타입확인(MessageType.TERMINATION.value):
                return {
                    '성공': False,
                    '메시지': f'잘못된 메시지 타입: {메시지.타입}',
                    '결과데이터': None
                }
            
            # 해지 처리 시뮬레이션 수행
            처리결과 = self.처리시뮬레이션()
            
            if 처리결과['성공']:
                # 성공 시 통계 업데이트
                해지정보 = {
                    '서비스번호': 서비스번호,
                    '계약번호': 계약번호,
                    '해지일시': time.strftime('%Y-%m-%d %H:%M:%S'),
                    '해지타입': 해지타입,
                    '요금정산': {
                        '사용요금': 사용요금,
                        '위약금': 위약금,
                        '할인금액': 할인금액,
                        '최종요금': 최종요금
                    },
                    '상태': '완료'
                }
                
                # 해지 타입별 추가 정보
                if 해지타입 == '즉시해지':
                    해지정보['즉시해지수수료'] = 10000
                    해지정보['최종요금'] = 최종요금 + 10000
                elif 해지타입 == '번호보존해지':
                    해지정보['보존기간'] = f"{random.randint(30, 90)}일"
                    해지정보['보존수수료'] = 5000
                    해지정보['최종요금'] = 최종요금 + 5000
                
                # 장비 반납 정보 (30% 확률)
                if random.random() < 0.3:
                    해지정보['장비반납'] = {
                        '단말기': f"DEVICE{random.randint(1000, 9999)}",
                        '반납방법': random.choice(['택배', '매장방문', '기사방문']),
                        '반납기한': time.strftime('%Y-%m-%d', 
                            time.localtime(time.time() + random.randint(86400 * 7, 86400 * 14)))  # 1-2주 후
                    }
                
                return {
                    '성공': True,
                    '해지타입': 해지타입,
                    '처리시간': round(처리시간, 3),
                    '해지정보': 해지정보
                }
            else:
                # 실패 시뮬레이션
                오류원인 = random.choice([
                    '미납요금 존재',
                    '약정기간 위반',
                    '장비 미반납',
                    '본인 확인 실패',
                    '시스템 오류',
                    '법정대리인 동의 필요'
                ])
                
                return {
                    '성공': False,
                    '해지타입': 해지타입,
                    '처리시간': round(처리시간, 3),
                    '오류': 오류원인
                }
                
        except Exception as e:
            return {
                '성공': False,
                '오류': f'시뮬레이션 실행 실패: {e}',
                '처리시간': 0
            }
    
    def 해지통계조회(self) -> Dict[str, Any]:
        """
        해지 처리 전용 통계 조회
        
        Returns:
            dict: 해지 통계 정보
        """
        기본통계 = self.처리통계조회()
        
        총해지시도 = sum(self.해지통계.values())
        해지성공률 = round(
            (총해지시도 - self.해지통계['해지실패']) / 총해지시도 * 100, 2
        ) if 총해지시도 > 0 else 0
        
        return {
            **기본통계,
            '해지별통계': {
                '일반해지': self.해지통계['일반해지'],
                '즉시해지': self.해지통계['즉시해지'],
                '번호보존해지': self.해지통계['번호보존해지'],
                '해지실패': self.해지통계['해지실패'],
                '총해지시도': 총해지시도,
                '해지성공률': f"{해지성공률}%"
            }
        }


# 메인 실행부 (컨테이너에서 직접 실행될 때)
if __name__ == "__main__":
    import signal
    import sys
    
    # 해지 처리 서비스 인스턴스 생성
    processor = 해지처리서비스()
    
    # Graceful shutdown을 위한 시그널 핸들러
    def signal_handler(signum, frame):
        processor.로거.info("종료 신호 수신, 해지 처리 서비스 종료 중...")
        processor.메시지처리중지()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 메시지 처리 시작
        processor.메시지처리시작()
        processor.로거.info("해지 처리 서비스 실행 중... (Ctrl+C로 종료)")
        
        # 메인 스레드에서 대기
        while True:
            time.sleep(25)  # 해지는 낮은 빈도로 통계 출력
            
            # 주기적으로 통계 출력 (모니터링 활성화 시)
            if processor.설정.모니터링상태확인():
                통계 = processor.해지통계조회()
                processor.로거.info(f"해지 처리 통계: {통계['기본통계']}")
                
    except KeyboardInterrupt:
        processor.로거.info("키보드 인터럽트 수신")
    except Exception as e:
        processor.로거.error(f"해지 처리 서비스 실행 중 오류: {e}")
    finally:
        processor.메시지처리중지()
        processor.로거.info("해지 처리 서비스 종료 완료")타입 = 처리결과.get('해지타입', '일반해지')
                self.해지통계[해지타입] += 1
                
                self.로거.info(f"해지 처리 완료: {메시지.아이디} - {해지타입}")
                
                return {
                    '성공': True,
                    '메시지': f'해지 처리 성공: {해지타입}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '처리타입': self.처리타입,
                        '해지타입': 해지타입,
                        '처리시간': 처리결과['처리시간'],
                        '해지정보': 처리결과.get('해지정보', {})
                    }
                }
            else:
                self.해지통계['해지실패'] += 1
                return {
                    '성공': False,
                    '메시지': f'해지 처리 실패: {처리결과["오류"]}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '오류원인': 처리결과.get('오류', '알 수 없는 오류')
                    }
                }
                
        except Exception as e:
            self.해지통계['해지실패'] += 1
            error_msg = f"해지 처리 중 예외 발생: {e}"
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
        해지 처리 시뮬레이션
        실제 요금 정산, 서비스 해지, 장비 반납 처리 대신 시뮬레이션 수행
        
        Returns:
            dict: 시뮬레이션 결과
        """
        try:
            # 처리 시간 시뮬레이션 (1.0~4.0초 - 요금 정산 및 장비 확인 시간 포함)
            처리시간 = random.uniform(1.0, 4.0)
            time.sleep(처리시간)
            
            # 해지 타입 랜덤 결정 (50% 일반해지, 25% 즉시해지, 15% 번호보존해지, 10% 실패)
            rand = random.random()
            if rand < 0.5:
                해지타입 = '일반해지'
                성공 = True
            elif rand < 0.75:
                해지타입 = '즉시해지'
                성공 = True
            elif rand < 0.9:
                해지타입 = '번호보존해지'
                성공 = True
            else:
                해지타입 = '해지실패'
                성공 = False
            
            if 성공:
                # 성공 시뮬레이션
                서비스번호 = f"010{random.randint(10000000, 99999999)}"
                계약번호 = f"CONTRACT{random.randint(100000, 999999)}"
                
                # 요금 정산 시뮬레이션
                사용요금 = random.randint(10000, 150000)
                위약금 = random.randint(0, 200000) if random.random() < 0.3 else 0
                할인금액 = random.randint(0, 50000) if random.random() < 0.4 else 0
                최종요금 = max(0, 사용요금 + 위약금 - 할인금액)
                
                해지