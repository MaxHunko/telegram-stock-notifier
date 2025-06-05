#!/bin/bash

cd /root/preorderBot/ || { echo "Failed to navigate to directory /root/preorderBot/"; exit 1; }

PID_FILE="check.pid"

LOG_FILE="/logs/restart.log"

stop_script() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Terminating check.py process with PID $PID" >> "$LOG_FILE"
            kill $PID
            sleep 5
            if ps -p $PID > /dev/null 2>&1; then
                echo "$(date '+%Y-%m-%d %H:%M:%S') -The process did not complete. Forced termination..." >> "$LOG_FILE"
                kill -9 $PID
            fi
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') - The PID file exists, but the process was not found." >> "$LOG_FILE"
        fi
        rm -f "$PID_FILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - PID file not found. It is assumed that the script is not running." >> "$LOG_FILE"
    fi
}

start_script() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running the script check.py..." >> "$LOG_FILE"
    nohup python3 check.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - The script is running with PID $(cat "$PID_FILE")." >> "$LOG_FILE"
}

stop_script
start_script

