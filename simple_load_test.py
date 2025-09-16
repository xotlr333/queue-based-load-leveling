import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def send_request(request_id):
    """단일 요청 전송"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return {"id": request_id, "status": response.status_code, "success": True}
    except Exception as e:
        return {"id": request_id, "error": str(e), "success": False}

def load_test_simple(total_requests=50, max_workers=10):
    """간단한 부하 테스트"""
    print(f"부하 테스트 시작: {total_requests}개 요청, 동시성 {max_workers}")
    
    start_time = time.time()
    
    # ThreadPoolExecutor를 사용한 동시 요청
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(send_request, i) for i in range(total_requests)]
        results = [future.result() for future in futures]
    
    end_time = time.time()
    
    # 결과 분석
    success_count = sum(1 for r in results if r.get("success", False))
    duration = end_time - start_time
    
    print(f"\n=== 테스트 결과 ===")
    print(f"총 요청: {total_requests}")
    print(f"성공: {success_count}")
    print(f"실패: {total_requests - success_count}")
    print(f"소요 시간: {duration:.2f}초")
    print(f"초당 처리량: {success_count / duration:.2f} req/sec")
    
    # 실패한 요청 상세 정보
    failed_requests = [r for r in results if not r.get("success", False)]
    if failed_requests:
        print(f"\n실패한 요청 상세:")
        for fail in failed_requests[:5]:  # 최대 5개만 표시
            print(f"  - 요청 {fail['id']}: {fail.get('error', 'Unknown error')}")

def burst_test():
    """급증 부하 테스트"""
    print("\n=== 급증 부하 테스트 ===")
    load_test_simple(100, 20)  # 100개 요청을 20개 동시 처리

def sustained_test():
    """지속 부하 테스트"""
    print("\n=== 지속 부하 테스트 ===")
    for i in range(5):
        print(f"라운드 {i+1}/5")
        load_test_simple(20, 5)
        time.sleep(2)

if __name__ == "__main__":
    # 기본 연결 테스트
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Producer API 연결 확인: {response.status_code}")
    except Exception as e:
        print(f"❌ Producer API 연결 실패: {e}")
        print("포트 포워딩을 확인하세요: kubectl port-forward svc/bss-producer-service 8000:8000 -n bss-queue-system")
        exit(1)
    
    # 부하 테스트 실행
    load_test_simple(50, 10)
    burst_test()
    sustained_test()
