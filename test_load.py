import asyncio
import aiohttp
import json
import time
from datetime import datetime


async def send_simple_request(session, count):
    """간단한 요청 전송"""
    url = "http://localhost:8000/"
    try:
        async with session.get(url) as response:
            return await response.json()
    except Exception as e:
        print(f"Error {count}: {e}")
        return None


async def load_test_simple(total_requests=1000, concurrent=10):
    """간단한 부하 테스트"""
    print(f"부하 테스트 시작: {total_requests}개 요청, 동시성 {concurrent}")

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrent)

        async def bounded_request(i):
            async with semaphore:
                return await send_simple_request(session, i)

        start_time = time.time()
        tasks = [bounded_request(i) for i in range(total_requests)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        success_count = sum(1 for r in results if r is not None)
        duration = end_time - start_time

        print(f"테스트 완료:")
        print(f"- 총 요청: {total_requests}")
        print(f"- 성공: {success_count}")
        print(f"- 실패: {total_requests - success_count}")
        print(f"- 소요 시간: {duration:.2f}초")
        print(f"- 초당 처리량: {success_count / duration:.2f} req/sec")


if __name__ == "__main__":
    asyncio.run(load_test_simple(100, 10))
