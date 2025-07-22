# 파일 경로: src/consumer/mnp_processor.py
# 번호이동 처리 서비스

import time
import random
from typing import Dict, Any
from src.consumer.base_processor import 기본처리서비스
from src.common.message_models import BSS메시지, MessageType


class 번호이동처리서비스(기본처리서비스):
    """
    번호이동(MNP) 요청 메시지를 처리하는 서비스
    MNP 타입 메시지만 처리
    """
    
    def __init__(self):
        """번호이동 처리 서비스 초기화"""
        super().__init__(MessageType.MNP.value)
        
        # 번호이동 처리 전용 통계
        self.번호이동통계 = {
            '이동완료': 0,
            '이동대기': 0,
            '이동실패': 0,
            '이동취소': 0
        }
        
        self.로거.info("번호이동 처리 서비스 초기화 완료")
    
    def 메시지처리(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        번호이동 메시지 처리
        
        Args:
            메시지: 처리할 번호이동 메시지
            
        Returns:
            dict: 처리 결과
        """
        try:
            self.로거.info(f"번호이동 처리 시작: {메시지.아이디}")
            
            # 메시지 타입 확인
            if not 메시지.타입확인(MessageType.MNP.value):
                return {
                    '성공': False,
                    '메시지': f'잘못된 메시지 타입: {메시지.타입}',
                    '결과데이터': None
                }
            
            # 번호이동 처리 시뮬레이션 수행
            처리결과 = self.처리시뮬레이션()
            
            if 처리결과['성공']:
                # 성공 시 통계 업데이트
                이동상태 = 처리결과.get('이동상태', '이동완료')
                self.번호이동통계[이동상태] += 1
                
                self.로거.info(f"번호이동 처리 완료: {메시지.아이디} - {이동상태}")
                
                return {
                    '성공': True,
                    '메시지': f'번호이동 처리 성공: {이동상태}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '처리타입': self.처리타입,
                        '이동상태': 이동상태,
                        '처리시간': 처리결과['처리시간'],
                        '이동정보': 처리결과.get('이동정보', {})
                    }
                }
            else:
                self.번호이동통계['이동실패'] += 1
                return {
                    '성공': False,
                    '메시지': f'번호이동 처리 실패: {처리결과["오류"]}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '오류원인': 처리결과.get('오류', '알 수 없는 오류')
                    }
                }
                
        except Exception as e:
            self.번호이동통계['이동실패'] += 1
            error_msg = f"번호이동 처리 중 예외 발생: {e}"
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
        번호이동 처리 시뮬레이션
        실제 외부 API 연동 및 데이터베이스 작업 대신 시뮬레이션 수행
        
        Returns:
            dict: 시뮬레이션 결과
        """
        try:
            # 처리 시간 시뮬레이션 (1.0~5.0초 - MNP는 복잡한 처리)
            처리시간 = random.uniform(1.0, 5.0)
            time.sleep(처리시간)
            
            # 번호이동 상태 랜덤 결정 (60% 완료, 25% 대기, 10% 취소, 5% 실패)
            rand = random.random()
            if rand < 0.6:
                이동상태 = '이동완료'
                성공 = True
            elif rand < 0.85:
                이동상태 = '이동대기'
                성공 = True
            elif rand < 0.95:
                이동상태 = '이동취소'
                성공 = True
            else:
                이동상태 = '이동실패'
                성공 = False
            
            if 성공:
                # 성공 시뮬레이션
                기존번호 = f"010{random.randint(10000000, 99999999)}"
                신규번호 = f"010{random.randint(10000000, 99999999)}"
                기증통신사 = random.choice(['SKT', 'KT', 'LGU+'])
                
                이동정보 = {
                    '기존번호': 기존번호,
                    '신규번호': 신규번호,
                    '기증통신사': 기증통신사,
                    '이동일시': time.strftime('%Y-%m-%d %H:%M:%S'),
                    '상태': 이동상태
                }
                
                # 이동 대기인 경우 예상 완료일 추가
                if 이동상태 == '이동대기':
                    이동정보['예상완료일'] = time.strftime('%Y-%m-%d', 
                        time.localtime(time.time() + random.randint(86400, 259200)))  # 1-3일 후
                
                return {
                    '성공': True,
                    '이동상태': 이동상태,
                    '처리시간': round(처리시간, 3),
                    '이동정보': 이동정보
                }
            else:
                # 실패 시뮬레이션
                오류원인 = random.choice([
                    '기증통신사 연동 실패',
                    '번호 중복',
                    '고객 정보 불일치',
                    '네트워크 오류',
                    '외부 시스템 장애'
                ])
                
                return {
                    '성공': False,
                    '이동상태': 이동상태,
                    '처리시간': round(처리시간, 3),
                    '오류': 오류원인
                }
                
        except Exception as e:
            return {
                '성공': False,
                '오류': f'시뮬레이션 실행 실패: {e}',
                '처리시간': 0
            }
    
    def 번호이동통계조회(self) -> Dict[str, Any]:
        """
        번호이동 처리 전용 통계 조회
        
        Returns:
            dict: 번호이동 통계 정보
        """
        기본통계 = self.처리통계조회()
        
        총이동시도 = sum(self.번호이동통계.values())
        이동성공률 = round(
            (self.번호이동통계['이동완료'] + self.번호이동통계['이동대기']) / 총이동시도 * 100, 2
        ) if 총이동시도 > 0 else 0
        
        return {
            **기본통계,
            '번호이동별통계': {
                '이동완료': self.번호이동통계['이동완료'],
                '이동대기': self.번호이동통계['이동대기'],
                '이동취소': self.번호이동통계['이동취소'],
                '이동실패': self.번호이동통계['이동실패'],
                '총이동시도': 총이동시도,
                '이동성공률': f"{이동성공률}%"
            }
        }


# 메인 실행부 (컨테이너에서 직접 실행될 때)
if __name__ == "__main__":
    import signal
    import sys
    
    # 번호이동 처리 서비스 인스턴스 생성
    processor = 번호이동처리서비스()
    
    # Graceful shutdown을 위한 시그널 핸들러
    def signal_handler(signum, frame):
        processor.로거.info("종료 신호 수신, 번호이동 처리 서비스 종료 중...")
        processor.메시지처리중지()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 메시지 처리 시작
        processor.메시지처리시작()
        processor.로거.info("번호이동 처리 서비스 실행 중... (Ctrl+C로 종료)")
        
        # 메인 스레드에서 대기
        while True:
            time.sleep(15)  # MNP는 상대적으로 긴 주기로 통계 출력
            
            # 주기적으로 통계 출력 (모니터링 활성화 시)
            if processor.설정.모니터링상태확인():
                통계 = processor.번호이동통계조회()
                processor.로거.info(f"번호이동 처리 통계: {통계['기본통계']}")
                
    except KeyboardInterrupt:
        processor.로거.info("키보드 인터럽트 수신")
    except Exception as e:
        processor.로거.error(f"번호이동 처리 서비스 실행 중 오류: {e}")
    finally:
        processor.메시지처리중지()
        processor.로거.info("번호이동 처리 서비스 종료 완료")