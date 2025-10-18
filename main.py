import time
import requests
import threading
from parser import TcpdumpParser

# 파싱된 데이터를 임시 저장할 리스트
packet_buffer = []
# 버퍼 접근을 동기화하기 위한 Lock
buffer_lock = threading.Lock()

# 주기적으로 데이터를 POST로 전송하는 함수
def send_data_periodically(url, interval):
    """
    지정된 간격(interval)마다 버퍼의 데이터를 POST로 전송합니다.
    """
    while True:
        time.sleep(interval)

        # 버퍼에 데이터가 있는지 확인
        if not packet_buffer:
            continue

        # Lock을 사용하여 버퍼의 데이터를 안전하게 복사하고 비움
        with buffer_lock:
            data_to_send = list(packet_buffer)
            packet_buffer.clear()

        try:
            # POST 요청 전송 (json 형식)
            response = requests.post(url, json=data_to_send)
            response.raise_for_status()  # 2xx 상태 코드가 아닐 경우 예외 발생
            print(f"Successfully sent {len(data_to_send)} packets.")

        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")
            # 전송 실패 시, 데이터를 다시 버퍼에 추가 (필요에 따라 로직 변경 가능)
            with buffer_lock:
                packet_buffer.extend(data_to_send)


import os
from dotenv import load_dotenv

def main():
    """
    메인 함수: TcpdumpParser를 실행하고,
    파싱된 데이터를 버퍼에 추가합니다.
    """
    load_dotenv()  # .env 파일에서 환경 변수 로드

    parser = TcpdumpParser()
    post_url = os.getenv("POST_URL")  # 데이터를 전송할 URL
    send_interval = int(os.getenv("SEND_INTERVAL", 10))  # 전송 주기 (초)

    # 데이터 전송 스레드 시작
    sender_thread = threading.Thread(
        target=send_data_periodically, args=(post_url, send_interval), daemon=True
    )
    sender_thread.start()

    try:
        print("Starting tcpdump parser...")
        parser.start()

        # 파서로부터 패킷을 지속적으로 읽어와 버퍼에 추가
        for packet in parser.packets():
            with buffer_lock:
                packet_buffer.append(packet)
            # (디버깅용) 수신된 패킷 정보 출력
            # print(f"Packet captured: {packet}")

    except KeyboardInterrupt:
        print("
Stopping parser...")
    finally:
        parser.stop()
        print("Parser stopped.")


if __name__ == "__main__":
    main()
