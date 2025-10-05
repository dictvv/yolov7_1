# YOLOv7 on vast.ai Quick Setup Guide

## 🚀 First Time Setup (New Instance)

When you start a new vast.ai instance, run:

```bash
# 1. Clone the repository
git clone https://github.com/dictvv/yolov7_1.git
cd yolov7_1

# 2. Run the setup script (one-time setup)
chmod +x setup.sh
bash setup.sh
```

This will:
- Create a Python virtual environment
- Install PyTorch with CUDA 12.x support
- Install all required dependencies
- Verify GPU availability

## 📊 Start Training

After setup, you can start training with:

```bash
# Option 1: Use the quick start script
chmod +x quick_start.sh
bash quick_start.sh

# Option 2: Manual command
source venv/bin/activate
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
```

## 🔄 Resume on Existing Instance

If you already set up the environment:

```bash
cd yolov7_1
source venv/bin/activate
python train.py [your arguments]
```

## 📋 Dataset Setup

Make sure your COCO dataset is organized as:

```
/workspace/yolov7_1/coco/
├── images/
│   ├── train2017/
│   └── val2017/
└── labels/
    ├── train2017/
    └── val2017/
```

## 🛠️ Troubleshooting

### Missing packages
If you encounter missing package errors:
```bash
source venv/bin/activate
pip install <package-name>
```

### CUDA not available
Check GPU status:
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### Training interrupted
Resume training:
```bash
python train.py --resume runs/train/yolov7-tiny-320/weights/last.pt
```

## 📦 Files Overview

- `setup.sh` - Initial environment setup
- `quick_start.sh` - Quick training launcher
- `requirements.txt` - Python dependencies
- `data/coco.yaml` - Dataset configuration
- `cfg/training/yolov7-tiny.yaml` - Model architecture
- `data/hyp.scratch.tiny.yaml` - Hyperparameters

## 💾 Save Your Work

Before terminating the instance:
```bash
git add .
git commit -m "Update training progress"
git push
```

Or download important files:
```bash
# Download trained weights
# runs/train/yolov7-tiny-320/weights/best.pt
```
