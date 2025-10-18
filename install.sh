#!/bin/bash

# ==============================================================================
# Tcpdump to API 설치 스크립트
# ==============================================================================
# 이 스크립트는 다음 작업을 수행합니다:
# 1. 애플리케이션 파일을 /etc/tcpdump-to-api 디렉토리로 복사합니다.
# 2. 해당 디렉토리 내에 Python 가상 환경을 생성합니다.
# 3. 필요한 라이브러리를 가상 환경에 설치합니다.
# 4. 애플리케이션을 실행하는 systemd 서비스 파일을 생성하고 등록합니다.
# ==============================================================================

# --- 변수 정의 ---
# 소스 파일이 있는 현재 디렉토리
SOURCE_DIR="$( cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 ; pwd -P )"
# 애플리케이션을 설치할 디렉토리
INSTALL_DIR="/etc/tcpdump-to-api"
# Python 가상 환경 디렉토리
VENV_DIR="$INSTALL_DIR/.venv"
# 서비스 이름
SERVICE_NAME="tcpdump-api"
# systemd 서비스 파일 경로
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
# 서비스를 실행할 사용자 (sudo를 실행한 사용자)
RUN_USER=${SUDO_USER:-$(whoami)}


# --- 스크립트 시작 ---

# 1. 루트 권한 확인
if [[ $EUID -ne 0 ]]; then
   echo "오류: 이 스크립트는 반드시 sudo 또는 루트 권한으로 실행해야 합니다."
   exit 1
fi

echo "Tcpdump to API 서비스 설치를 시작합니다..."

# 2. 이전 설치 제거 (선택적)
if [ -d "$INSTALL_DIR" ]; then
    echo "기존 설치 디렉토리를 삭제합니다: $INSTALL_DIR"
    # 만약 서비스가 실행 중이면 중지
    systemctl stop "$SERVICE_NAME.service" >/dev/null 2>&1
    rm -rf "$INSTALL_DIR"
fi
if [ -f "$SERVICE_FILE" ]; then
    echo "기존 서비스 파일을 삭제합니다: $SERVICE_FILE"
    systemctl disable "$SERVICE_NAME.service" >/dev/null 2>&1
    rm "$SERVICE_FILE"
fi


# 3. 설치 디렉토리 생성 및 파일 복사
echo "설치 디렉토리를 생성하고 파일을 복사합니다..."
mkdir -p "$INSTALL_DIR"
cp "$SOURCE_DIR/main.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/parser.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/"

# .env 파일이 존재하면 복사
if [ -f "$SOURCE_DIR/.env" ]; then
    cp "$SOURCE_DIR/.env" "$INSTALL_DIR/"
    echo ".env 파일이 '$INSTALL_DIR'에 복사되었습니다."
else
    echo "경고: .env 파일이 없습니다. '$INSTALL_DIR/.env' 위치에 직접 생성해야 할 수 있습니다."
fi

# 4. Python 가상 환경 생성 및 라이브러리 설치
echo "Python 가상 환경을 생성하고 의존성을 설치합니다..."
python3 -m venv "$VENV_DIR"
# 생성된 가상 환경의 pip를 사용하여 라이브러리 설치
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"


# 5. systemd 서비스 파일 생성
echo "systemd 서비스 파일을 생성합니다..."

cat > "$SERVICE_FILE" <<-EOF
[Unit]
Description=Tcpdump to API Service
Wants=network-online.target
After=network-online.target

[Service]
# 서비스를 실행할 사용자 및 그룹
User=$RUN_USER
Group=$(id -gn "$RUN_USER")

# 작업 디렉토리
WorkingDirectory=$INSTALL_DIR

# 실행 명령어 (가상 환경의 Python 사용)
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main.py

# 일반 사용자로 tcpdump를 실행하기 위한 권한 부여
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN

# 서비스가 실패하면 5초 후 다시 시작
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF


# 6. 서비스 등록 및 활성화
echo "systemd 데몬을 리로드하고 서비스를 활성화합니다..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME.service"

# 7. 완료 메시지
echo ""
echo "✅ 설치가 성공적으로 완료되었습니다!"
echo "--------------------------------------------------"
echo "애플리케이션은 '$INSTALL_DIR'에 설치되었습니다."
echo ""
echo "다음을 사용하여 서비스를 제어할 수 있습니다:"
echo "  - 서비스 시작: sudo systemctl start $SERVICE_NAME"
echo "  - 서비스 상태 확인: sudo systemctl status $SERVICE_NAME"
echo "  - 서비스 중지: sudo systemctl stop $SERVICE_NAME"
echo "  - 실시간 로그 확인: sudo journalctl -u $SERVICE_NAME -f"
echo "--------------------------------------------------"
