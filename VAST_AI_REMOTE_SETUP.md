# Vast.ai Remote Setup Guide for Claude Code

This guide explains how to set up a new vast.ai instance and configure Claude Code to control it remotely via tmux MCP server.

## Prerequisites

- Claude Code installed locally
- Node.js and npm installed (for tmux MCP server)
- SSH client available on your local machine
- A vast.ai account with a new instance created

## Step 1: Configure SSH Connection

### 1.1 Get SSH Connection Info from Vast.ai

From your vast.ai instance page, copy the SSH connection command. It will look like:
```bash
ssh -p <PORT> root@<HOST>.vast.ai -L 8080:localhost:8080
```

### 1.2 Add SSH Config Entry

Edit your SSH config file:
- **Windows**: `C:\Users\<YourUsername>\.ssh\config`
- **Linux/Mac**: `~/.ssh/config`

Add the following entry (replace with your actual connection details):

```ssh-config
Host vastai-yolo
    HostName <HOST>.vast.ai
    Port <PORT>
    User root
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LocalForward 8080 localhost:8080
```

**Note**: If you don't have an SSH key, vast.ai typically uses password authentication by default.

### 1.3 Test SSH Connection

```bash
ssh vastai-yolo
```

You should be able to connect to your vast.ai instance.

## Step 2: Setup Remote Environment

### 2.1 Initial System Setup

Connect to your vast.ai instance and run:

```bash
# Update system
apt-get update

# Install required packages
apt-get install -y git tmux wget curl

# Install Node.js (required for tmux MCP server)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Verify installations
node --version
npm --version
tmux -V
```

### 2.2 Clone and Setup YOLOv7 Project

```bash
# Navigate to workspace
cd /workspace

# Clone your YOLOv7 repository
git clone <YOUR_REPO_URL> yolov7_1
cd yolov7_1

# Run automated setup script
bash setup.sh
```

This will:
- Create Python virtual environment
- Install PyTorch with CUDA support
- Install all required dependencies

### 2.3 Install tmux MCP Server

```bash
# Install globally
npm install -g @modelcontextprotocol/server-remote-tmux

# Or install locally
npm install @modelcontextprotocol/server-remote-tmux
```

### 2.4 Configure tmux MCP Server

Create a startup script for the tmux MCP server:

```bash
# Create script directory
mkdir -p ~/.mcp

# Create startup script
cat > ~/.mcp/start-tmux-server.sh << 'EOF'
#!/bin/bash
npx -y @modelcontextprotocol/server-remote-tmux
EOF

# Make executable
chmod +x ~/.mcp/start-tmux-server.sh
```

## Step 3: Configure Local Claude Code

### 3.1 Edit Claude Code MCP Settings

On your local machine, open Claude Code settings:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 3.2 Add Remote tmux MCP Server Configuration

Add or update the MCP servers section:

```json
{
  "mcpServers": {
    "remote-tmux": {
      "command": "ssh",
      "args": [
        "vastai-yolo",
        "~/.mcp/start-tmux-server.sh"
      ],
      "env": {}
    }
  }
}
```

**Alternative Configuration (using npx directly):**

```json
{
  "mcpServers": {
    "remote-tmux": {
      "command": "ssh",
      "args": [
        "vastai-yolo",
        "npx",
        "-y",
        "@modelcontextprotocol/server-remote-tmux"
      ],
      "env": {}
    }
  }
}
```

### 3.3 Restart Claude Code

Close and restart Claude Code completely for the changes to take effect.

## Step 4: Verify Setup

### 4.1 Check MCP Connection

In Claude Code, you should now be able to use tmux commands. Test with:

```
Please list all tmux sessions on the remote server.
```

### 4.2 Create Test Sessions

Ask Claude Code to:
```
Create three tmux sessions named remote, cpu, and gpu, and activate the venv environment in each.
```

### 4.3 Verify Remote Environment

```
In the gpu tmux session, run: nvidia-smi
```

This should display GPU information from your vast.ai instance.

## Step 5: Common Operations

### Start Training in tmux

Ask Claude Code to execute in a specific tmux session:
```
In the gpu tmux session, start training with:
python train.py --workers 8 --device 0 --batch-size 32 --data data/coco.yaml --img 640 640 --cfg cfg/training/yolov7.yaml --weights '' --name yolov7 --hyp data/hyp.scratch.p5.yaml --epochs 100
```

### Monitor Training Progress

```
Show me the output from the gpu tmux session
```

### Run Multiple Tasks

- **remote session**: File operations, git commands, general tasks
- **cpu session**: CPU-intensive preprocessing, data augmentation
- **gpu session**: Model training, inference

## Troubleshooting

### Connection Issues

**Problem**: SSH connection fails
```bash
# Test SSH manually
ssh vastai-yolo

# Check SSH config syntax
ssh -G vastai-yolo
```

**Problem**: MCP server not responding
```bash
# Test MCP server manually on remote
ssh vastai-yolo "npx -y @modelcontextprotocol/server-remote-tmux"
```

### tmux Issues

**Problem**: "no server running" error
```bash
# tmux server needs to be started first
# Claude Code will start it automatically when creating first session
```

**Problem**: Virtual environment not activating
```bash
# Verify venv exists
ssh vastai-yolo "ls -la /workspace/yolov7_1/venv"

# Manually test activation
ssh vastai-yolo "cd /workspace/yolov7_1 && source venv/bin/activate && python --version"
```

### Node.js Issues

**Problem**: npx command not found
```bash
# Reinstall Node.js on remote
ssh vastai-yolo "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs"
```

## Quick Start Checklist

- [ ] vast.ai instance created and running
- [ ] SSH config added to local `~/.ssh/config`
- [ ] SSH connection tested successfully
- [ ] Remote system packages installed (git, tmux, node, npm)
- [ ] YOLOv7 repository cloned and setup script run
- [ ] tmux MCP server installed on remote
- [ ] Claude Code MCP config updated locally
- [ ] Claude Code restarted
- [ ] MCP connection verified by listing tmux sessions
- [ ] Test tmux session created successfully

## Automation Script (Optional)

For even faster setup, you can create a single automation script:

```bash
#!/bin/bash
# save as: remote-setup.sh

echo "Setting up vast.ai remote environment..."

# Update and install packages
apt-get update
apt-get install -y git tmux wget curl

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Setup YOLOv7
cd /workspace
git clone <YOUR_REPO_URL> yolov7_1
cd yolov7_1
bash setup.sh

# Install tmux MCP server
npm install -g @modelcontextprotocol/server-remote-tmux

# Create MCP startup script
mkdir -p ~/.mcp
cat > ~/.mcp/start-tmux-server.sh << 'EOF'
#!/bin/bash
npx -y @modelcontextprotocol/server-remote-tmux
EOF
chmod +x ~/.mcp/start-tmux-server.sh

echo "Remote setup complete!"
echo "Now configure Claude Code locally with the MCP server settings."
```

Run on new vast.ai instance:
```bash
wget https://your-server.com/remote-setup.sh
bash remote-setup.sh
```

## Additional Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [MCP Remote tmux Server](https://github.com/modelcontextprotocol/servers/tree/main/src/remote-tmux)
- [Vast.ai Documentation](https://vast.ai/docs/)
- [YOLOv7 Training Guide](VAST_AI_SETUP.md)

## Notes

- Keep your SSH session alive with `ServerAliveInterval` settings
- Use tmux to prevent training interruption if SSH disconnects
- Download trained models before terminating vast.ai instance
- Consider using vast.ai's disk persistence features for longer projects
- Monitor GPU usage and costs regularly
