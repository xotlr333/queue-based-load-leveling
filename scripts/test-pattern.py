# 파일 경로: scripts/test-pattern.py
# 패턴 검증 테스트 스크립트

#!/usr/bin/env python3
"""
Queue-Based Load Leveling 패턴 검증 테스트 스크립트
"""

import asyncio
import sys
import argparse
from src.experiments.load_generator import 부하생성기
from src.experiments.pattern_validator import 패턴검증기


async def 기본부하테스트(api_url: str):
    """기본 부하 테스트"""
    print("=== 기본 부하 테스트 ===")

    generator = 부하생성기(api_url)

    # 1. 급증 부하 테스트
    print("1. 급증 부하 테스트 (500개 메시지, 30초)")
    result = await generator.급증부하생성(500, 30)
    print(f"   결과: {result['성공']}, 성공률: {result.get('결과', {}).get('성공률', 0)}%")

    # 2. 지속 부하 테스트
    print("2. 지속 부하 테스트 (10/초, 60초)")
    result = await generator.지속부하생성(10, 60)
    print(f"   결과: {result['성공']}, 처리량: {result.get('결과', {}).get('처리량', 0)}/초")


async def 패턴검증테스트(api_url: str):
    """패턴 검증 테스트"""
    print("=== Queue-Based Load Leveling 패턴 검증 ===")

    validator = 패턴검증기(api_url)

    # 1. 부하 평활화 검증
    print("1. 부하 평활화 검증 중...")
    result1 = await validator.부하평활화검증(1000, 120)
    print(f"   결과: {'성공' if result1.성공 else '실패'}, 점수: {result1.점수:.1f}")

    # 2. 시스템 보호 검증
    print("2. 시스템 보호 검증 중...")
    result2 = await validator.시스템보호검증(50, 180)
    print(f"   결과: {'성공' if result2.성공 else '실패'}, 점수: {result2.점수:.1f}")

    # 3. 큐 버퍼링 효과 검증
    print("3. 큐 버퍼링 효과 검증 중...")
    result3 = await validator.큐버퍼링효과검증(2000)
    print(f"   결과: {'성공' if result3.성공 else '실패'}, 점수: {result3.점수:.1f}")

    # 4. 종합 보고서 생성
    print("4. 종합 보고서 생성 중...")
    report = validator.검증보고서생성()

    print(f"\n=== 검증 결과 요약 ===")
    print(f"전체 점수: {report['종합결과']['평균점수']}")
    print(f"성공률: {report['종합결과']['성공률']}%")
    print(f"등급: {report['종합결과']['등급']}")
    print(f"패턴 효과: {report['종합결과']['패턴효과']}")


def main():
    parser = argparse.ArgumentParser(description='BSS Queue Pattern 테스트')
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='API Gateway URL')
    parser.add_argument('--test-type', choices=['basic', 'validation', 'all'],
                        default='basic', help='테스트 타입')

    args = parser.parse_args()

    async def run_tests():
        try:
            if args.test_type in ['basic', 'all']:
                await 기본부하테스트(args.api_url)

            if args.test_type in ['validation', 'all']:
                await 패턴검증테스트(args.api_url)

        except KeyboardInterrupt:
            print("\n테스트가 중단되었습니다.")
        except Exception as e:
            print(f"테스트 실행 중 오류: {e}")
            sys.exit(1)

    print(f"BSS Queue-Based Load Leveling 패턴 테스트 시작")
    print(f"API URL: {args.api_url}")
    print(f"테스트 타입: {args.test_type}")
    print("-" * 50)

    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
