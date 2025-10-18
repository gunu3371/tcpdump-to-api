# Tcpdump to API

이 프로젝트는 `tcpdump`를 사용하여 네트워크 트래픽을 캡처하고, 그 결과를 파싱하여 지정된 API 엔드포인트로 주기적으로 POST 요청을 보내는 파이썬 스크립트입니다. `systemd` 서비스로 등록하여 백그라운드에서 안정적으로 실행되도록 설계되었습니다.

**주의: 이 프로젝트의 코드는 전부 AI에 의해 작성되었습니다.**

## 주요 기능

- **실시간 패킷 캡처**: `tcpdump`를 백그라운드 프로세스로 실행하여 네트워크 패킷을 실시간으로 캡처합니다.
- **데이터 파싱**: 캡처된 `tcpdump` 출력에서 프로토콜, IP 주소, 포트, 데이터 길이 등 핵심 정보를 추출합니다.
- **주기적 데이터 전송**: 파싱된 데이터를 메모리 버퍼에 임시 저장 후, 설정된 주기마다 지정된 API로 전송합니다.
- **안전한 종료**: `SIGTERM`, `SIGINT` 신호를 감지하여 실행 중인 작업을 안전하게 마무리하고 종료합니다.
- **Systemd 서비스**: `systemd` 서비스로 등록하여 부팅 시 자동으로 실행되고, 안정적으로 관리됩니다.
- **간편한 설치/제거**: `install.sh`, `uninstall.sh` 스크립트를 통해 손쉽게 서비스를 설치하고 제거할 수 있습니다.

## 시스템 요구 사항

- `systemd`를 사용하는 Linux 배포판
- Python 3
- `tcpdump`

## 설치 방법

프로젝트를 `systemd` 서비스로 설치하려면 아래 명령어를 실행하세요.

```bash
# 1. 설치 스크립트에 실행 권한을 부여합니다.
chmod +x install.sh

# 2. 스크립트를 루트 권한으로 실행합니다.
sudo ./install.sh
```

설치 스크립트는 다음 작업을 자동으로 수행합니다:
- 애플리케이션 파일을 `/etc/tcpdump-to-api` 디렉토리에 복사합니다.
- 서비스 실행을 위한 독립된 Python 가상 환경을 생성하고 라이브러리를 설치합니다.
- `tcpdump-api.service` 파일을 생성하고 `systemd`에 등록합니다.

## 설정

설치가 완료된 후, 서비스의 설정은 `/etc/tcpdump-to-api/.env` 파일에서 변경할 수 있습니다.

```
# 데이터를 전송할 API 엔드포인트 URL
POST_URL=http://localhost:8000/packets

# 데이터 전송 주기 (초)
SEND_INTERVAL=10
```

설정 파일을 수정한 후에는 반드시 서비스를 재시작하여 변경사항을 적용해야 합니다.

```bash
sudo systemctl restart tcpdump-api
```

## 사용법 (서비스 관리)

서비스는 `systemctl` 명령어를 통해 관리할 수 있습니다.

- **서비스 시작**
  ```bash
  sudo systemctl start tcpdump-api
  ```

- **서비스 상태 확인**
  ```bash
  sudo systemctl status tcpdump-api
  ```

- **서비스 중지**
  ```bash
  sudo systemctl stop tcpdump-api
  ```

- **실시간 로그 확인**
  ```bash
  sudo journalctl -u tcpdump-api -f
  ```

## 제거 방법

서비스와 관련된 모든 파일을 시스템에서 제거하려면 `uninstall.sh` 스크립트를 사용하세요.

```bash
# 1. 제거 스크립트에 실행 권한을 부여합니다.
chmod +x uninstall.sh

# 2. 스크립트를 루트 권한으로 실행합니다.
sudo ./uninstall.sh
```

## 개발 환경에서 직접 실행

서비스로 설치하지 않고 소스 코드 디렉토리에서 직접 스크립트를 실행하려면 다음 단계를 따르세요.

1.  **라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

2.  **스크립트 실행**
    네트워크 인터페이스 접근을 위해 `sudo` 권한이 필요할 수 있습니다.
    ```bash
    sudo python3 main.py
    ```