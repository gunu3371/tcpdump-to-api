import time
import sys
from parser import TcpdumpParser


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
        if parser.process:  # start()가 성공적으로 실행된 경우에만 stop() 호출
            parser.stop()
