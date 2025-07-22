# 파일 경로: src/consumer/change_processor.py
# 명의변경 처리 서비스

import time
import random
from typing import Dict, Any
from src.consumer.base_processor import 기본처리서비스
from src.common.message_models import BSS메시지, MessageType


class 명의변경처리서비스(기본처리서비스):
    """
    명의변경 요청 메시지를 처리하는 서비스
    CHANGE 타입 메시지만 처리
    """
    
    def __init__(self):
        """명의변경 처리 서비스 초기화"""
        super().__init__(MessageType.CHANGE.value)
        
        # 명의변경 처리 전용 통계
        self.명의변경통계 = {
            '개인전환': 0,
            '법인전환': 0,
            '가족간이동': 0,
            '변경실패': 0
        }
        
        self.로거.info("명의변경 처리 서비스 초기화 완료")
    
    def 메시지처리(self, 메시지: BSS메시지) -> Dict[str, Any]:
        """
        명의변경 메시지 처리
        
        Args:
            메시지: 처리할 명의변경 메시지
            
        Returns:
            dict: 처리 결과
        """
        try:
            self.로거.info(f"명의변경 처리 시작: {메시지.아이디}")
            
            # 메시지 타입 확인
            if not 메시지.타입확인(MessageType.CHANGE.value):
                return {
                    '성공': False,
                    '메시지': f'잘못된 메시지 타입: {메시지.타입}',
                    '결과데이터': None
                }
            
            # 명의변경 처리 시뮬레이션 수행
            처리결과 = self.처리시뮬레이션()
            
            if 처리결과['성공']:
                # 성공 시 통계 업데이트
                변경타입 = 처리결과.get('변경타입', '개인전환')
                self.명의변경통계[변경타입] += 1
                
                self.로거.info(f"명의변경 처리 완료: {메시지.아이디} - {변경타입}")
                
                return {
                    '성공': True,
                    '메시지': f'명의변경 처리 성공: {변경타입}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '처리타입': self.처리타입,
                        '변경타입': 변경타입,
                        '처리시간': 처리결과['처리시간'],
                        '변경정보': 처리결과.get('변경정보', {})
                    }
                }
            else:
                self.명의변경통계['변경실패'] += 1
                return {
                    '성공': False,
                    '메시지': f'명의변경 처리 실패: {처리결과["오류"]}',
                    '결과데이터': {
                        '메시지아이디': 메시지.아이디,
                        '오류원인': 처리결과.get('오류', '알 수 없는 오류')
                    }
                }
                
        except Exception as e:
            self.명의변경통계['변경실패'] += 1
            error_msg = f"명의변경 처리 중 예외 발생: {e}"
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
        명의변경 처리 시뮬레이션
        실제 고객정보 변경 및 계약서 처리 대신 시뮬레이션 수행
        
        Returns:
            dict: 시뮬레이션 결과
        """
        try:
            # 처리 시간 시뮬레이션 (0.5~3.0초 - 문서 검증 시간 포함)
            처리시간 = random.uniform(0.5, 3.0)
            time.sleep(처리시간)
            
            # 변경 타입 랜덤 결정 (40% 개인전환, 25% 법인전환, 25% 가족간이동, 10% 실패)
            rand = random.random()
            if rand < 0.4:
                변경타입 = '개인전환'
                성공 = True
            elif rand < 0.65:
                변경타입 = '법인전환'
                성공 = True
            elif rand < 0.9:
                변경타입 = '가족간이동'
                성공 = True
            else:
                변경타입 = '변경실패'
                성공 = False
            
            if 성공:
                # 성공 시뮬레이션
                기존명의자 = f"고객{random.randint(1000, 9999)}"
                신규명의자 = f"고객{random.randint(1000, 9999)}"
                계약번호 = f"CONTRACT{random.randint(100000, 999999)}"
                
                변경정보 = {
                    '기존명의자': 기존명의자,
                    '신규명의자': 신규명의자,
                    '계약번호': 계약번호,
                    '변경일시': time.strftime('%Y-%m-%d %H:%M:%S'),
                    '변경타입': 변경타입,
                    '상태': '완료'
                }
                
                # 변경 타입별 추가 정보
                if 변경타입 == '법인전환':
                    변경정보['사업자번호'] = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10000, 99999)}"
                    변경정보['법인명'] = f"(주)테스트{random.randint(1, 100)}"
                elif 변경타입 == '가족간이동':
                    변경정보['관계'] = random.choice(['배우자', '자녀', '부모', '형제자매'])
                    변경정보['가족증명서'] = f"DOC{random.randint(100000, 999999)}"
                
                return {
                    '성공': True,
                    '변경타입': 변경타입,
                    '처리시간': round(처리시간, 3),
                    '변경정보': 변경정보
                }
            else:
                # 실패 시뮬레이션
                오류원인 = random.choice([
                    '신분증 확인 실패',
                    '서류 미비',
                    '신용정보 불량',
                    '중복 계약 존재',
                    '시스템 오류',
                    '법정대리인 동의 필요'
                ])
                
                return {
                    '성공': False,
                    '변경타입': 변경타입,
                    '처리시간': round(처리시간, 3),
                    '오류': 오류원인
                }
                
        except Exception as e:
            return {
                '성공': False,
                '오류': f'시뮬레이션 실행 실패: {e}',
                '처리시간': 0
            }
    
    def 명의변경통계조회(self) -> Dict[str, Any]:
        """
        명의변경 처리 전용 통계 조회
        
        Returns:
            dict: 명의변경 통계 정보
        """
        기본통계 = self.처리통계조회()
        
        총변경시도 = sum(self.명의변경통계.values())
        변경성공률 = round(
            (총변경시도 - self.명의변경통계['변경실패']) / 총변경시도 * 100, 2
        ) if 총변경시도 > 0 else 0
        
        return {
            **기본통계,
            '명의변경별통계': {
                '개인전환': self.명의변경통계['개인전환'],
                '법인전환': self.명의변경통계['법인전환'],
                '가족간이동': self.명의변경통계['가족간이동'],
                '변경실패': self.명의변경통계['변경실패'],
                '총변경시도': 총변경시도,
                '변경성공률': f"{변경성공률}%"
            }
        }


# 메인 실행부 (컨테이너에서 직접 실행될 때)
if __name__ == "__main__":
    import signal
    import sys
    
    # 명의변경 처리 서비스 인스턴스 생성
    processor = 명의변경처리서비스()
    
    # Graceful shutdown을 위한 시그널 핸들러
    def signal_handler(signum, frame):
        processor.로거.info("종료 신호 수신, 명의변경 처리 서비스 종료 중...")
        processor.메시지처리중지()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 메시지 처리 시작
        processor.메시지처리시작()
        processor.로거.info("명의변경 처리 서비스 실행 중... (Ctrl+C로 종료)")
        
        # 메인 스레드에서 대기
        while True:
            time.sleep(20)  # 명의변경은 낮은 빈도로 통계 출력
            
            # 주기적으로 통계 출력 (모니터링 활성화 시)
            if processor.설정.모니터링상태확인():
                통계 = processor.명의변경통계조회()
                processor.로거.info(f"명의변경 처리 통계: {통계['기본통계']}")
                
    except KeyboardInterrupt:
        processor.로거.info("키보드 인터럽트 수신")
    except Exception as e:
        processor.로거.error(f"명의변경 처리 서비스 실행 중 오류: {e}")
    finally:
        processor.메시지처리중지()
        processor.로거.info("명의변경 처리 서비스 종료 완료")