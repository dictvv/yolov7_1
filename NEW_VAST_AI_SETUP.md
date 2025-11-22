# 新 Vast.ai 遠端環境設置指南

## 新遠端連線資訊

**SSH 連線指令：**
```bash
ssh -p 40711 root@162.213.119.141 -L 8080:localhost:8080
```

**連線詳情：**
- 主機：162.213.119.141
- 端口：40711
- 用戶：root
- 端口轉發：本地 8080 → 遠程 localhost:8080
- 遠端工作目錄：`/workspace/yolov7_1/`

## 配置時間

配置時間：2025-11-17

## 步驟 1: 測試 SSH 連接

```bash
ssh -p 40711 root@162.213.119.141 "echo 'Connection successful'"
```

## 步驟 2: 在遠端服務器上安裝必要環境

連接到遠端服務器後執行：

```bash
# 更新系統
apt-get update

# 安裝必要套件
apt-get install -y git tmux wget curl

# 安裝 Node.js (用於 tmux MCP server)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 驗證安裝
node --version
npm --version
tmux -V
```

## 步驟 3: 設置 YOLOv7 項目

```bash
# 進入工作目錄
cd /workspace

# 如果已有項目，拉取最新代碼
cd yolov7_1
git pull

# 如果沒有項目，克隆倉庫
# git clone <YOUR_REPO_URL> yolov7_1
# cd yolov7_1

# 運行自動設置腳本
bash setup.sh
```

## 步驟 4: 安裝 tmux MCP Server

```bash
# 全局安裝
npm install -g @modelcontextprotocol/server-remote-tmux

# 或使用 npx（推薦）
npx -y @modelcontextprotocol/server-remote-tmux --version
```

## 步驟 5: 配置本地 Claude Code

### 5.1 配置文件位置

Windows：`C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json`

### 5.2 更新 MCP 配置（推薦方式）

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-p",
        "40711",
        "root@162.213.119.141",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

### 5.3 備用配置（包含端口轉發）

如果需要同時使用端口轉發（例如訪問遠端 Jupyter 或其他 web 服務）：

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-p",
        "40711",
        "root@162.213.119.141",
        "-L",
        "8080:localhost:8080",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

## 步驟 6: 重啟 Claude Code

1. 完全關閉 Claude Code（包括系統托盤）
2. 重新啟動 Claude Code
3. MCP 服務器應該會自動連接

## 步驟 7: 驗證連接

在 Claude Code 中測試以下命令：

1. **列出所有 tmux sessions**
   ```
   請列出遠端服務器上的所有 tmux sessions
   ```

2. **創建測試 session**
   ```
   創建三個 tmux sessions，名稱為 remote、cpu 和 gpu，並在每個中激活 venv 環境
   ```

3. **驗證 GPU**
   ```
   在 gpu tmux session 中執行：nvidia-smi
   ```

## 快速設置自動化腳本

在遠端服務器上執行（一鍵安裝所有依賴）：

```bash
#!/bin/bash
# 保存為 remote-setup.sh

echo "開始設置遠端環境..."

# 更新並安裝套件
apt-get update
apt-get install -y git tmux wget curl

# 安裝 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 設置 YOLOv7
cd /workspace
if [ -d "yolov7_1" ]; then
    echo "項目已存在，拉取最新代碼..."
    cd yolov7_1
    git pull
else
    echo "克隆項目..."
    # git clone <YOUR_REPO_URL> yolov7_1
    cd yolov7_1
fi

# 運行設置腳本
bash setup.sh

# 安裝 tmux MCP server
npm install -g @modelcontextprotocol/server-remote-tmux

echo "遠端設置完成！"
echo "請在本地配置 Claude Code MCP 設置"
```

## 故障排除

### SSH 連接問題

```bash
# 測試基本連接
ssh -p 40711 root@162.213.119.141 "echo test"

# 測試遠端工具
ssh -p 40711 root@162.213.119.141 "node --version && npx --version"
```

### MCP 服務器問題

```bash
# 手動測試 MCP 服務器
ssh -p 40711 root@162.213.119.141 "npx -y tmux-mcp"
```

### 檢查遠端環境

```bash
# 檢查工作目錄
ssh -p 40711 root@162.213.119.141 "ls -la /workspace/yolov7_1"

# 檢查 Python 虛擬環境
ssh -p 40711 root@162.213.119.141 "cd /workspace/yolov7_1 && source venv/bin/activate && python --version"
```

## 常用操作

### 在遠端啟動訓練

```
在 gpu tmux session 中，啟動訓練：
python train.py --workers 8 --device 0 --batch-size 32 --data data/coco.yaml --img 640 640 --cfg cfg/training/yolov7.yaml --weights '' --name yolov7 --hyp data/hyp.scratch.p5.yaml --epochs 100
```

### 監控訓練進度

```
顯示 gpu tmux session 的輸出
```

### 多任務管理

- **remote session**: 文件操作、git 命令、一般任務
- **cpu session**: CPU 密集型預處理、數據增強
- **gpu session**: 模型訓練、推理

## 檢查清單

設置完成後，確認以下項目：

- [ ] vast.ai 實例運行中
- [ ] SSH 連接正常（端口 40711）
- [ ] Node.js/npx 已安裝在遠端
- [ ] tmux MCP server 已安裝
- [ ] YOLOv7 環境已設置（venv、依賴）
- [ ] Claude Code MCP 配置已更新
- [ ] Claude Code 已重啟
- [ ] MCP 連接成功（可列出 tmux sessions）

## 與舊服務器的對比

| 項目 | 舊服務器 | 新服務器 |
|------|---------|---------|
| 主機 | 116.122.206.233 | 162.213.119.141 |
| 端口 | 20430 | 40711 |
| 工作目錄 | /workspace/yolov7_1/ | /workspace/yolov7_1/ |
| 配置文件 | MCP_SETUP_GUIDE.md | NEW_VAST_AI_SETUP.md |

## 注意事項

1. **實例重啟後** - IP 或端口可能改變，需更新配置
2. **保存訓練成果** - 終止實例前下載訓練好的模型
3. **成本監控** - 定期檢查 GPU 使用率和費用
4. **數據持久化** - 考慮使用 vast.ai 的磁盤持久化功能

---

**參考文檔：**
- 舊服務器配置：`MCP_SETUP_GUIDE.md`
- 遠端設置指南：`VAST_AI_REMOTE_SETUP.md`
- YOLOv7 訓練指南：`VAST_AI_SETUP.md`
