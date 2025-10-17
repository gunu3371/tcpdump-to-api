import subprocess
import re
import sys
import threading
import queue
import time

class TcpdumpParser:
    """
    tcpdump 프로세스를 별도 스레드에서 실행하고
    그 출력을 파싱하여 큐(Queue)에 저장하는 클래스입니다.
    수동으로 start() 및 stop() 메서드를 호출하여 제어해야 합니다.
    """
    
    def __init__(self):
        self.cmd = ['tcpdump', '-l', '-t', '-q', '-v', '-nn', '-i', "any"]
        
        # 정규표현식
        self.header_regex = re.compile(
            r"^(?P<interface>\S+)\s+"
            r"(?P<direction>In|Out)\s+"
            r"IP\s+\(.*\s+"
            r"proto\s+(?P<proto>\S+)\s+"
            r".*,\s+"
            r"length\s+(?P<length>\d+)\)$"
        )
        self.address_regex = re.compile(
            r"^(?P<src_ip>(?:\d{1,3}\.){3}\d{1,3})"
            r"(?:\.(?P<src_port>\S+))?\s+>\s+"
            r"(?P<dst_ip>(?:\d{1,3}\.){3}\d{1,3})"
            r"(?:\.(?P<dst_port>\S+))?:"
        )
        
        self.process = None
        self.packet_queue = queue.Queue()
        self.parser_thread = None

    def start(self):
        """
        tcpdump 서브프로세스와 파싱 스레드를 시작합니다.
        """
        print(f"Starting tcpdump on interface '{self.interface}'... (This may require sudo privileges)")
        try:
            # 1. tcpdump 프로세스 시작
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("--- tcpdump process started ---")

            # 2. 파싱 스레드 시작
            self.parser_thread = threading.Thread(target=self._run_parser, daemon=True)
            self.parser_thread.start()
            print("--- Parser thread started ---")
            
        except FileNotFoundError:
            print("Error: 'tcpdump' command not found. Please install it.", file=sys.stderr)
            raise
        except PermissionError:
            print("Error: Permission denied. Please run this script with sudo.", file=sys.stderr)
            raise

    def stop(self):
        """
        tcpdump 서브프로세스와 스레드를 확실하게 종료합니다.
        """
        print("\n--- Stopping tcpdump ---")
        
        # 1. tcpdump 프로세스 종료 (stdout이 닫힘)
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("--- tcpdump process terminated ---")

        # 2. 파싱 스레드 종료 대기
        if self.parser_thread:
            self.parser_thread.join()
        print("--- Parser thread terminated ---")

    def _run_parser(self):
        """
        [스레드에서 실행될 메서드]
        tcpdump의 stdout을 실시간으로 읽고 파싱하여 큐에 넣습니다.
        """
        try:
            if not self.process or not self.process.stdout:
                return

            packet_info = {}
            for line in iter(self.process.stdout.readline, ''):
                line = line.strip()
                
                header_match = self.header_regex.match(line)
                if header_match:
                    packet_info = header_match.groupdict()
                    continue

                if packet_info:
                    address_match = self.address_regex.match(line)
                    if address_match:
                        packet_info.update(address_match.groupdict())
                        packet_info['src_port'] = packet_info.get('src_port', 'N/A')
                        packet_info['dst_port'] = packet_info.get('dst_port', 'N/A')
                        
                        self.packet_queue.put(packet_info)
                        packet_info = {}
        
        except ValueError:
            pass
        except Exception as e:
            print(f"Parser thread error: {e}", file=sys.stderr)
        
        finally:
            # 스레드 종료 신호 'None' (sentinel 값)을 큐에 넣음
            self.packet_queue.put(None)

    def packets(self):
        """
        파싱된 패킷 정보를 큐에서 꺼내 'yield'하는 제너레이터입니다.
        큐에 'None'이 들어오면(파싱 스레드 종료 신호) 중지합니다.
        """
        while True:
            packet = self.packet_queue.get()
            if packet is None:
                break
            yield packet


# --- 클래스 사용 예시 ---
if __name__ == "__main__":
    
    # parser 인스턴스 생성
    parser = TcpdumpParser()
    
    try:
        # 1. 수동으로 start() 호출
        parser.start()
        
        print("\n--- Waiting for packets... (Press Ctrl+C to stop) ---")
        
        # 2. 'packets()' 제너레이터 순회
        for packet in parser.packets():
            print(packet)
            
    except (FileNotFoundError, PermissionError):
        print("Exiting due to startup error.", file=sys.stderr)
    except KeyboardInterrupt:
        # Ctrl+C가 눌리면 루프를 중단
        print("\n--- Parsing interrupted by user ---")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # 3. try 블록이 어떻게 끝나든(정상 종료, 예외) 
        #    반드시 stop()을 호출하여 리소스를 정리
        if parser.process: # start()가 성공적으로 실행된 경우에만 stop() 호출
            parser.stop()
