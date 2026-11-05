#!/usr/bin/env bash
# Bygger film 01 från grunden: bild + ljud -> output/gnistan_tiktok.mp4
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p output
python3 render_audio.py
python3 render_video.py
ffmpeg -y -loglevel error -i output/video_only.mp4 -i output/soundtrack.wav \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart output/gnistan_tiktok.mp4
echo "Klar: output/gnistan_tiktok.mp4"
