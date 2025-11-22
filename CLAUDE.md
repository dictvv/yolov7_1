# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YOLOv7 object detection implementation optimized for training on vast.ai cloud GPU instances. The codebase has been customized for PyTorch 2.6+ compatibility and large batch size training with CUDA 12.x support.

## Key Architecture Components

### Training Pipeline
- **train.py**: Standard YOLOv7 training for P5 models (640x640 input). Supports single/multi-GPU training with DDP.
- **train_aux.py**: Training script for P6 models (1280x1280 input) with auxiliary heads.
- Training uses mixed precision (AMP), gradient accumulation, and exponential moving average (EMA) for model weights.
- Loss computation has two modes: `ComputeLossOTA` (default) and `ComputeLoss`, controlled by `hyp['loss_ota']`.

### Model Architecture
- **models/yolo.py**: Core YOLO model definition using YAML-based architecture configs.
- **models/common.py**: Building blocks (Conv, Bottleneck, SPPCSPC, RepConv, etc.).
- **models/experimental.py**: Model loading utilities including `attempt_load` for ensemble/checkpoint loading.
- Models support implicit learning (im, imc, imb, imo, ia attributes) and attention mechanisms.

### Data Loading
- **utils/datasets.py**: Contains `create_dataloader` for training/validation.
- Supports mosaic augmentation, mixup, copy-paste augmentation, and rectangular training.
- Datasets are cached for faster loading when using `--cache-images`.

### Configuration Files
- **cfg/training/**: Model architecture YAML files (yolov7.yaml, yolov7-tiny.yaml, yolov7-x.yaml, etc.).
- **data/**: Dataset configs (coco.yaml) and hyperparameter configs (hyp.scratch.*.yaml).
- Dataset paths in `coco.yaml` point to `/workspace/yolov7_1/coco/` (vast.ai workspace structure).

## Common Commands

### Environment Setup
```bash
# First-time setup (creates venv, installs PyTorch with CUDA 12.x)
bash setup.sh

# Activate environment
source venv/bin/activate  # Linux/vast.ai
```

### Training
```bash
# Quick start with optimized settings (tiny model, 320x320, batch 256)
bash quick_start.sh

# Single GPU training (P5 models)
python train.py --workers 8 --device 0 --batch-size 32 \
  --data data/coco.yaml --img 640 640 \
  --cfg cfg/training/yolov7.yaml --weights '' \
  --name yolov7 --hyp data/hyp.scratch.p5.yaml --epochs 300

# Single GPU training (P6 models)
python train_aux.py --workers 8 --device 0 --batch-size 16 \
  --data data/coco.yaml --img 1280 1280 \
  --cfg cfg/training/yolov7-w6.yaml --weights '' \
  --name yolov7-w6 --hyp data/hyp.scratch.p6.yaml --epochs 300

# Multi-GPU training (P5)
python -m torch.distributed.launch --nproc_per_node 4 --master_port 9527 \
  train.py --workers 8 --device 0,1,2,3 --sync-bn --batch-size 128 \
  --data data/coco.yaml --img 640 640 \
  --cfg cfg/training/yolov7.yaml --weights '' \
  --name yolov7 --hyp data/hyp.scratch.p5.yaml

# Resume training
python train.py --resume runs/train/yolov7/weights/last.pt

# Fine-tuning with pretrained weights
python train.py --weights yolov7_training.pt \
  --cfg cfg/training/yolov7-custom.yaml \
  --data data/custom.yaml --hyp data/hyp.scratch.custom.yaml
```

### Testing/Validation
```bash
# Standard validation
python test.py --data data/coco.yaml --img 640 --batch 32 \
  --conf 0.001 --iou 0.65 --device 0 \
  --weights yolov7.pt --name yolov7_640_val

# Save predictions as JSON (for COCO eval)
python test.py --data data/coco.yaml --img 640 --batch 32 \
  --weights yolov7.pt --save-json

# YOLOv5 metric compatibility
python test.py --data data/coco.yaml --weights yolov7.pt --v5-metric
```

### Inference
```bash
# Run detection on images
python detect.py --weights yolov7.pt --conf 0.25 --img-size 640 \
  --source inference/images/horses.jpg

# Run detection on video
python detect.py --weights yolov7.pt --conf 0.25 --img-size 640 \
  --source yourvideo.mp4

# Run detection on webcam
python detect.py --weights yolov7.pt --source 0
```

### Export Models
```bash
# Export to ONNX with NMS
python export.py --weights yolov7.pt --grid --end2end --simplify \
  --topk-all 100 --iou-thres 0.65 --conf-thres 0.35 --img-size 640 640
```

## Important Implementation Details

### PyTorch 2.6+ Compatibility
The codebase includes `fix_torch_load.py` which adds `weights_only=False` to all `torch.load()` calls. This was necessary for PyTorch 2.6+ compatibility. All checkpoint loading uses this parameter.

### Training Modifications
- Default epochs reduced from 300 to 100 in `quick_start.sh` for faster iteration.
- Batch size increased to 256 for tiny models to utilize modern GPUs efficiently.
- Workers set to 8 for optimal data loading performance on vast.ai instances.

### Checkpointing Strategy
Training saves checkpoints to `runs/train/<name>/weights/`:
- `last.pt`: Latest checkpoint (saved every epoch)
- `best.pt`: Best checkpoint based on fitness score
- `epoch_000.pt`, `epoch_025.pt`, etc.: Periodic checkpoints every 25 epochs
- Last 5 epochs are always saved individually

### Optimizer Groups
The optimizer divides parameters into 3 groups:
- `pg0`: BatchNorm weights, implicit learning params, attention params (no weight decay)
- `pg1`: Convolutional weights (with weight decay)
- `pg2`: Biases (no weight decay)

### Dataset Structure
Expected COCO dataset layout:
```
coco/
├── images/
│   ├── train2017/
│   └── val2017/
└── labels/
    ├── train2017/
    └── val2017/
```

### Logging
- TensorBoard logs saved to `runs/train/<name>/`
- Supports Weights & Biases (wandb) integration for experiment tracking
- Training results written to `results.txt` in run directory

### Loss Computation
- Uses OTA (Optimal Transport Assignment) loss by default for better anchor assignment
- Falls back to standard loss if `hyp['loss_ota'] != 1`
- Loss scales with batch size, number of detection layers, and image size

### GPU Memory Optimization
- Half precision (FP16) enabled by default on CUDA devices
- Gradient accumulation used when nominal batch size (64) > total batch size
- Images normalized to 0-1 range (uint8 -> float32 / 255.0)

## Project-Specific Conventions

### File Naming
- Training runs auto-increment: `runs/train/exp`, `runs/train/exp2`, etc.
- Use `--name` to specify custom run names
- Use `--exist-ok` to overwrite existing run directories

### Configuration Files
- Hyperparameters in `data/hyp.*.yaml` include augmentation settings, optimizer params, and loss weights
- Model architectures in `cfg/training/*.yaml` define layer structure
- Dataset configs in `data/*.yaml` specify paths and class names

### Git Workflow
The project is configured for vast.ai deployment:
- `setup.sh` and `quick_start.sh` automate environment setup and training
- `VAST_AI_SETUP.md` contains instance setup instructions
- Training state should be committed or downloaded before terminating instances