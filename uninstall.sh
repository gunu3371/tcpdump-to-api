#!/bin/bash

# 스크립트 실행 중 오류 발생 시 즉시 중단합니다.
set -e
set -o pipefail

# ==============================================================================
# Tcpdump to API 제거 스크립트
# ==============================================================================
# 이 스크립트는 다음 작업을 수행합니다:
# 1. systemd 서비스를 중지하고 비활성화합니다.
# 2. systemd 서비스 파일을 삭제합니다.
# 3. /etc/tcpdump-to-api 설치 디렉토리를 삭제합니다.
# ==============================================================================

# --- 변수 정의 ---
INSTALL_DIR="/etc/tcpdump-to-api"
SERVICE_NAME="tcpdump-to-api"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# --- 스크립트 시작 ---

# 1. 루트 권한 확인
if [[ $EUID -ne 0 ]]; then
   echo "오류: 이 스크립트는 반드시 sudo 또는 루트 권한으로 실행해야 합니다."
   exit 1
fi

echo "Tcpdump to API 서비스 제거를 시작합니다..."

# 2. 서비스 중지 및 비활성화
echo "서비스를 중지하고 비활성화합니다..."
# 서비스가 존재하지 않더라도 오류를 출력하지 않음
systemctl stop "$SERVICE_NAME.service" >/dev/null 2>&1
systemctl disable "$SERVICE_NAME.service" >/dev/null 2>&1

# 3. systemd 서비스 파일 삭제
if [ -f "$SERVICE_FILE" ]; then
    echo "서비스 파일을 삭제합니다: $SERVICE_FILE"
    rm "$SERVICE_FILE"
else
    echo "서비스 파일이 이미 존재하지 않습니다."
fi

# 4. systemd 데몬 리로드
echo "systemd 데몬을 리로드합니다..."
systemctl daemon-reload

# 5. 설치 디렉토리 삭제
if [ -d "$INSTALL_DIR" ]; then
    echo "설치 디렉토리를 삭제합니다: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
else
    echo "설치 디렉토리가 이미 존재하지 않습니다."
fi

echo ""
echo "✅ 제거가 성공적으로 완료되었습니다!"
