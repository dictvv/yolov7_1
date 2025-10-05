#!/bin/bash
# YOLOv7 Auto Setup Script for vast.ai
# Usage: bash setup.sh

set -e  # Exit on error

echo "=========================================="
echo "YOLOv7 Environment Setup Script"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Check CUDA version
echo "Checking CUDA version..."
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    echo "CUDA Version: $CUDA_VERSION"
else
    echo "WARNING: nvidia-smi not found. GPU may not be available."
fi

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA 12.x support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install other requirements
echo "Installing other requirements..."
pip install -r requirements.txt

# Verify installation
echo "Verifying PyTorch installation..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start training, run:"
echo "  python train.py --workers 4 --device 0 --batch-size 32 --data data/coco.yaml --img 320 320 --cfg cfg/training/yolov7-tiny.yaml --weights '' --name yolov7-tiny-320 --hyp data/hyp.scratch.tiny.yaml --epochs 300"
