#!/bin/bash
set -e

export DISPLAY=:${DISPLAY_NUM}

# Start Xvfb (virtual display)
echo "Starting Xvfb..."
Xvfb ${DISPLAY} -screen 0 ${WIDTH}x${HEIGHT}x24 -ac -nolisten tcp -dpi 96 +extension RANDR > /tmp/xvfb.log 2>&1 &
XVFB_PID=$!

# Wait for X server to be ready
sleep 2

# Start window manager
echo "Starting window manager..."
mutter --replace --sm-disable --display=${DISPLAY} > /tmp/mutter.log 2>&1 &

# Start tint2 (taskbar)
echo "Starting tint2..."
tint2 > /tmp/tint2.log 2>&1 &

# Start VNC server
echo "Starting VNC server..."
x11vnc -display ${DISPLAY} -forever -shared -rfbport 5900 > /tmp/x11vnc.log 2>&1 &

# Start noVNC
echo "Starting noVNC..."
/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080 > /tmp/novnc.log 2>&1 &

echo "✨ Desktop environment is ready!"
echo "➡️  VNC: vnc://localhost:5900"
echo "➡️  noVNC: http://localhost:6080"

# Start FastAPI backend
echo "Starting FastAPI backend..."
cd /home/computeruse/app
uv run python main.py
