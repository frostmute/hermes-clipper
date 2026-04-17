#!/bin/bash

# --- CONFIG ---
OUTPUT="hermes_clipper_demo.mp4"
FPS=30

# Auto-detect resolution
DISPLAY_SIZE=$(xrandr | grep '*' | awk '{print $1}' | head -n1)
echo "Detected Resolution: $DISPLAY_SIZE"

# --- PREP ---
echo "⚡ PREPARING DEMO ORCHESTRATION..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Start the Bridge in the background
pkill -f "hermes_clipper.main serve" || true
/usr/bin/python3 -m hermes_clipper.main serve > demo_server.log 2>&1 &
BRIDGE_PID=$!
sleep 3

# --- RECORDING START ---
echo "🎥 RECORDING STARTING IN 3 SECONDS..."
sleep 3

ffmpeg -y -f x11grab -video_size $DISPLAY_SIZE -i :0.0 -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p $OUTPUT > ffmpeg.log 2>&1 &
FFMPEG_PID=$!

# --- ACTIONS ---

# 1. Open Terminal and Show Help
# We use xdg-open for generic app opening if possible, or assume a terminal
xterm -geometry 100x30+100+100 -e "bash -c 'echo \"$HERMES_LOGO\"; hermes-clip --help; sleep 5'" &
sleep 5

# 2. Show the Command Center
xdg-open "https://frostmute.github.io/hermes-clipper/"
sleep 7

# 3. Simulate CLI Clip
xterm -geometry 100x20+200+200 -e "bash -c 'echo \">>> CLIPPING EXAMPLE.COM...\"; hermes-clip clip --url https://example.com --direct --caveman; sleep 5'" &
sleep 8

# 4. Open Obsidian
xdg-open "obsidian://open?vault=Endeavor&file=Clippings/Example Domain"
sleep 10

# --- CLEANUP ---
echo "🛑 STOPPING RECORDING..."
kill $FFMPEG_PID
kill $BRIDGE_PID
pkill xterm
wait $FFMPEG_PID 2>/dev/null

echo "🎬 DEMO READY: $OUTPUT"
