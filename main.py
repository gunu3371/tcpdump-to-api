import time
import requests
import threading
import os
import signal
import queue
from dotenv import load_dotenv
from parser import TcpdumpParser

# 파싱된 데이터를 임시 저장할 리스트
packet_buffer = []
# 버퍼 접근을 동기화하기 위한 Lock
buffer_lock = threading.Lock()


class GracefulKiller:
    """
    SIGINT 및 SIGTERM 신호를 정상적으로 처리하여
    애플리케이션이 안전하게 종료될 수 있도록 돕는 클래스입니다.
    """

    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        """신호가 수신되면 kill_now 플래그를 True로 설정합니다."""
        print("Graceful shutdown signal received...")
        self.kill_now = True


# 주기적으로 데이터를 POST로 전송하는 함수
def send_data_periodically(url, api_key, interval, killer):
    """
    지정된 간격(interval)마다 버퍼의 데이터를 POST로 전송합니다.
    killer.kill_now가 True가 되면 스레드가 종료됩니다.
    """
    while not killer.kill_now:
        # killer.kill_now를 더 자주 확인할 수 있도록 sleep을 짧게 분할
        for _ in range(interval):
            if killer.kill_now:
                break
            time.sleep(1)

        if killer.kill_now:
            break

        # 버퍼에 데이터가 있는지 확인
        if not packet_buffer:
            continue

        # Lock을 사용하여 버퍼의 데이터를 안전하게 복사하고 비움
        with buffer_lock:
            data_to_send = list(packet_buffer)
            packet_buffer.clear()

        if not data_to_send:
            continue

        try:
            # POST 요청 전송 (json 형식)
            response = requests.post(url, json=data_to_send, headers={"key": api_key})
            response.raise_for_status()  # 2xx 상태 코드가 아닐 경우 예외 발생
            print(f"Successfully sent {len(data_to_send)} packets.")

        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")
            # 전송 실패 시, 데이터를 다시 버퍼에 추가
            with buffer_lock:
                # 데이터를 맨 앞에 추가하여 순서 유지
                packet_buffer[:0] = data_to_send


def main():
    """
    메인 함수: TcpdumpParser를 실행하고,
    파싱된 데이터를 버퍼에 추가하며, 종료 신호를 처리합니다.
    """
    load_dotenv()  # .env 파일에서 환경 변수 로드
    killer = GracefulKiller()

    parser = TcpdumpParser()
    post_url = os.getenv("POST_URL")
    api_key = os.getenv("API_KEY")
    send_interval = int(os.getenv("SEND_INTERVAL", 10))

    # 데이터 전송 스레드 시작
    sender_thread = threading.Thread(
        target=send_data_periodically,
        args=(post_url, api_key, send_interval, killer),
        daemon=True,
    )
    sender_thread.start()

    print("Starting tcpdump parser...")
    parser.start()

    print("Application started. Waiting for packets or shutdown signal.")
    while not killer.kill_now:
        try:
            # 1초 타임아웃으로 큐에서 패킷을 가져옴
            # 이를 통해 메인 루프가 block되지 않고 killer.kill_now를 확인할 수 있음
            packet = parser.packet_queue.get(timeout=1)
            if packet is None:
                # 파서 스레드가 종료되었음을 의미
                break

            with buffer_lock:
                packet_buffer.append(packet)

        except queue.Empty:
            # 1초 동안 패킷이 없으면 예외 발생, 정상적인 상황임
            continue

    # 종료 신호 수신 후 정리 작업
    print("Shutting down. Stopping parser...")
    parser.stop()
    print("Parser stopped.")

    # 데이터 전송 스레드가 종료될 때까지 잠시 대기
    sender_thread.join(timeout=2)
    print("Application finished.")


if __name__ == "__main__":
    main()
