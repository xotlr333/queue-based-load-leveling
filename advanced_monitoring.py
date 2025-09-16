import subprocess
import threading
import time
import psutil
from datetime import datetime

class AdvancedMonitor:
    def __init__(self):
        self.monitoring = True
        self.stats = {
            'pod_counts': [],
            'cpu_usage': [],
            'memory_usage': [],
            'network_stats': [],
            'timestamps': []
        }
    
    def monitor_system_resources(self):
        """시스템 리소스 집중 모니터링"""
        while self.monitoring:
            try:
                # Minikube 상태
                result = subprocess.run(
                    ['kubectl', 'get', 'pods', '-n', 'bss-queue-system', '--no-headers'],
                    capture_output=True, text=True
                )
                
                running_pods = 0
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if 'Running' in line:
                            running_pods += 1
                
                # 로컬 시스템 리소스
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                network = psutil.net_io_counters()
                
                # 통계 저장
                current_time = datetime.now()
                self.stats['pod_counts'].append(running_pods)
                self.stats['cpu_usage'].append(cpu_percent)
                self.stats['memory_usage'].append(memory.percent)
                self.stats['network_stats'].append({
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                })
                self.stats['timestamps'].append(current_time)
                
                # 콘솔 출력
                print(f"\r🔍 [{current_time.strftime('%H:%M:%S')}] "
                      f"Pods: {running_pods:2d} | "
                      f"CPU: {cpu_percent:5.1f}% | "
                      f"Memory: {memory.percent:5.1f}% | "
                      f"Network: ↑{network.bytes_sent/1024/1024:.1f}MB "
                      f"↓{network.bytes_recv/1024/1024:.1f}MB", end='')
                
            except Exception as e:
                print(f"\n⚠️ 모니터링 오류: {e}")
            
            time.sleep(2)
    
    def start_monitoring(self):
        """모니터링 시작"""
        monitor_thread = threading.Thread(target=self.monitor_system_resources)
        monitor_thread.daemon = True
        monitor_thread.start()
        print("📊 고급 모니터링 시작...")
        return monitor_thread
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        print("\n📊 모니터링 중지")
        
        if self.stats['timestamps']:
            duration = (self.stats['timestamps'][-1] - self.stats['timestamps'][0]).total_seconds()
            max_pods = max(self.stats['pod_counts'])
            avg_cpu = sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage'])
            max_memory = max(self.stats['memory_usage'])
            
            print(f"\n📈 모니터링 요약:")
            print(f"   모니터링 시간: {duration:.0f}초")
            print(f"   최대 Pod 수: {max_pods}")
            print(f"   평균 CPU 사용률: {avg_cpu:.1f}%")
            print(f"   최대 메모리 사용률: {max_memory:.1f}%")

if __name__ == "__main__":
    monitor = AdvancedMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
