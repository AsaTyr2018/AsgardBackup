#!/bin/bash

set -e

TARGET_DIR="/opt/asgardbackup"
SERVICE_FILE="/etc/systemd/system/asgardbackup.service"

function install_repo() {
    local repo_url="$1"
    if [ -z "$repo_url" ]; then
        echo "Repo-URL fehlt" >&2
        exit 1
    fi
    if [ -d "$TARGET_DIR/.git" ]; then
        echo "AsgardBackup ist bereits installiert. Führe Update aus." >&2
        update_repo
        return
    fi
    git clone "$repo_url" "$TARGET_DIR"
    python3 -m venv "$TARGET_DIR/venv"
    "$TARGET_DIR/venv/bin/pip" install -r "$TARGET_DIR/requirements.txt"
    create_service
    systemctl daemon-reload
    systemctl enable asgardbackup.service
    systemctl start asgardbackup.service
}

function update_repo() {
    if [ ! -d "$TARGET_DIR/.git" ]; then
        echo "Installation nicht gefunden" >&2
        exit 1
    fi
    cd "$TARGET_DIR"
    git pull
    "$TARGET_DIR/venv/bin/pip" install -r requirements.txt
    systemctl restart asgardbackup.service
}

function create_service() {
    cat <<SERVICE > "$SERVICE_FILE"
[Unit]
Description=AsgardBackup Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$TARGET_DIR
ExecStart=$TARGET_DIR/venv/bin/python server.py serve
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
}

case "$1" in
    install)
        install_repo "$2"
        ;;
    update)
        update_repo
        ;;
    *)
        echo "Verwendung: $0 {install <repo-url>|update}" >&2
        exit 1
        ;;
esac
