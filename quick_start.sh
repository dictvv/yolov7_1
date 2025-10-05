#!/bin/bash
# Quick Start Training Script
# Usage: bash quick_start.sh

set -e

echo "Starting YOLOv7-tiny 320x320 training..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Start training with recommended parameters
python train.py \
  --workers 4 \
  --device 0 \
  --batch-size 32 \
  --data data/coco.yaml \
  --img 320 320 \
  --cfg cfg/training/yolov7-tiny.yaml \
  --weights '' \
  --name yolov7-tiny-320 \
  --hyp data/hyp.scratch.tiny.yaml \
  --epochs 300

echo "Training completed!"
