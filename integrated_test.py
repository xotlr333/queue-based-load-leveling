import subprocess
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

class IntegratedTester:
    def __init__(self):
        self.monitoring = True
        
    def monitor_system(self):
        """시스템 상태 모니터링"""
        while self.monitoring:
            try:
                # Pod 상태 확인
                result = subprocess.run(
                    ['kubectl', 'get', 'pods', '-n', 'bss-queue-system'],
                    capture_output=True, text=True
                )
                
                print(f"\n🔍 [{time.strftime('%H:%M:%S')}] Pod 상태:")
                print(result.stdout)
                
                # 간단한 메트릭
                lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
                running_pods = sum(1 for line in lines if 'Running' in line)
                total_pods = len(lines)
                
                print(f"📊 Running Pods: {running_pods}/{total_pods}")
                
            except Exception as e:
                print(f"모니터링 오류: {e}")
            
            time.sleep(5)
    
    def load_test(self, requests_count=20):
        """부하 테스트"""
        print(f"\n🚀 부하 테스트 시작: {requests_count}개 요청")
        
        def send_request(i):
            try:
                response = requests.get("http://localhost:8000/", timeout=5)
                return {"id": i, "status": response.status_code, "success": True}
            except Exception as e:
                return {"id": i, "error": str(e), "success": False}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(send_request, range(requests_count)))
        
        end_time = time.time()
        
        success_count = sum(1 for r in results if r.get("success"))
        duration = end_time - start_time
        
        print(f"✅ 테스트 완료: {success_count}/{requests_count} 성공")
        print(f"⏱️ 소요 시간: {duration:.2f}초")
        print(f"📈 처리량: {success_count/duration:.2f} req/sec")
        
        return results
    
    def run_integrated_test(self):
        """통합 테스트 실행"""
        print("🔬 BSS Queue System 통합 테스트 시작")
        
        # 백그라운드 모니터링 시작
        monitor_thread = threading.Thread(target=self.monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # API 연결 확인
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            print(f"✅ API 연결 확인: {response.status_code}")
        except Exception as e:
            print(f"❌ API 연결 실패: {e}")
            return
        
        # 여러 라운드 테스트
        for round_num in range(3):
            print(f"\n🔄 테스트 라운드 {round_num + 1}/3")
            self.load_test(20)
            time.sleep(10)  # 시스템 안정화 대기
        
        # 모니터링 종료
        self.monitoring = False
        print("\n🏁 통합 테스트 완료")

if __name__ == "__main__":
    tester = IntegratedTester()
    tester.run_integrated_test()
