import subprocess
import time
import os
from datetime import datetime

class MacOSPodMonitor:
    def __init__(self, namespace="bss-queue-system", interval=3):
        self.namespace = namespace
        self.interval = interval
        self.running = True
    
    def clear_screen(self):
        """화면 클리어 (macOS 호환)"""
        os.system('clear')
    
    def get_pod_resources(self):
        """Pod 리소스 정보 조회"""
        try:
            result = subprocess.run(
                ['kubectl', 'top', 'pods', '-n', self.namespace],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            return f"❌ 오류: {e}"
    
    def get_pod_status(self):
        """Pod 상태 정보 조회"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.namespace, '-o', 'wide'],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            return f"❌ 오류: {e}"
    
    def get_hpa_status(self):
        """HPA 상태 조회"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'hpa', '-n', self.namespace],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.returncode == 0 else "HPA 정보 없음"
        except Exception as e:
            return "HPA 조회 불가"
    
    def monitor(self):
        """실시간 모니터링 시작"""
        print(f"🚀 macOS Pod 모니터링 시작 ({self.interval}초 간격)")
        print("Ctrl+C로 종료")
        
        try:
            while self.running:
                self.clear_screen()
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print("╔" + "═" * 78 + "╗")
                print(f"║{'BSS Queue System 실시간 모니터링':^78}║")
                print(f"║{current_time:^78}║")
                print("╚" + "═" * 78 + "╝")
                print()
                
                # Pod 상태
                print("📊 Pod 상태:")
                pod_status = self.get_pod_status()
                if pod_status:
                    print(pod_status)
                else:
                    print("   ⏳ Pod 상태 조회 중...")
                print()
                
                # 리소스 사용량
                print("📈 리소스 사용량:")
                resources = self.get_pod_resources()
                if resources:
                    print(resources)
                else:
                    print("   ⏳ 메트릭 서버 대기 중...")
                print()
                
                # HPA 상태
                print("🔄 HPA 상태:")
                hpa_status = self.get_hpa_status()
                print(hpa_status)
                print()
                
                print(f"💡 {self.interval}초 후 자동 갱신... (Ctrl+C로 종료)")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.clear_screen()
            print("✅ 모니터링 종료")
            self.running = False
    
    def monitor_specific_pod(self, pod_pattern):
        """특정 Pod 패턴만 모니터링"""
        print(f"🎯 '{pod_pattern}' Pod 집중 모니터링 시작")
        
        try:
            while self.running:
                self.clear_screen()
                
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"🔍 [{current_time}] '{pod_pattern}' Pod 모니터링")
                print("-" * 60)
                
                # 특정 Pod만 필터링
                try:
                    # Pod 상태
                    status_result = subprocess.run(
                        ['kubectl', 'get', 'pods', '-n', self.namespace],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if status_result.returncode == 0:
                        print("📊 Pod 상태:")
                        for line in status_result.stdout.split('\n'):
                            if pod_pattern.lower() in line.lower():
                                print(f"   {line}")
                    
                    # 리소스 사용량
                    resource_result = subprocess.run(
                        ['kubectl', 'top', 'pods', '-n', self.namespace],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if resource_result.returncode == 0:
                        print("\n📈 리소스 사용량:")
                        lines = resource_result.stdout.split('\n')
                        if len(lines) > 0:
                            print(f"   {lines[0]}")  # 헤더
                            for line in lines[1:]:
                                if pod_pattern.lower() in line.lower():
                                    print(f"   {line}")
                    
                except Exception as e:
                    print(f"❌ 조회 오류: {e}")
                
                print(f"\n💡 {self.interval}초 후 갱신... (Ctrl+C로 종료)")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.clear_screen()
            print("✅ 모니터링 종료")
            self.running = False

def main():
    import sys
    
    monitor = MacOSPodMonitor()
    
    if len(sys.argv) > 1:
        pod_pattern = sys.argv[1]
        monitor.monitor_specific_pod(pod_pattern)
    else:
        monitor.monitor()

if __name__ == "__main__":
    main()
