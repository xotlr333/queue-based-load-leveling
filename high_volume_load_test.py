import asyncio
import aiohttp
import time
from datetime import datetime
import json

class HighVolumeLoadTester:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.results = []
        
    async def send_async_request(self, session, request_id):
        """비동기 요청 전송"""
        start_time = time.time()
        try:
            async with session.get(f"{self.api_url}/") as response:
                response_time = time.time() - start_time
                return {
                    "id": request_id,
                    "status": response.status,
                    "response_time": response_time,
                    "timestamp": time.time(),
                    "success": True
                }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "id": request_id,
                "error": str(e),
                "response_time": response_time,
                "timestamp": time.time(),
                "success": False
            }
    
    async def massive_load_test(self, total_requests=10000, concurrent_limit=200):
        """대용량 부하테스트 (10,000+ 요청)"""
        print(f"🔥 대용량 부하테스트 시작")
        print(f"   총 요청: {total_requests:,}")
        print(f"   최대 동시성: {concurrent_limit}")
        print(f"   시작 시간: {datetime.now()}")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def limited_request(session, request_id):
            async with semaphore:
                return await self.send_async_request(session, request_id)
        
        # 커넥션 풀 최적화
        connector = aiohttp.TCPConnector(
            limit=500,  # 총 연결 수
            limit_per_host=200,  # 호스트당 연결 수
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout
        ) as session:
            # 배치 단위로 요청 처리 (메모리 효율성)
            batch_size = 1000
            all_results = []
            
            for batch_start in range(0, total_requests, batch_size):
                batch_end = min(batch_start + batch_size, total_requests)
                batch_requests = range(batch_start, batch_end)
                
                print(f"   배치 처리: {batch_start:,} - {batch_end:,}")
                
                tasks = [limited_request(session, i) for i in batch_requests]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 예외 처리
                valid_results = []
                for result in batch_results:
                    if isinstance(result, dict):
                        valid_results.append(result)
                    else:
                        valid_results.append({
                            "error": str(result),
                            "success": False,
                            "timestamp": time.time()
                        })
                
                all_results.extend(valid_results)
                
                # 메모리 관리를 위한 중간 분석
                if len(all_results) % 5000 == 0:
                    self.print_interim_stats(all_results, start_time)
        
        end_time = time.time()
        
        # 최종 분석
        self.analyze_massive_results(all_results, end_time - start_time)
        return all_results
    
    def print_interim_stats(self, results, start_time):
        """중간 통계 출력"""
        successful = [r for r in results if r.get("success", False)]
        elapsed = time.time() - start_time
        
        print(f"   중간 통계: {len(successful):,}/{len(results):,} 성공, "
              f"평균 {len(successful)/elapsed:.1f} req/sec")
    
    def analyze_massive_results(self, results, total_duration):
        """대용량 결과 분석"""
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        print(f"\n📊 대용량 부하테스트 결과:")
        print(f"   총 요청: {len(results):,}")
        print(f"   성공: {len(successful_requests):,}")
        print(f"   실패: {len(failed_requests):,}")
        print(f"   성공률: {len(successful_requests)/len(results)*100:.1f}%")
        print(f"   총 소요 시간: {total_duration:.1f}초")
        print(f"   평균 처리량: {len(successful_requests)/total_duration:.1f} req/sec")
        
        if successful_requests:
            response_times = [r.get("response_time", 0) for r in successful_requests]
            response_times.sort()
            
            print(f"\n⏱️ 응답 시간 분석:")
            print(f"   평균: {sum(response_times)/len(response_times):.3f}초")
            print(f"   중앙값: {response_times[len(response_times)//2]:.3f}초")
            print(f"   P95: {response_times[int(len(response_times)*0.95)]:.3f}초")
            print(f"   P99: {response_times[int(len(response_times)*0.99)]:.3f}초")
            print(f"   최대: {max(response_times):.3f}초")
        
        # 시간대별 처리량 분석 (10초 단위)
        if successful_requests:
            self.analyze_throughput_over_time(successful_requests, total_duration)
    
    def analyze_throughput_over_time(self, successful_requests, total_duration):
        """시간대별 처리량 분석"""
        print(f"\n📈 시간대별 처리량 분석 (10초 단위):")
        
        # 타임스탬프 정규화
        min_time = min(r["timestamp"] for r in successful_requests)
        time_buckets = {}
        
        for request in successful_requests:
            bucket = int((request["timestamp"] - min_time) // 10) * 10
            time_buckets[bucket] = time_buckets.get(bucket, 0) + 1
        
        for second in sorted(time_buckets.keys())[:10]:  # 처음 100초만 표시
            throughput = time_buckets[second] / 10  # 10초 평균
            print(f"   {second:3d}-{second+9:3d}초: {throughput:6.1f} req/sec ({time_buckets[second]:,}개)")

# 다양한 시나리오 테스트
async def run_high_volume_scenarios():
    """다양한 대용량 시나리오 실행"""
    tester = HighVolumeLoadTester()
    
    scenarios = [
        {"name": "중간 규모", "requests": 5000, "concurrent": 100},
        {"name": "대규모", "requests": 10000, "concurrent": 150},
        {"name": "초대규모", "requests": 20000, "concurrent": 200},
        {"name": "극한 테스트", "requests": 50000, "concurrent": 300}
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"🧪 시나리오: {scenario['name']}")
        
        try:
            await tester.massive_load_test(
                scenario['requests'], 
                scenario['concurrent']
            )
        except Exception as e:
            print(f"❌ 시나리오 실패: {e}")
        
        print("\n⏳ 시스템 안정화 대기 중 (30초)...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(run_high_volume_scenarios())
