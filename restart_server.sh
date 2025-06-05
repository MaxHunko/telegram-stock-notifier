#!/bin/bash

cd /root/preorderBot/ || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to navigate to directory /root/preorderBot/" >> logs/server_restart.log; exit 1; }

PID_FILE="pid/server.pid"
LOG_FILE="logs/server_restart.log"

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")

        if ps -p $PID > /dev/null 2>&1; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Completing server.py with PID $PID" >> "$LOG_FILE"
            kill $PID
            sleep 5

            if ps -p $PID > /dev/null 2>&1; then
                echo "$(date '+%Y-%m-%d %H:%M:%S') - Forced termination..." >> "$LOG_FILE"
                kill -9 $PID
            fi
        fi

        rm -f "$PID_FILE"
    fi
}

start_server() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running server.py with nohup..." >> "$LOG_FILE"
    nohup python3 server.py >> logs/server_output.log 2>&1 &
    echo $! > "$PID_FILE"
}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Forced server restart..." >> "$LOG_FILE"

stop_server
start_server
