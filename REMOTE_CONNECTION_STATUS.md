# 遠端連線設定狀態

## 當前狀態：✅ 已完成設定，等待 Claude Code 重啟以啟用

**最後更新時間**: 2025-11-22 11:01 UTC

---

## 快速開始（給下一個 Claude Code 會話）

如果您是新的 Claude Code 會話，請執行以下驗證步驟：

```bash
# 1. 測試 SSH 連線
ssh -p 42229 root@83.27.164.65 "echo 'Connection OK'"

# 2. 檢查遠端 tmux MCP 伺服器狀態
ssh -p 42229 root@83.27.164.65 "tmux list-sessions"

# 3. 檢查本地配置檔案
cat "C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json"
```

---

## 已完成的設定步驟

### ✅ Step 1: GitHub 儲存庫上傳
- **儲存庫 URL**: https://github.com/dictvv/yolov7_1.git
- **最後提交**: 582daa5 - "Add 4-head multi-task YOLOv7 implementation"
- **狀態**: 已推送，包含所有程式碼和配置檔案

### ✅ Step 2: SSH 連線到 vast.ai
- **主機**: 83.27.164.65
- **端口**: 42229
- **用戶**: root
- **SSH 金鑰**: 已配置（使用 StrictHostKeyChecking=no）
- **端口轉發**: 8080:localhost:8080
- **測試命令**:
  ```bash
  ssh -p 42229 root@83.27.164.65 "echo 'Connection OK'"
  ```
- **狀態**: ✅ 連線正常

### ✅ Step 3: 遠端環境設定
- **工作目錄**: /workspace/yolov7_1
- **Git 儲存庫**: 已從 GitHub 複製
- **Node.js**: v20.19.5 已安裝
- **npx**: 已安裝（位於 /usr/bin/npx）
- **tmux**: v3.4 已安裝
- **狀態**: ✅ 環境準備完成

### ✅ Step 4: tmux MCP 伺服器設定
- **MCP 套件**: tmux-mcp（透過 npx 安裝）
- **啟動腳本**: ~/.mcp/start-tmux-server.sh
- **腳本內容**:
  ```bash
  #!/bin/bash
  npx -y tmux-mcp
  ```
- **tmux 會話**: mcp_server（已創建並運行）
- **檢查命令**:
  ```bash
  ssh -p 42229 root@83.27.164.65 "tmux list-sessions"
  ```
- **狀態**: ✅ MCP 伺服器運行中

### ✅ Step 5: 本地 Claude Code 配置
- **配置檔案**: `C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json`
- **配置內容**:
  ```json
  {
    "mcpServers": {
      "remote-tmux": {
        "type": "stdio",
        "command": "ssh",
        "args": [
          "-o",
          "StrictHostKeyChecking=no",
          "-p",
          "42229",
          "root@83.27.164.65",
          "/usr/bin/npx",
          "-y",
          "tmux-mcp"
        ],
        "env": {}
      }
    }
  }
  ```
- **狀態**: ✅ 配置已更新

---

## 🔲 待完成步驟

### Step 6: 重啟 Claude Code
**用戶需要手動執行**：
1. 完全關閉 Claude Code（包括系統托盤）
2. 重新啟動 Claude Code
3. 驗證 remote-tmux MCP 伺服器已連接

---

## 驗證清單

重啟 Claude Code 後，請驗證以下項目：

### 本地端驗證
- [ ] Claude Code 已重新啟動
- [ ] MCP 伺服器列表中顯示 "remote-tmux"
- [ ] remote-tmux 狀態顯示為 "已連接" 或 "Connected"

### 遠端功能驗證
透過 Claude Code 的 MCP 功能測試：
- [ ] 列出遠端 tmux 會話
- [ ] 創建新的 tmux 會話
- [ ] 在遠端執行命令
- [ ] 讀取命令輸出

### 測試命令示例
```bash
# 在 Claude Code 中請求執行以下操作：
# 1. 列出所有 tmux 會話
# 2. 創建新會話 "test_session"
# 3. 在會話中執行 "echo 'Hello from remote'"
# 4. 讀取輸出
```

---

## 重要資訊

### vast.ai 實例資訊
- **實例 ID**: （請向用戶確認）
- **SSH 主機**: 83.27.164.65
- **SSH 端口**: 42229
- **工作目錄**: /workspace/yolov7_1
- **GPU**: （請向用戶確認型號）

### ⚠️ 重要提醒
1. **實例重啟後 IP/端口可能改變**
   - 需要更新 `claude_desktop_config.json` 中的連線資訊
   - 需要重新建立 SSH 信任關係

2. **tmux MCP 伺服器需要運行**
   - 如果遠端伺服器重啟，需要重新啟動 MCP 伺服器
   - 重啟命令：
     ```bash
     ssh -p 42229 root@83.27.164.65 "tmux new-session -d -s mcp_server 'bash ~/.mcp/start-tmux-server.sh'"
     ```

3. **本地配置變更需要重啟**
   - 任何對 `claude_desktop_config.json` 的修改都需要重啟 Claude Code

---

## 故障排除

### 問題 1: remote-tmux 未顯示在 MCP 列表中
**解決方案**:
1. 檢查配置檔案路徑和格式是否正確
2. 確認 Claude Code 已完全重啟
3. 查看 Claude Code 日誌檔案

### 問題 2: 連線失敗 "Connection refused"
**解決方案**:
1. 測試 SSH 連線：
   ```bash
   ssh -p 42229 root@83.27.164.65 "echo test"
   ```
2. 檢查 vast.ai 實例是否運行中
3. 確認端口和 IP 正確

### 問題 3: tmux-mcp 啟動失敗
**解決方案**:
1. 檢查遠端 Node.js 是否正常：
   ```bash
   ssh -p 42229 root@83.27.164.65 "node --version"
   ```
2. 手動測試 tmux-mcp：
   ```bash
   ssh -p 42229 root@83.27.164.65 "/usr/bin/npx -y tmux-mcp"
   ```
3. 檢查 tmux 會話狀態：
   ```bash
   ssh -p 42229 root@83.27.164.65 "tmux list-sessions"
   ```

### 問題 4: 權限問題
**解決方案**:
1. 確保 SSH 金鑰配置正確
2. 檢查遠端檔案權限：
   ```bash
   ssh -p 42229 root@83.27.164.65 "ls -la ~/.mcp/"
   ```

---

## 下一步操作（訓練相關）

連線設定完成後，可以進行以下操作：

### 1. 設定遠端 Python 環境
```bash
cd /workspace/yolov7_1
bash setup.sh
source venv/bin/activate
```

### 2. 下載 COCO 資料集
參考 `VAST_AI_REMOTE_SETUP.md` 中的指示

### 3. 開始訓練
參考 `4HEAD_TRAINING_PLAN.md` 中的訓練命令

### 4. 使用 tmux 監控訓練
```bash
# 創建訓練會話
tmux new -s train_head1

# 執行訓練
python train.py --workers 8 --device 0 --batch-size 32 \
  --data data/coco_head1.yaml --img 640 640 \
  --cfg cfg/training/yolov7.yaml --weights '' \
  --name yolov7_head1 --hyp data/hyp.scratch.p5.yaml --epochs 100

# 分離會話（Ctrl+B, D）
```

---

## 相關文檔

- **訓練計劃**: `4HEAD_TRAINING_PLAN.md`
- **MCP 設定指南**: `MCP_SETUP_GUIDE.md`
- **vast.ai 遠端設定**: `VAST_AI_REMOTE_SETUP.md`
- **專案說明**: `CLAUDE.md`

---

## 如何告訴下一個 Claude Code 會話

當您開始新的 Claude Code 會話時，只需說：

> "請讀取 REMOTE_CONNECTION_STATUS.md 和 4HEAD_TRAINING_PLAN.md，了解目前的專案狀態和已完成的設定。"

或者更簡潔：

> "讀取 REMOTE_CONNECTION_STATUS.md，繼續遠端訓練設定。"

---

## 配置檔案備份

### 本地配置檔案
**位置**: `C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json`

如果需要恢復配置，使用以下內容：
```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        "42229",
        "root@83.27.164.65",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

### 遠端啟動腳本
**位置**: `/root/.mcp/start-tmux-server.sh`（在 vast.ai 伺服器上）

如果需要重建，使用以下內容：
```bash
#!/bin/bash
npx -y tmux-mcp
```

別忘記設定執行權限：
```bash
chmod +x ~/.mcp/start-tmux-server.sh
```

---

**文檔建立**: 2025-11-22
**維護者**: Claude Code
**版本**: 1.0
